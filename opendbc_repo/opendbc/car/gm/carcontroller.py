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
GM_AUTO_HOLD_BRAKE = 1
GM_SNG_RESET_TIMEOUT_FRAMES = max(1, round(2.5 / DT_CTRL))
GM_SNG_BUTTON_FRAMES = 5


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


def gm_auto_hold_command(CP, CC, CS):
  return (
    CP.carFingerprint == CAR.CHEVROLET_TRAVERSE and
    not CC.longActive and not CC.enabled and not CS.out.cruiseState.enabled and
    CS.autoHold and CS.autoHoldActive and not CS.out.gasPressed and
    CS.out.gearShifter in (GearShifter.drive, GearShifter.low) and
    CS.out.vEgo < 0.05 and not CS.out.regenBraking
  )


def gm_long_auto_hold_command(CP, CC, CS, actuators):
  return (
    CP.carFingerprint == CAR.CHEVROLET_TRAVERSE and CP.autoResumeSng and
    CC.longActive and actuators.longControlState == LongCtrlState.stopping and
    CS.longAutoHoldActive and not CS.out.gasPressed and not CS.out.regenBraking and
    CS.out.gearShifter in (GearShifter.drive, GearShifter.low) and CS.out.standstill
  )


def gm_uses_auto_hold_sng(CP):
  return CP.carFingerprint == CAR.CHEVROLET_TRAVERSE and CP.autoResumeSng


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
    self.sng_resume_frame = -1
    self.sng_last_stock_counter = None
    self.sng_last_sent_counter = None
    self.sng_button_frames_remaining = 0

    self.lka_steering_cmd_counter = 0
    self.lka_icon_status_last = (False, False)

    self.params = CarControllerParams(self.CP)

    self.packer_pt = CANPacker(DBC[self.CP.carFingerprint][Bus.pt])
    self.packer_obj = CANPacker(DBC[self.CP.carFingerprint][Bus.radar])
    self.packer_ch = CANPacker(DBC[self.CP.carFingerprint][Bus.chassis])

  def reset_sng_resume(self):
    self.sng_resume_frame = -1
    self.sng_last_stock_counter = None
    self.sng_last_sent_counter = None
    self.sng_button_frames_remaining = 0

  def send_sng_button(self, can_sends, button, counter=None):
    if counter is None:
      if self.sng_last_sent_counter is None:
        return False
      counter = (self.sng_last_sent_counter + 1) & 0x3
    # A physical Traverse RES frame is visible on the powertrain side before
    # it reaches the isolated camera side. Mirror the same payload and rolling
    # counter onto both sides so both receivers observe one coherent press.
    can_sends.append(gmcan.create_buttons(self.packer_pt, CanBus.CAMERA, counter, button))
    can_sends.append(gmcan.create_buttons(self.packer_pt, CanBus.POWERTRAIN, counter, button))
    self.sng_last_sent_counter = counter
    return True

  def update_sng_resume(self, CC, CS, actuators, can_sends):
    resume_request = (
      gm_uses_auto_hold_sng(self.CP) and CC.enabled and CC.longActive and
      CC.cruiseControl.resume and actuators.longControlState == LongCtrlState.starting and
      not CS.out.brakePressed and not CS.out.gasPressed and
      CS.out.gearShifter in (GearShifter.drive, GearShifter.low)
    )

    resume_eligible = (
      gm_uses_auto_hold_sng(self.CP) and CC.enabled and CC.longActive and
      not CS.out.brakePressed and not CS.out.gasPressed and
      CS.out.gearShifter in (GearShifter.drive, GearShifter.low)
    )

    stock_counter = int(CS.buttons_counter) & 0x3
    stock_frame_updated = self.sng_last_stock_counter is None or stock_counter != self.sng_last_stock_counter

    # The stock CANCEL frame is blocked during interception. Relay CANCEL with
    # the next synthetic counter before aborting so driver input wins.
    if (self.sng_resume_frame >= 0 and stock_frame_updated and
        CS.cruise_buttons == CruiseButtons.CANCEL):
      self.send_sng_button(can_sends, CruiseButtons.CANCEL)
      self.reset_sng_resume()
      self.sng_resume_request_prev = False
      return True

    if not resume_eligible:
      self.reset_sng_resume()
      self.sng_resume_request_prev = False
      return False

    if resume_request and not self.sng_resume_request_prev and self.sng_resume_frame < 0:
      self.sng_resume_frame = self.frame
      self.sng_last_stock_counter = None
      self.sng_last_sent_counter = None
      self.sng_button_frames_remaining = GM_SNG_BUTTON_FRAMES
    self.sng_resume_request_prev = resume_request

    if self.sng_resume_frame < 0:
      return False

    if not CS.out.cruiseState.standstill:
      self.send_sng_button(can_sends, CruiseButtons.UNPRESS)
      self.reset_sng_resume()
      return True

    if self.frame - self.sng_resume_frame > GM_SNG_RESET_TIMEOUT_FRAMES:
      self.send_sng_button(can_sends, CruiseButtons.UNPRESS)
      self.reset_sng_resume()
      return True

    # A physical RES press replaces about five consecutive 33 Hz button
    # messages. Transmit the next rolling counter to the camera side as soon as
    # each stock UNPRESS arrives; Panda suppresses the matching stock frame.
    if stock_frame_updated:
      self.sng_last_stock_counter = stock_counter

    if (stock_frame_updated and self.sng_button_frames_remaining > 0 and
        CS.cruise_buttons == CruiseButtons.UNPRESS):
      resume_counter = (stock_counter + 1) & 0x3 if self.sng_last_sent_counter is None else None
      self.send_sng_button(can_sends, CruiseButtons.RES_ACCEL, resume_counter)
      self.sng_button_frames_remaining -= 1
    elif (stock_frame_updated and self.sng_button_frames_remaining == 0 and
          CS.cruise_buttons == CruiseButtons.UNPRESS):
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
      sng_resume_active = self.update_sng_resume(CC, CS, actuators, can_sends)

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

        if sng_resume_active:
          # Preserve hydraulic hold and inactive gas until the ECU acknowledges
          # RES by clearing CruiseState.standstill. Only then may normal launch
          # acceleration proceed.
          self.apply_brake = GM_AUTO_HOLD_BRAKE
          at_full_stop = False
          self.apply_gas = self.params.INACTIVE_REGEN

        # GasRegenCmdActive needs to be 1 to avoid cruise faults. It describes the ACC state, not actuation
        can_sends.append(gmcan.create_gas_regen_command(self.packer_pt, CanBus.POWERTRAIN, self.apply_gas,
                                                        idx, CC.enabled, at_full_stop))
        if sng_resume_active:
          can_sends.append(gmcan.create_friction_brake_command(self.packer_ch, friction_brake_bus, GM_AUTO_HOLD_BRAKE,
                                                               idx, CC.enabled, True, False, self.CP))
          CS.autoHoldActivated = True
        elif manual_auto_hold or long_auto_hold:
          can_sends.append(gmcan.create_friction_brake_command(self.packer_ch, friction_brake_bus, GM_AUTO_HOLD_BRAKE,
                                                               idx, CC.enabled and long_auto_hold, True, False, self.CP))
          CS.autoHoldActivated = True
        else:
          can_sends.append(gmcan.create_friction_brake_command(self.packer_ch, friction_brake_bus, self.apply_brake,
                                                               idx, CC.enabled, near_stop, at_full_stop, self.CP))
          CS.autoHoldActivated = False

        # Send dashboard UI commands (ACC status)
        send_fcw = hud_alert == VisualAlert.fcw
        dashboard_speed_kph = get_acc_dashboard_speed_kph(self.CP, hud_v_cruise * CV.MS_TO_KPH)
        can_sends.append(gmcan.create_acc_dashboard_command(self.packer_pt, CanBus.POWERTRAIN, CC.enabled,
                                                            dashboard_speed_kph, hud_control, send_fcw))

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
