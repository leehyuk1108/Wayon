from cereal import car, log
from opendbc.car.gm.values import CAR

from openpilot.selfdrive.car.car_specific import CarSpecificEvents


EventName = log.OnroadEvent.EventName


def gm_events(cruise_standstill: bool, vehicle_standstill: bool | None = None,
              auto_resume_sng: bool = False) -> list[int]:
  CP = car.CarParams.new_message()
  CP.brand = "gm"
  CP.carFingerprint = CAR.CHEVROLET_TRAVERSE
  CP.pcmCruise = True
  CP.openpilotLongitudinalControl = True
  CP.autoResumeSng = auto_resume_sng

  CS = car.CarState.new_message()
  CS.gearShifter = car.CarState.GearShifter.drive
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
