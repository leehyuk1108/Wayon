#!/usr/bin/env python3

import math
import os
import numpy as np

from cereal import messaging, car
from openpilot.common.constants import CV
from opendbc.car.vehicle_model import VehicleModel
from openpilot.common.realtime import DT_CTRL, Ratekeeper
from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog
from openpilot.tools.joystick.remote_control_limits import joystick_cc_enabled, remote_control_limits, remote_hud_set_speed_kph

LongCtrlState = car.CarControl.Actuators.LongControlState
MAX_LAT_ACCEL = 3.0
REMOTE_CONTROL_SESSION = "/data/RemoteControlNextDrive"


def joystickd_thread():
  params = Params()
  cloudlog.info("joystickd is waiting for CarParams")
  CP = messaging.log_from_bytes(params.get("CarParams", block=True), car.CarParams)
  VM = VehicleModel(CP)
  # This file is created offroad by the authenticated :4444 page. It remains
  # present for exactly one onroad cycle, then the web process removes it when
  # the device returns offroad.
  remote_control = os.path.isfile(REMOTE_CONTROL_SESSION)

  sm = messaging.SubMaster(['carState', 'onroadEvents', 'liveParameters', 'selfdriveState', 'testJoystick'], frequency=1. / DT_CTRL)
  pm = messaging.PubMaster(['carControl', 'controlsState'])

  rk = Ratekeeper(100, print_delay_threshold=None)
  while 1:
    sm.update(0)

    # A dead publisher must disengage remote control even if its last message
    # claimed an armed session.
    should_reset_joystick = sm.recv_frame['testJoystick'] == 0 or (sm.frame - sm.recv_frame['testJoystick'])*DT_CTRL > 0.2

    cc_msg = messaging.new_message('carControl')
    cc_msg.valid = True
    CC = cc_msg.carControl
    if not should_reset_joystick:
      joystick_axes = sm['testJoystick'].axes
    else:
      joystick_axes = [0.0, 0.0]

    remote_input_active = (not remote_control or
                           (not should_reset_joystick and len(sm['testJoystick'].buttons) > 0 and
                            sm['testJoystick'].buttons[0]))
    remote_vehicle_ready = (not remote_control or
                            (sm['carState'].gearShifter in (car.CarState.GearShifter.drive,
                                                            car.CarState.GearShifter.low) and
                             not sm['carState'].gasPressed and not sm['carState'].brakePressed and
                             not sm['carState'].parkingBrake))
    # Losing the web heartbeat immediately zeros actuation, but it must not
    # toggle GM's ACC command-active state. A delayed active edge without a
    # fresh physical SET/RES edge makes the Traverse ACC enter FAULTED after
    # roughly 500 ms. Keep enabled synchronized with selfdrived/Panda instead.
    if remote_control and (not remote_input_active or not remote_vehicle_ready):
      joystick_axes = [0.0, 0.0]
    remote_accel, remote_torque = remote_control_limits(joystick_axes[0], joystick_axes[1], sm['carState'].vEgo)
    CC.enabled = joystick_cc_enabled(sm['selfdriveState'].enabled, remote_control,
                                     remote_input_active, remote_vehicle_ready)
    remote_steering_requested = not remote_control or abs(remote_torque) > 1e-3
    CC.latActive = (CC.enabled and remote_steering_requested and sm['selfdriveState'].active and
                    not sm['carState'].steerFaultTemporary and not sm['carState'].steerFaultPermanent)
    CC.longActive = CC.enabled and not any(e.overrideLongitudinal for e in sm['onroadEvents']) and CP.openpilotLongitudinalControl
    CC.cruiseControl.cancel = sm['carState'].cruiseState.enabled and (not CC.enabled or not CP.pcmCruise)
    CC.hudControl.setSpeed = remote_hud_set_speed_kph(sm['carState'].vCruiseCluster) * CV.KPH_TO_MS
    CC.hudControl.speedVisible = CC.enabled
    CC.hudControl.lanesVisible = CC.enabled
    CC.hudControl.leadDistanceBars = 2

    actuators = CC.actuators

    if CC.longActive:
      if remote_control:
        actuators.accel = remote_accel
      else:
        actuators.accel = 4.0 * float(np.clip(joystick_axes[0], -1, 1))
      if remote_control and actuators.accel > 0.0 and sm['carState'].vEgo <= CP.vEgoStopping:
        actuators.longControlState = LongCtrlState.starting
      else:
        actuators.longControlState = LongCtrlState.pid if sm['carState'].vEgo > CP.vEgoStopping else LongCtrlState.stopping
      CC.cruiseControl.resume = actuators.accel > 0.0

    if CC.latActive:
      max_curvature = MAX_LAT_ACCEL / max(sm['carState'].vEgo ** 2, 5)
      max_angle = math.degrees(VM.get_steer_from_curvature(max_curvature, sm['carState'].vEgo, sm['liveParameters'].roll))

      if remote_control:
        actuators.torque = remote_torque
      else:
        actuators.torque = float(np.clip(joystick_axes[1], -1, 1))
      actuators.steeringAngleDeg, actuators.curvature = actuators.torque * max_angle, actuators.torque * -max_curvature

    pm.send('carControl', cc_msg)

    cs_msg = messaging.new_message('controlsState')
    cs_msg.valid = True
    controlsState = cs_msg.controlsState
    controlsState.lateralControlState.init('debugState')

    lp = sm['liveParameters']
    steer_angle_without_offset = math.radians(sm['carState'].steeringAngleDeg - lp.angleOffsetDeg)
    controlsState.curvature = -VM.calc_curvature(steer_angle_without_offset, sm['carState'].vEgo, lp.roll)

    pm.send('controlsState', cs_msg)

    rk.keep_time()


def main():
  joystickd_thread()


if __name__ == "__main__":
  main()
