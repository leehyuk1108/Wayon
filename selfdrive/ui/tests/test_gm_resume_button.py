import re
from pathlib import Path
from types import SimpleNamespace

import pyray as rl
import pytest

from cereal import car
from opendbc.car.gm.values import CAR
from openpilot.selfdrive.ui.mici.onroad.gm_resume_button import (
  GMResumeButton, REQUEST_QUEUED, REQUEST_UNAVAILABLE, RESUME_LABEL, RESUME_SERVICES, RESUME_SUBTITLE, show_manual_resume_button,
)
from openpilot.system.ui.lib.application import MouseEvent, MousePos, gui_app


class UIObservations(dict):
  fresh = True

  def all_checks(self, services):
    assert tuple(services) == RESUME_SERVICES
    return self.fresh


@pytest.fixture
def state():
  cp = car.CarParams.new_message(carFingerprint=CAR.CHEVROLET_TRAVERSE, brand="gm",
                                 autoResumeSng=True, openpilotLongitudinalControl=True)
  cs = car.CarState.new_message(canValid=True, standstill=True, gearShifter="drive")
  cs.cruiseState.enabled = True
  cs.cruiseState.standstill = True
  control = car.CarControl.new_message(longActive=True)
  control.actuators.longControlState = car.CarControl.Actuators.LongControlState.stopping
  sm = UIObservations(carState=cs, carControl=control, selfdriveState=SimpleNamespace(enabled=True),
                       longitudinalPlan=SimpleNamespace(shouldStop=False))
  return SimpleNamespace(started=True, CP=cp, sm=sm)


def test_test_button_does_not_require_a_lead(state):
  # No radar/lead service is provided; this is an explicit driver test.
  assert show_manual_resume_button(state)


@pytest.mark.parametrize("font", ["Pretendard-SemiBold", "unifont"])
def test_bitmap_fonts_cover_every_button_label(font):
  font_path = Path(__file__).parents[2] / "assets" / "fonts" / f"{font}.fnt"
  available = {int(codepoint) for codepoint in re.findall(r"char id=(\d+)", font_path.read_text())}
  labels = RESUME_LABEL + RESUME_SUBTITLE + REQUEST_QUEUED + REQUEST_UNAVAILABLE
  assert set(map(ord, labels)) <= available


@pytest.mark.parametrize("change", [
  lambda s: setattr(s, "started", False),
  lambda s: setattr(s.sm, "fresh", False),
  lambda s: setattr(s.CP, "autoResumeSng", False),
  lambda s: setattr(s.CP, "carFingerprint", "OTHER"),
  lambda s: setattr(s.sm["carState"], "vEgo", 0.06),
  lambda s: setattr(s.sm["carState"], "standstill", False),
  lambda s: setattr(s.sm["carState"], "brakePressed", True),
  lambda s: setattr(s.sm["carState"], "gasPressed", True),
  lambda s: setattr(s.sm["carState"], "parkingBrake", True),
  lambda s: setattr(s.sm["carState"].cruiseState, "standstill", False),
  lambda s: setattr(s.sm["selfdriveState"], "enabled", False),
  lambda s: setattr(s.sm["carControl"], "longActive", False),
  lambda s: setattr(s.sm["carControl"].actuators, "longControlState", "starting"),
  lambda s: setattr(s.sm["longitudinalPlan"], "shouldStop", True),
])
def test_button_hides_when_ineligible(state, change):
  change(state)
  assert not show_manual_resume_button(state)


@pytest.fixture
def touch_button(state, monkeypatch):
  now = [10.0]
  requests = []
  button = GMResumeButton(state=state, request=lambda: requests.append(now[0]) or True, clock=lambda: now[0])
  button.set_rect(rl.Rectangle(100, 80, 220, 76))

  def touch(pressed=False, released=False, down=False, pos=None):
    pos = MousePos(210, 115) if pos is None else pos
    event = MouseEvent(pos, 0, pressed, released, down, now[0])
    monkeypatch.setattr(gui_app, "_mouse_events", [event])
    button._update_state()
    if button.is_visible and button.enabled:
      button._process_mouse_events()
    now[0] += 0.01

  return button, touch, requests, now


def test_release_sends_once_and_holding_or_double_tapping_does_not_repeat(touch_button):
  button, touch, requests, now = touch_button
  touch(pressed=True, down=True)
  for _ in range(50):
    touch(down=True)
  assert requests == []
  touch(released=True)
  assert len(requests) == 1
  assert button._status == "요청 보냄"
  assert button.consumes_touch(MousePos(210, 115))
  touch(pressed=True, down=True)
  touch(released=True)
  assert len(requests) == 1
  now[0] += 3.0
  touch(pressed=True, down=True)
  touch(released=True)
  assert len(requests) == 2


def test_movement_between_press_and_release_cancels_touch(state, touch_button):
  button, touch, requests, _ = touch_button
  touch(pressed=True, down=True)
  state.sm["carState"].vEgo = 0.1
  touch(released=True)
  assert not button.is_visible
  assert requests == []
  state.sm["carState"].vEgo = 0.0
  touch(released=True)
  assert requests == []
  touch(pressed=True, down=True)
  touch(released=True)
  assert len(requests) == 1


def test_dragging_outside_is_not_a_request(touch_button):
  _, touch, requests, _ = touch_button
  touch(pressed=True, down=True)
  touch(down=True, pos=MousePos(20, 20))
  touch(released=True, pos=MousePos(20, 20))
  touch(released=True)
  assert requests == []


def test_unavailable_control_connection_does_not_claim_a_sent_request(touch_button):
  button, touch, requests, _ = touch_button
  button._request = lambda: False
  touch(pressed=True, down=True)
  touch(released=True)
  assert requests == []
  assert button._status == "제어 연결 대기"
