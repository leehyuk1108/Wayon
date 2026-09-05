import numpy as np
from opendbc.can import CANPacker
from opendbc.car import Bus, DT_CTRL, structs
from opendbc.car.lateral import apply_driver_steer_torque_limits
from opendbc.car.gm import gmcan
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.gm.cluster_speed import gm_raw_display_kph_from_cluster_display_kph
from opendbc.car.gm.values import CAR, DBC, CanBus, CarControllerParams, CruiseButtons, SDGM_CAR
from opendbc.car.interfaces import CarControllerBase
from opendbc.sunnypilot.car.gm.icbm import IntelligentCruiseButtonManagementInterface

VisualAlert = structs.CarControl.HUDControl.VisualAlert
NetworkLocation = structs.CarParams.NetworkLocation
LongCtrlState = structs.CarControl.Actuators.LongControlState
GearShifter = structs.CarState.GearShifter

# Camera cancels up to 0.1s after brake is pressed, ECM allows 0.5s
CAMERA_CANCEL_DELAY_FRAMES = 10
# Enforce a minimum interval between steering messages to avoid a fault
MIN_STEER_MSG_INTERVAL_MS = 15
TRAVERSE_COAST_MIN_SPEED = 5.0
TRAVERSE_COAST_ENTER_ACCEL = (-0.30, 0.05)
TRAVERSE_COAST_STAY_ACCEL = (-0.45, 0.12)
GM_AUTO_HOLD_BRAKE = 400
GM_AUTO_HOLD_SETTLED_ACCEL = 0.15
GM_AUTO_HOLD_SETTLED_SPEED = 0.01
GM_AUTO_HOLD_SETTLED_FRAMES = 5  # 0.20 seconds at the 25 Hz brake command rate
GM_AUTO_HOLD_SETTLE_TIMEOUT_FRAMES = 20  # Ensure hold engages even when aEgo remains noisy
GM_AUTO_HOLD_RAMP_STEP = 32
GM_AUTO_HOLD_ROLL_SPEED = 0.08
GM_STOPPING_BRAKE_TAPER_ZERO = 0
GM_STOPPING_BRAKE_TAPER_THREE_TENTHS_KPH = 1
GM_STOPPING_BRAKE_TAPER_HALF_KPH = 3
GM_STOPPING_BRAKE_TAPER_START_SPEED = 0.8 * CV.KPH_TO_MS
GM_STOPPING_BRAKE_TAPER_MAX = 12
# Keep the comfort taper limited to residual brake pressure. If longitudinal
# control asks for more than a very light stop, preserve the full command so
# smoothing cannot consume meaningful stopping distance.
GM_STOPPING_BRAKE_TAPER_LOW_SPEED_BYPASS = 20
GM_SNG_RESUME_ARM_TIMEOUT_FRAMES = round(2.0 / DT_CTRL)
GM_SNG_BUTTON_FRAMES = 4  # physical Traverse press: four frames over about 0.12 seconds
# Original buttons arrive at about 33 Hz. Allow 20-40 ms receive/control
# quantization plus 2 ms of jitter, but never compress missed frames into a burst.
GM_SNG_BUTTON_MIN_SOURCE_INTERVAL_NS = 18_000_000
GM_SNG_BUTTON_MIN_SEND_INTERVAL_NS = 25_000_000
GM_SNG_BUTTON_MAX_INTERVAL_NS = 50_000_000
GM_SNG_BUTTON_MAX_AGE_NS = 20_000_000
GM_SNG_MAX_RESUME_SPEED = 1.5
GM_EPB_HOLD_OVERLAP_FRAMES = 5  # 0.20 seconds at the 25 Hz brake command rate


def get_friction_brake_bus(CP):
  if CP.networkLocation == NetworkLocation.fwdCamera:
    return CanBus.CAMERA if CP.carFingerprint in SDGM_CAR else CanBus.POWERTRAIN
  return CanBus.CHASSIS


def get_acc_dashboard_speed_kph(CP, cluster_target_kph):
  if CP.carFingerprint in SDGM_CAR:
    return gm_raw_display_kph_from_cluster_display_kph(cluster_target_kph)
  return cluster_target_kph


def update_traverse_coasting(CP, coasting, long_active, stopping, v_ego, accel):
  if CP.carFingerprint != CAR.CHEVROLET_TRAVERSE or not long_active or stopping or v_ego < TRAVERSE_COAST_MIN_SPEED:
    return False
  accel_range = TRAVERSE_COAST_STAY_ACCEL if coasting else TRAVERSE_COAST_ENTER_ACCEL
  return accel_range[0] <= accel <= accel_range[1]


def limit_traverse_stopping_brake(CP, stopping, v_ego, apply_brake):
  if (CP.carFingerprint != CAR.CHEVROLET_TRAVERSE or not stopping or
      v_ego >= GM_STOPPING_BRAKE_TAPER_START_SPEED or
      apply_brake >= GM_STOPPING_BRAKE_TAPER_LOW_SPEED_BYPASS):
    return apply_brake
  brake_limit = round(np.interp(max(v_ego, 0.0),
                                [0.0, 0.15 * CV.KPH_TO_MS, 0.3 * CV.KPH_TO_MS,
                                 0.5 * CV.KPH_TO_MS, GM_STOPPING_BRAKE_TAPER_START_SPEED],
                                [GM_STOPPING_BRAKE_TAPER_ZERO, GM_STOPPING_BRAKE_TAPER_ZERO,
                                 GM_STOPPING_BRAKE_TAPER_THREE_TENTHS_KPH,
                                 GM_STOPPING_BRAKE_TAPER_HALF_KPH, GM_STOPPING_BRAKE_TAPER_MAX]))
  return min(apply_brake, brake_limit)


def gm_auto_hold_command(CP, CC, CS):
  return (
    CP.carFingerprint == CAR.CHEVROLET_TRAVERSE and
    not CC.longActive and not CC.enabled and not CS.out.cruiseState.enabled and
    CS.autoHold and CS.autoHoldActive and not CS.out.gasPressed and
    CS.out.gearShifter in (GearShifter.drive, GearShifter.low) and
    CS.out.vEgo < 0.05 and not CS.out.regenBraking and not CS.out.parkingBrake
  )


def gm_long_auto_hold_command(CP, CC, CS, actuators):
  return (
    CP.carFingerprint == CAR.CHEVROLET_TRAVERSE and CP.autoResumeSng and
    CC.longActive and actuators.longControlState == LongCtrlState.stopping and
    CS.longAutoHoldActive and not CS.out.gasPressed and not CS.out.regenBraking and
    CS.out.gearShifter in (GearShifter.drive, GearShifter.low) and CS.out.vEgo < 0.5 and
    not CS.out.parkingBrake
  )


def update_gm_long_auto_hold_brake(hold_requested, confirmed, zero_frames, settled_frames, hold_brake,
                                   regular_brake, v_ego_raw, a_ego):
  if not hold_requested:
    return regular_brake, False, 0, 0, 0

  raw_speed = abs(v_ego_raw)
  if confirmed:
    hold_brake = min(GM_AUTO_HOLD_BRAKE, max(hold_brake, regular_brake) + GM_AUTO_HOLD_RAMP_STEP)
    return hold_brake, True, zero_frames, settled_frames, hold_brake

  was_zero = zero_frames > 0
  if raw_speed <= GM_AUTO_HOLD_SETTLED_SPEED:
    zero_frames += 1
    settled_frames = settled_frames + 1 if abs(a_ego) <= GM_AUTO_HOLD_SETTLED_ACCEL else 0
  else:
    zero_frames = 0
    settled_frames = 0

  # A rolling vehicle takes priority over the comfort ramp. This path is only
  # reachable after CarState has already requested hold at a standstill.
  if was_zero and raw_speed > GM_AUTO_HOLD_ROLL_SPEED:
    return GM_AUTO_HOLD_BRAKE, True, zero_frames, settled_frames, GM_AUTO_HOLD_BRAKE

  if settled_frames < GM_AUTO_HOLD_SETTLED_FRAMES and zero_frames < GM_AUTO_HOLD_SETTLE_TIMEOUT_FRAMES:
    return regular_brake, False, zero_frames, settled_frames, 0

  hold_brake = min(GM_AUTO_HOLD_BRAKE, max(hold_brake, regular_brake) + GM_AUTO_HOLD_RAMP_STEP)
  return hold_brake, True, zero_frames, settled_frames, hold_brake


def gm_uses_auto_hold_sng(CP):
  return CP.carFingerprint == CAR.CHEVROLET_TRAVERSE and CP.autoResumeSng


def update_epb_hold_handoff(parking_brake, hold_requested, long_hold_requested,
                            hold_was_commanded, hold_was_long, overlap_frames):
  """Keep hydraulic pressure briefly while a confirmed EPB takes ownership."""
  overlap_active = False
  overlap_was_long = hold_was_long
  if parking_brake:
    if hold_was_commanded and overlap_frames == 0:
      overlap_frames = GM_EPB_HOLD_OVERLAP_FRAMES
    if overlap_frames > 0:
      overlap_active = True
      overlap_frames -= 1
    hold_was_commanded = overlap_frames > 0
    hold_was_long = overlap_was_long if hold_was_commanded else False
  else:
    overlap_frames = 0
    hold_was_commanded = hold_requested
    hold_was_long = long_hold_requested

  return overlap_active, overlap_was_long, hold_was_commanded, hold_was_long, overlap_frames


class CarController(CarControllerBase, IntelligentCruiseButtonManagementInterface):
  def __init__(self, dbc_names, CP, CP_SP):
    CarControllerBase.__init__(self, dbc_names, CP, CP_SP)
    IntelligentCruiseButtonManagementInterface.__init__(self, CP, CP_SP)
    self.start_time = 0.
    self.apply_torque_last = 0
    self.apply_gas = 0
    self.apply_brake = 0
    self.last_steer_frame = 0
    self.last_button_frame = 0
    self.cancel_counter = 0
    self.traverse_coasting = False
    self.sng_resume_request_prev = False
    self.sng_resume_attempted = False
    self.sng_brake_release_ns = 0
    self.sng_resume_frame = -1
    self.sng_resume_arm_ns = 0
    self.sng_last_stock_counter = None
    self.sng_last_stock_ts_ns = 0
    self.sng_last_sent_counter = None
    self.sng_last_sent_ns = 0
    self.sng_button_frames_remaining = 0
    self.gm_auto_hold_confirmed = False
    self.gm_auto_hold_zero_frames = 0
    self.gm_auto_hold_settled_frames = 0
    self.gm_auto_hold_brake = 0
    self.gm_epb_hold_overlap_frames = 0
    self.gm_hold_was_commanded = False
    self.gm_hold_was_long = False

    self.lka_steering_cmd_counter = 0
    self.lka_icon_status_last = (False, False)

    self.params = CarControllerParams(self.CP)

    self.packer_pt = CANPacker(DBC[self.CP.carFingerprint][Bus.pt])
    self.packer_obj = CANPacker(DBC[self.CP.carFingerprint][Bus.radar])
    self.packer_ch = CANPacker(DBC[self.CP.carFingerprint][Bus.chassis])

  def reset_sng_resume(self):
    self.sng_resume_frame = -1
    self.sng_resume_arm_ns = 0
    self.sng_last_stock_counter = None
    self.sng_last_stock_ts_ns = 0
    self.sng_last_sent_counter = None
    self.sng_last_sent_ns = 0
    self.sng_button_frames_remaining = 0

  def send_sng_button(self, can_sends, button, counter=None):
    if counter is None:
      if self.sng_last_sent_counter is None:
        return False
      counter = (self.sng_last_sent_counter + 1) & 0x3
    # Retain the existing two-bus request. This does not remove original button
    # frames from their source bus or prove that an ECU accepted the request.
    can_sends.append(gmcan.create_buttons(self.packer_pt, CanBus.CAMERA, counter, button))
    can_sends.append(gmcan.create_buttons(self.packer_pt, CanBus.POWERTRAIN, counter, button))
    self.sng_last_sent_counter = counter
    return True

  def update_sng_resume(self, CC, CS, actuators, can_sends, now_nanos):
    acknowledged_motion = (CS.out.canValid and not CS.out.accFaulted and
                           CS.out.cruiseState.enabled and not CS.out.cruiseState.standstill and
                           CS.out.vEgo > self.CP.vEgoStarting)
    # LongControl owns the automatic same-stop attempt latch. After it withdraws
    # the request and returns to stopping, a fresh explicit UI request may retry.
    # Toggling the request while still starting must not re-arm this sequencer.
    request_withdrawn_at_stop = not CC.cruiseControl.resume and actuators.longControlState == LongCtrlState.stopping
    if (not CC.enabled or not CC.longActive or CS.out.brakePressed or CS.out.gasPressed or
        acknowledged_motion or request_withdrawn_at_stop):
      self.sng_resume_attempted = False

    resume_eligible = (
      gm_uses_auto_hold_sng(self.CP) and CC.enabled and CC.longActive and
      actuators.longControlState == LongCtrlState.starting and CS.out.canValid and
      CS.out.cruiseState.enabled and not CS.out.accFaulted and
      not CS.out.regenBraking and not CS.out.parkingBrake and
      not CS.out.brakePressed and not CS.out.gasPressed and
      CS.out.gearShifter in (GearShifter.drive, GearShifter.low)
    )
    resume_request = (
      resume_eligible and CC.cruiseControl.resume and
      abs(CS.out.vEgo) < GM_SNG_MAX_RESUME_SPEED and CS.out.cruiseState.standstill and
      0 < self.sng_brake_release_ns < now_nanos and self.apply_brake == 0
    )
    stock_counter = int(CS.buttons_counter) & 0x3
    stock_ts = int(CS.buttons_ts_nanos)
    request_rising = resume_request and not self.sng_resume_request_prev
    self.sng_resume_request_prev = resume_request

    # Forwarding may have blocked this original CANCEL. Relay it with the next
    # synthetic counter before aborting; never wait for timing checks to pass.
    if self.sng_resume_frame >= 0 and CS.cruise_buttons == CruiseButtons.CANCEL:
      was_intercepting = self.sng_last_sent_counter is not None
      if was_intercepting:
        self.send_sng_button(can_sends, CruiseButtons.CANCEL)
      self.reset_sng_resume()
      return was_intercepting

    # Do not overlay an UNPRESS on a driver's RES/SET (or another physical
    # button). Panda ends interception when it receives a physical button;
    # forwarding may already have blocked that first frame before RX processing.
    if CS.cruise_buttons != CruiseButtons.UNPRESS:
      self.reset_sng_resume()
      return False

    if not resume_eligible or not CC.cruiseControl.resume or not CS.out.cruiseState.standstill:
      if self.sng_resume_frame >= 0:
        self.send_sng_button(can_sends, CruiseButtons.UNPRESS)
      self.reset_sng_resume()
      return False

    # LongControl supplies a request originating from a confirmed full stop.
    # First emit a zero brake command, then arm on a later control tick. This
    # records a command, not proof of actual hydraulic pressure release.
    # Snapshot the original frame on arm; an unset counter is not a new frame.
    if request_rising and not self.sng_resume_attempted and self.sng_resume_frame < 0:
      self.sng_resume_attempted = True
      if stock_ts <= 0 or not 0 <= now_nanos - stock_ts <= GM_SNG_BUTTON_MAX_INTERVAL_NS:
        return False
      self.sng_resume_frame = self.frame
      self.sng_resume_arm_ns = now_nanos
      self.sng_last_stock_counter = stock_counter
      self.sng_last_stock_ts_ns = stock_ts
      self.sng_last_sent_counter = None
      self.sng_button_frames_remaining = GM_SNG_BUTTON_FRAMES
      return True

    if self.sng_resume_frame < 0:
      return False

    source_age = now_nanos - stock_ts
    source_interval = stock_ts - self.sng_last_stock_ts_ns
    stock_frame_updated = source_interval > 0
    valid_source = (stock_ts > 0 and source_interval >= 0 and
                    0 <= source_age <= GM_SNG_BUTTON_MAX_INTERVAL_NS)
    if stock_frame_updated:
      valid_source &= (stock_ts > self.sng_resume_arm_ns and source_age <= GM_SNG_BUTTON_MAX_AGE_NS and
                       GM_SNG_BUTTON_MIN_SOURCE_INTERVAL_NS <= source_interval <= GM_SNG_BUTTON_MAX_INTERVAL_NS and
                       stock_counter == ((self.sng_last_stock_counter + 1) & 0x3))
    else:
      valid_source &= stock_counter == self.sng_last_stock_counter

    send_interval = now_nanos - self.sng_last_sent_ns
    valid_send = self.sng_last_sent_counter is None or send_interval <= GM_SNG_BUTTON_MAX_INTERVAL_NS
    if (not valid_source or not valid_send or self.apply_brake != 0 or
        abs(CS.out.vEgo) >= GM_SNG_MAX_RESUME_SPEED or
        self.frame - self.sng_resume_frame > GM_SNG_RESUME_ARM_TIMEOUT_FRAMES):
      self.send_sng_button(can_sends, CruiseButtons.UNPRESS)
      self.reset_sng_resume()
      return True

    if not stock_frame_updated:
      return True
    if self.sng_last_sent_counter is not None and send_interval < GM_SNG_BUTTON_MIN_SEND_INTERVAL_NS:
      # Keep this source frame pending. If it becomes stale or the next counter
      # arrives before we can send, the validation above aborts instead.
      return True
    self.sng_last_stock_counter = stock_counter
    self.sng_last_stock_ts_ns = stock_ts

    if self.sng_button_frames_remaining > 0:
      resume_counter = (stock_counter + 1) & 0x3 if self.sng_last_sent_counter is None else None
      self.send_sng_button(can_sends, CruiseButtons.RES_ACCEL, resume_counter)
      self.sng_last_sent_ns = now_nanos
      self.sng_button_frames_remaining -= 1
    else:
      self.send_sng_button(can_sends, CruiseButtons.UNPRESS)
      self.reset_sng_resume()

    return True

  def update(self, CC, CC_SP, CS, now_nanos):
    actuators = CC.actuators
    hud_control = CC.hudControl
    hud_alert = hud_control.visualAlert
    hud_v_cruise = hud_control.setSpeed
    if hud_v_cruise > 70:
      hud_v_cruise = 0

    # Send CAN commands.
    can_sends = []

    # Steering (Active: 50Hz, inactive: 10Hz)
    steer_step = self.params.STEER_STEP if CC.latActive else self.params.INACTIVE_STEER_STEP

    if self.CP.networkLocation == NetworkLocation.fwdCamera:
      # Also send at 50Hz:
      # - on startup, first few msgs are blocked
      # - until we're in sync with camera so counters align when relay closes, preventing a fault.
      #   openpilot can subtly drift, so this is activated throughout a drive to stay synced
      out_of_sync = self.lka_steering_cmd_counter % 4 != (CS.cam_lka_steering_cmd_counter + 1) % 4
      if CS.loopback_lka_steering_cmd_ts_nanos == 0 or out_of_sync:
        steer_step = self.params.STEER_STEP

    self.lka_steering_cmd_counter += 1 if CS.loopback_lka_steering_cmd_updated else 0

    # Avoid GM EPS faults when transmitting messages too close together: skip this transmit if we
    # received the ASCMLKASteeringCmd loopback confirmation too recently
    last_lka_steer_msg_ms = (now_nanos - CS.loopback_lka_steering_cmd_ts_nanos) * 1e-6
    if (self.frame - self.last_steer_frame) >= steer_step and last_lka_steer_msg_ms > MIN_STEER_MSG_INTERVAL_MS:
      # Initialize ASCMLKASteeringCmd counter using the camera until we get a msg on the bus
      if CS.loopback_lka_steering_cmd_ts_nanos == 0:
        self.lka_steering_cmd_counter = CS.pt_lka_steering_cmd_counter + 1

      if CC.latActive:
        new_torque = int(round(actuators.torque * self.params.STEER_MAX))
        apply_torque = apply_driver_steer_torque_limits(new_torque, self.apply_torque_last, CS.out.steeringTorque, self.params)
      else:
        apply_torque = 0

      self.last_steer_frame = self.frame
      self.apply_torque_last = apply_torque
      idx = self.lka_steering_cmd_counter % 4
      can_sends.append(gmcan.create_steering_control(self.packer_pt, CanBus.POWERTRAIN, apply_torque, idx, CC.latActive))

    if self.CP.openpilotLongitudinalControl:
      # Stock steering-button frames update faster than the 25 Hz longitudinal
      # messages, so track every control frame without skipping counters.
      self.update_sng_resume(CC, CS, actuators, can_sends, now_nanos)

      # Gas/regen, brakes, and UI commands - all at 25Hz
      if self.frame % 4 == 0:
        stopping = actuators.longControlState == LongCtrlState.stopping
        if not CC.longActive:
          self.traverse_coasting = False
          # ASCM sends max regen when not enabled
          self.apply_gas = self.params.INACTIVE_REGEN
          self.apply_brake = 0
        else:
          self.traverse_coasting = update_traverse_coasting(
            self.CP, self.traverse_coasting, CC.longActive, stopping, CS.out.vEgo, actuators.accel)
          if self.traverse_coasting:
            self.apply_gas = 0.0
            self.apply_brake = 0
          else:
            self.apply_gas = float(np.interp(actuators.accel, self.params.GAS_LOOKUP_BP, self.params.GAS_LOOKUP_V))
            self.apply_brake = int(round(np.interp(actuators.accel, self.params.BRAKE_LOOKUP_BP, self.params.BRAKE_LOOKUP_V)))
          # Don't allow any gas above inactive regen while stopping
          # FIXME: brakes aren't applied immediately when enabling at a stop
          if stopping:
            self.apply_gas = self.params.INACTIVE_REGEN
            self.apply_brake = limit_traverse_stopping_brake(
              self.CP, stopping, CS.out.vEgo, self.apply_brake)

        idx = (self.frame // 4) % 4

        at_full_stop = CC.longActive and CS.out.standstill
        near_stop = CC.longActive and (abs(CS.out.vEgo) < self.params.NEAR_STOP_BRAKE_PHASE)
        friction_brake_bus = get_friction_brake_bus(self.CP)
        # GM Camera exceptions
        # TODO: can we always check the longControlState?
        if gm_uses_auto_hold_sng(self.CP):
          # Never ask the Traverse ACC ECU to latch its non-resumable full-stop
          # state. Physical standstill is retained by the GM hydraulic hold.
          at_full_stop = False
        elif self.CP.networkLocation == NetworkLocation.fwdCamera:
          at_full_stop = at_full_stop and stopping

        manual_auto_hold = gm_auto_hold_command(self.CP, CC, CS)
        long_auto_hold = gm_long_auto_hold_command(self.CP, CC, CS, actuators)
        epb_hold_overlap, epb_overlap_was_long, self.gm_hold_was_commanded, \
          self.gm_hold_was_long, self.gm_epb_hold_overlap_frames = update_epb_hold_handoff(
            CS.out.parkingBrake, manual_auto_hold or long_auto_hold, long_auto_hold,
            self.gm_hold_was_commanded, self.gm_hold_was_long, self.gm_epb_hold_overlap_frames)

        long_hold_brake, self.gm_auto_hold_confirmed, self.gm_auto_hold_zero_frames, \
          self.gm_auto_hold_settled_frames, self.gm_auto_hold_brake = update_gm_long_auto_hold_brake(
            long_auto_hold, self.gm_auto_hold_confirmed, self.gm_auto_hold_zero_frames,
            self.gm_auto_hold_settled_frames, self.gm_auto_hold_brake, self.apply_brake,
            CS.out.vEgoRaw, CS.out.aEgo)

        # GasRegenCmdActive needs to be 1 to avoid cruise faults. It describes the ACC state, not actuation
        can_sends.append(gmcan.create_gas_regen_command(self.packer_pt, CanBus.POWERTRAIN, self.apply_gas,
                                                        idx, CC.enabled, at_full_stop))
        if manual_auto_hold or long_auto_hold or epb_hold_overlap:
          hold_brake = GM_AUTO_HOLD_BRAKE if manual_auto_hold or epb_hold_overlap else long_hold_brake
          hold_enabled = CC.enabled and (long_auto_hold or (epb_hold_overlap and epb_overlap_was_long))
          can_sends.append(gmcan.create_friction_brake_command(self.packer_ch, friction_brake_bus, hold_brake,
                                                               idx, hold_enabled, True, False, self.CP))
          self.apply_brake = hold_brake
          CS.autoHoldActivated = not epb_hold_overlap
        else:
          can_sends.append(gmcan.create_friction_brake_command(self.packer_ch, friction_brake_bus, self.apply_brake,
                                                               idx, CC.enabled, near_stop, at_full_stop, self.CP))
          CS.autoHoldActivated = False

        # SNG runs before this 25 Hz output block, so a later control tick must
        # observe this emitted release before it can arm a RES sequence.
        self.sng_brake_release_ns = now_nanos if self.apply_brake == 0 else 0

        # Send dashboard UI commands (ACC status)
        # SASCM blocks the stock 0x370 message while openpilot longitudinal is
        # active. Preserve its FCW field in the replacement dashboard message
        # so the stock red collision LEDs remain available.
        fcw_alert = 0x3 if hud_alert == VisualAlert.fcw else CS.stock_fcw_alert
        dashboard_speed_kph = get_acc_dashboard_speed_kph(self.CP, hud_v_cruise * CV.MS_TO_KPH)
        can_sends.append(gmcan.create_acc_dashboard_command(self.packer_pt, CanBus.POWERTRAIN, CC.enabled,
                                                            dashboard_speed_kph, hud_control, fcw_alert))

      # Radar needs to know current speed and yaw rate (50hz),
      # and that ADAS is alive (10hz)
      if not self.CP.radarUnavailable:
        tt = self.frame * DT_CTRL
        time_and_headlights_step = 10
        if self.frame % time_and_headlights_step == 0:
          idx = (self.frame // time_and_headlights_step) % 4
          can_sends.append(gmcan.create_adas_time_status(CanBus.OBSTACLE, int((tt - self.start_time) * 60), idx))
          can_sends.append(gmcan.create_adas_headlights_status(self.packer_obj, CanBus.OBSTACLE))

        speed_and_accelerometer_step = 2
        if self.frame % speed_and_accelerometer_step == 0:
          idx = (self.frame // speed_and_accelerometer_step) % 4
          can_sends.append(gmcan.create_adas_steering_status(CanBus.OBSTACLE, idx))
          can_sends.append(gmcan.create_adas_accelerometer_speed_status(CanBus.OBSTACLE, abs(CS.out.vEgo), idx))

      if self.CP.networkLocation == NetworkLocation.gateway and self.frame % self.params.ADAS_KEEPALIVE_STEP == 0:
        can_sends += gmcan.create_adas_keepalive(CanBus.POWERTRAIN)

    else:
      # While car is braking, cancel button causes ECM to enter a soft disable state with a fault status.
      # A delayed cancellation allows camera to cancel and avoids a fault when user depresses brake quickly
      self.cancel_counter = self.cancel_counter + 1 if CC.cruiseControl.cancel else 0

      # Stock longitudinal, integrated at camera
      if self.cancel_counter > 0:
        self.reset_button_sequence()
        if self.cancel_counter > CAMERA_CANCEL_DELAY_FRAMES and (self.frame - self.last_button_frame) * DT_CTRL > 0.04:
          self.last_button_frame = self.frame
          can_sends.append(gmcan.create_buttons(self.packer_pt, CanBus.CAMERA, CS.buttons_counter, CruiseButtons.CANCEL))
      else:
        icbm_sends = IntelligentCruiseButtonManagementInterface.update(self, CS, CC_SP, self.packer_pt, self.frame)
        if icbm_sends:
          self.last_button_frame = self.frame
          can_sends.extend(icbm_sends)

    if self.CP.networkLocation == NetworkLocation.fwdCamera:
      # Silence "Take Steering" alert sent by camera, forward PSCMStatus with HandsOffSWlDetectionStatus=1
      if self.frame % 10 == 0:
        can_sends.append(gmcan.create_pscm_status(self.packer_pt, CanBus.CAMERA, CS.pscm_status))

    new_actuators = actuators.as_builder()
    new_actuators.torque = self.apply_torque_last / self.params.STEER_MAX
    new_actuators.torqueOutputCan = self.apply_torque_last
    new_actuators.gas = self.apply_gas
    new_actuators.brake = self.apply_brake

    self.frame += 1
    return new_actuators, can_sends
