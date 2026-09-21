import time

from openpilot.common.swaglog import cloudlog


class LaneChangeInputMonitor:
  def __init__(self):
    self.last_car_signal = 0
    self.last_navdy_signal = 0

  @staticmethod
  def signal(left, right):
    return 1 if left and not right else 2 if right and not left else 0

  def update(self, sm, desire_helper):
    car_state = sm['carState']
    navdy_state = sm['carStateSP']
    car_signal = self.signal(car_state.leftBlinker, car_state.rightBlinker)
    navdy_signal = self.signal(navdy_state.navdyLeftBlinker, navdy_state.navdyRightBlinker)

    for source, signal, previous in (('carStateSP', navdy_signal, self.last_navdy_signal),
                                     ('carState', car_signal, self.last_car_signal)):
      if signal and signal != previous:
        cloudlog.event('lane_change_input_seen', source=source, direction=signal,
                       car_signal=car_signal, navdy_signal=navdy_signal,
                       car_state_time=sm.logMonoTime['carState'], navdy_state_time=sm.logMonoTime['carStateSP'],
                       car_control_time=sm.logMonoTime['carControl'], observed_time=time.monotonic_ns(),
                       speed=float(car_state.vEgo), lateral_active=bool(sm['carControl'].latActive),
                       setting=int(desire_helper.alc.lane_change_set_timer),
                       lane_change_state=int(desire_helper.lane_change_state))

    self.last_car_signal = car_signal
    self.last_navdy_signal = navdy_signal
