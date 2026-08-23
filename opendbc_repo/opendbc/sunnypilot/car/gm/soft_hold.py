"""Traverse soft hold state machine driven by the GM brake pedal position."""

from dataclasses import dataclass

from opendbc.car import structs


GearShifter = structs.CarState.GearShifter

SOFT_HOLD_PRESS_THRESHOLD = 100
SOFT_HOLD_RELEASE_THRESHOLD = 45
ENABLE_DELAY_FRAMES = 2


@dataclass(frozen=True)
class SoftHoldState:
  active: bool = False
  enable: bool = False
  cancel: bool = False


class SoftHoldController:
  def __init__(self, enabled: bool):
    self.enabled = enabled
    self.active = False
    self.strong_press_latched = False
    self.enable_delay = 0

  def reset(self) -> None:
    self.active = False
    self.strong_press_latched = False
    self.enable_delay = 0

  def update(self, *, brake_pedal_position: float, standstill: bool, gear_shifter,
             gas_pressed: bool, resume_pressed: bool, cancel_pressed: bool,
             door_open: bool, seatbelt_unlatched: bool, cruise_available: bool) -> SoftHoldState:
    if not self.enabled:
      return SoftHoldState()

    if brake_pedal_position <= SOFT_HOLD_RELEASE_THRESHOLD:
      self.strong_press_latched = False

    release_requested = gas_pressed or resume_pressed
    invalid_state = (gear_shifter != GearShifter.drive or door_open or
                     seatbelt_unlatched or not cruise_available)
    if release_requested or cancel_pressed or invalid_state:
      self.active = False
      self.enable_delay = 0
      return SoftHoldState()

    strong_press = brake_pedal_position >= SOFT_HOLD_PRESS_THRESHOLD
    new_strong_press = strong_press and not self.strong_press_latched
    if new_strong_press:
      self.strong_press_latched = True
      if self.active:
        self.active = False
        self.enable_delay = 0
        return SoftHoldState(cancel=True)
      if standstill:
        self.active = True
        # Wait until after the brake rising-edge event before requesting pre-enable.
        self.enable_delay = ENABLE_DELAY_FRAMES

    enable = False
    if self.active and self.enable_delay > 0:
      self.enable_delay -= 1
      enable = self.enable_delay == 0

    return SoftHoldState(active=self.active, enable=enable)
