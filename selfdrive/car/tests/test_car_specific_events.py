import pytest

from cereal import car, log
from opendbc.car.gm.values import CAR

from openpilot.selfdrive.car.car_specific import CarSpecificEvents
from openpilot.selfdrive.selfdrived.alertmanager import AlertManager
from openpilot.selfdrive.selfdrived.events import Events
from openpilot.selfdrive.selfdrived.state import StateMachine


EventName = log.OnroadEvent.EventName


def gm_events(cruise_standstill: bool, vehicle_standstill: bool | None = None,
              auto_resume_sng: bool = False, parking_brake: bool = False,
              gear=car.CarState.GearShifter.drive) -> list[int]:
  CP = car.CarParams.new_message()
  CP.brand = "gm"
  CP.carFingerprint = CAR.CHEVROLET_TRAVERSE
  CP.pcmCruise = True
  CP.openpilotLongitudinalControl = True
  CP.autoResumeSng = auto_resume_sng

  CS = car.CarState.new_message()
  CS.gearShifter = gear
  CS.parkingBrake = parking_brake
  CS.cruiseState.available = True
  CS.cruiseState.enabled = True
  CS.cruiseState.standstill = cruise_standstill
  CS.standstill = cruise_standstill if vehicle_standstill is None else vehicle_standstill
  CS.lowSpeedAlert = True

  CS_prev = car.CarState.new_message()
  CS_prev.cruiseState.enabled = True
  CC = car.CarControl.new_message()
  CC.longActive = auto_resume_sng
  if auto_resume_sng:
    CC.actuators.longControlState = car.CarControl.Actuators.LongControlState.stopping

  return CarSpecificEvents(CP).update(CS, CS_prev, CC).names


def test_gm_autohold_prefers_resume_timer_over_low_speed_steer_alert():
  events = gm_events(cruise_standstill=True)

  assert EventName.resumeRequired in events
  assert EventName.belowSteerSpeed not in events


def test_gm_low_speed_steer_alert_remains_outside_autohold():
  events = gm_events(cruise_standstill=False)

  assert EventName.resumeRequired not in events
  assert EventName.belowSteerSpeed in events


def test_gm_autohold_timer_ends_when_vehicle_starts_creeping():
  events = gm_events(cruise_standstill=True, vehicle_standstill=False)

  assert EventName.resumeRequired not in events
  assert EventName.belowSteerSpeed in events


def test_gm_hold_timer_uses_physical_stop_without_ecu_standstill():
  events = gm_events(cruise_standstill=False, vehicle_standstill=True, auto_resume_sng=True)

  assert EventName.resumeRequired in events
  assert EventName.belowSteerSpeed not in events


def test_gm_hold_timer_is_hidden_with_parking_brake():
  events = gm_events(cruise_standstill=False, vehicle_standstill=True,
                     auto_resume_sng=True, parking_brake=True)

  assert EventName.resumeRequired not in events
  assert EventName.parkBrake in events

  pcm_events = gm_events(cruise_standstill=True, parking_brake=True)
  assert EventName.resumeRequired not in pcm_events


def test_gm_hold_timer_is_hidden_outside_drive():
  events = gm_events(cruise_standstill=False, vehicle_standstill=True,
                     auto_resume_sng=True, gear=car.CarState.GearShifter.park)

  assert EventName.resumeRequired not in events


@pytest.mark.parametrize("speed", [0.12, 0.651, 1.2, -0.12, -1.2])
@pytest.mark.parametrize("engaged", [False, True])
def test_gm_autohold_warns_after_sustained_uncommanded_movement(speed, engaged):
  CP = car.CarParams.new_message()
  CP.brand = "gm"
  CP.carFingerprint = CAR.CHEVROLET_TRAVERSE
  CP.openpilotLongitudinalControl = True
  CP.autoResumeSng = True

  CS = car.CarState.new_message()
  CS.gearShifter = car.CarState.GearShifter.drive
  CS.cruiseState.available = True
  CS.standstill = True
  CS.brakeHoldActive = True
  CS_prev = car.CarState.new_message()
  CC = car.CarControl.new_message()
  detector = CarSpecificEvents(CP)

  detector.update(CS, CS_prev, CC)
  CS.standstill = False
  CS.vEgo = speed
  for _ in range(31):
    events = detector.update(CS, CS_prev, CC)

  assert EventName.gmAutoHoldMoving in events.names

  # Check the real state-machine filter and alert selection, not just detection.
  machine = StateMachine()
  machine.state = log.SelfdriveState.OpenpilotState.enabled if engaged else log.SelfdriveState.OpenpilotState.disabled
  alert_events = Events()
  alert_events.add(EventName.gmAutoHoldMoving)
  machine.update(alert_events)
  manager = AlertManager()
  manager.add_many(0, alert_events.create_alerts(machine.current_alert_types))
  manager.process_alerts(0, set())
  alert = manager.current_alert
  assert alert.alert_type == "gmAutoHoldMoving/permanent"
  assert alert.audible_alert == car.CarControl.HUDControl.AudibleAlert.prompt
  assert alert.visual_alert == car.CarControl.HUDControl.VisualAlert.brakePressed

  CS.vEgo = 0.0
  assert EventName.gmAutoHoldMoving not in detector.update(CS, CS_prev, CC).names


@pytest.mark.parametrize("release", ["gas", "regen", "epb", "gear", "latch"])
def test_gm_manual_hold_warning_clears_on_release(release):
  CP = car.CarParams.new_message()
  CP.brand = "gm"
  CP.carFingerprint = CAR.CHEVROLET_TRAVERSE
  CS = car.CarState.new_message()
  CS.gearShifter = car.CarState.GearShifter.drive
  CS.brakeHoldActive = True
  CS.vEgo = 0.2
  CS_prev = car.CarState.new_message()
  CC = car.CarControl.new_message()
  detector = CarSpecificEvents(CP)
  for _ in range(31):
    events = detector.update(CS, CS_prev, CC)
  assert EventName.gmAutoHoldMoving in events.names

  if release == "gas":
    CS.gasPressed = True
  elif release == "regen":
    CS.regenBraking = True
  elif release == "epb":
    CS.parkingBrake = True
  elif release == "gear":
    CS.gearShifter = car.CarState.GearShifter.park
  else:
    CS.brakeHoldActive = False
  assert EventName.gmAutoHoldMoving not in detector.update(CS, CS_prev, CC).names


def test_gm_manual_hold_warning_rejects_short_movement():
  CP = car.CarParams.new_message()
  CP.brand = "gm"
  CP.carFingerprint = CAR.CHEVROLET_TRAVERSE
  CS = car.CarState.new_message()
  CS.gearShifter = car.CarState.GearShifter.drive
  CS.brakeHoldActive = True
  CS_prev = car.CarState.new_message()
  CC = car.CarControl.new_message()
  detector = CarSpecificEvents(CP)
  for _ in range(3):
    CS.vEgo = 0.2
    for _ in range(29):
      assert EventName.gmAutoHoldMoving not in detector.update(CS, CS_prev, CC).names
    CS.vEgo = 0.0
    assert EventName.gmAutoHoldMoving not in detector.update(CS, CS_prev, CC).names


def test_gm_autohold_does_not_warn_during_requested_release():
  CP = car.CarParams.new_message()
  CP.brand = "gm"
  CP.carFingerprint = CAR.CHEVROLET_TRAVERSE
  CP.openpilotLongitudinalControl = True
  CP.autoResumeSng = True

  CS = car.CarState.new_message()
  CS.gearShifter = car.CarState.GearShifter.drive
  CS.cruiseState.available = True
  CS.standstill = True
  CS_prev = car.CarState.new_message()
  CC = car.CarControl.new_message()
  CC.longActive = True
  CC.actuators.longControlState = car.CarControl.Actuators.LongControlState.stopping
  detector = CarSpecificEvents(CP)

  detector.update(CS, CS_prev, CC)
  CS.standstill = False
  CS.vEgo = 0.12
  CC.actuators.longControlState = car.CarControl.Actuators.LongControlState.pid
  for _ in range(31):
    events = detector.update(CS, CS_prev, CC).names

  assert EventName.gmAutoHoldMoving not in events
