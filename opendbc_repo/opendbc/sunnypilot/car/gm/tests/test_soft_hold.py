from opendbc.car import structs
from opendbc.car.gm.carstate import CarState
from opendbc.sunnypilot.car.gm.soft_hold import SOFT_HOLD_PRESS_THRESHOLD, SoftHoldController


GearShifter = structs.CarState.GearShifter


def update(controller, brake=0, standstill=True, gear=GearShifter.drive, gas=False,
           resume=False, cancel=False, door=False, seatbelt=False, available=True):
  return controller.update(
    brake_pedal_position=brake,
    standstill=standstill,
    gear_shifter=gear,
    gas_pressed=gas,
    resume_pressed=resume,
    cancel_pressed=cancel,
    door_open=door,
    seatbelt_unlatched=seatbelt,
    cruise_available=available,
  )


def activate(controller):
  state = update(controller, brake=SOFT_HOLD_PRESS_THRESHOLD)
  assert state.active and not state.enable
  state = update(controller, brake=SOFT_HOLD_PRESS_THRESHOLD)
  assert state.active and state.enable
  return state


def test_requires_strong_press_at_standstill():
  controller = SoftHoldController(True)
  assert not update(controller, brake=SOFT_HOLD_PRESS_THRESHOLD - 1).active
  assert not update(controller, brake=SOFT_HOLD_PRESS_THRESHOLD + 20, standstill=False).active

  update(controller, brake=40)
  activate(controller)


def test_stays_active_after_brake_release():
  controller = SoftHoldController(True)
  activate(controller)
  assert update(controller, brake=0).active
  assert update(controller, brake=0).active


def test_second_strong_press_cancels():
  controller = SoftHoldController(True)
  activate(controller)
  update(controller, brake=0)
  state = update(controller, brake=SOFT_HOLD_PRESS_THRESHOLD + 10)
  assert not state.active
  assert state.cancel


def test_resume_or_gas_releases_without_cancel():
  for release in ({"resume": True}, {"gas": True}):
    controller = SoftHoldController(True)
    activate(controller)
    state = update(controller, brake=0, **release)
    assert not state.active
    assert not state.cancel


def test_invalid_vehicle_state_releases():
  invalid_states = (
    {"gear": GearShifter.park},
    {"door": True},
    {"seatbelt": True},
    {"available": False},
  )
  for invalid in invalid_states:
    controller = SoftHoldController(True)
    activate(controller)
    assert not update(controller, brake=0, **invalid).active


def test_disabled_controller_never_activates():
  controller = SoftHoldController(False)
  assert not update(controller, brake=100).active


def test_carstate_forwards_soft_hold_enable_pulse():
  car_state = CarState.__new__(CarState)
  car_state.soft_hold_button_enable = True
  assert car_state.update_button_enable([])
