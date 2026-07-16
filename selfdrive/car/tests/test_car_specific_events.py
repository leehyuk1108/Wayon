from cereal import car, log
from opendbc.car.gm.values import CAR

from openpilot.selfdrive.car.car_specific import CarSpecificEvents


EventName = log.OnroadEvent.EventName


def gm_events(cruise_standstill: bool) -> list[int]:
  CP = car.CarParams.new_message()
  CP.brand = "gm"
  CP.carFingerprint = CAR.CHEVROLET_TRAVERSE
  CP.pcmCruise = True

  CS = car.CarState.new_message()
  CS.gearShifter = car.CarState.GearShifter.drive
  CS.cruiseState.available = True
  CS.cruiseState.enabled = True
  CS.cruiseState.standstill = cruise_standstill
  CS.standstill = cruise_standstill
  CS.lowSpeedAlert = True

  CS_prev = car.CarState.new_message()
  CS_prev.cruiseState.enabled = True
  CC = car.CarControl.new_message()

  return CarSpecificEvents(CP).update(CS, CS_prev, CC).names


def test_gm_autohold_prefers_resume_timer_over_low_speed_steer_alert():
  events = gm_events(cruise_standstill=True)

  assert EventName.resumeRequired in events
  assert EventName.belowSteerSpeed not in events


def test_gm_low_speed_steer_alert_remains_outside_autohold():
  events = gm_events(cruise_standstill=False)

  assert EventName.resumeRequired not in events
  assert EventName.belowSteerSpeed in events
