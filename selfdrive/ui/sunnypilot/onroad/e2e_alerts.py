import time
from dataclasses import dataclass


E2E_ALERT_HOLD_SEC = 3.0


@dataclass(frozen=True)
class E2EAlert:
  name: str
  text1: str
  text2: str


GREEN_LIGHT_ALERT = E2EAlert(
  name="greenLight",
  text1="신호 변경됨",
  text2="전방 신호 변경 감지됨",
)

LEAD_DEPART_ALERT = E2EAlert(
  name="leadDeparting",
  text1="전방 차량 출발",
  text2="전방 차량이 출발했습니다",
)


class E2EAlertController:
  def __init__(self, hold_sec: float = E2E_ALERT_HOLD_SEC):
    self._hold_sec = hold_sec
    self.reset()

  def reset(self) -> None:
    self._active_alert: E2EAlert | None = None
    self._active_until = 0.0

  def update(self, green_light: bool, lead_depart: bool, now: float | None = None,
             allowed: bool = True) -> E2EAlert | None:
    now = time.monotonic() if now is None else now

    if not allowed:
      self.reset()
      return None

    alert = GREEN_LIGHT_ALERT if green_light else LEAD_DEPART_ALERT if lead_depart else None
    if alert is not None:
      self._active_alert = alert
      self._active_until = now + self._hold_sec

    if self._active_alert is None or now >= self._active_until:
      self.reset()
      return None

    return self._active_alert
