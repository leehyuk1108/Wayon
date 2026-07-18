"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""

from cereal import car, custom, messaging

from openpilot.common.params import Params
from openpilot.common.realtime import DT_MDL
from openpilot.sunnypilot import PARAMS_UPDATE_PERIOD
from openpilot.sunnypilot.selfdrive.selfdrived.events import EventsSP

GREEN_LIGHT_X_THRESHOLD = 30
GREEN_LIGHT_ARM_SEC = 0.5
LEAD_DEPART_DIST_THRESHOLD = 1.0
LEAD_DEPART_MAX_JUMP = 6.0
LEAD_DEPART_MAX_DISTANCE = 40.0
LEAD_DEPART_MIN_SPEED = 0.5
LEAD_DEPART_ARM_SEC = 0.75
TRIGGER_TIMER_THRESHOLD = 0.3
NON_DRIVING_GEARS = (
  car.CarState.GearShifter.neutral,
  car.CarState.GearShifter.park,
  car.CarState.GearShifter.reverse,
  car.CarState.GearShifter.unknown,
)


class E2EStates:
  INACTIVE = 0
  ARMED = 1
  CONSUMED = 2


class E2EAlertsHelper:
  def __init__(self):
    self._params = Params()
    self.frame = -1
    self.green_light_state = E2EStates.INACTIVE
    self.prev_green_light_state = E2EStates.INACTIVE
    self.lead_depart_state = E2EStates.INACTIVE
    self.prev_lead_depart_state = E2EStates.INACTIVE

    self.green_light_alert = False
    self.green_light_alert_enabled = self._params.get_bool("GreenLightAlert")
    self.lead_depart_alert = False
    self.lead_depart_alert_enabled = self._params.get_bool("LeadDepartAlert")

    self.green_light_trigger_timer = 0
    self.green_light_arm_timer = 0
    self.green_light_armed = False
    self.lead_depart_trigger_timer = 0
    self.last_lead_distance = -1
    self.last_lead_track_id = -1

    self.allowed = False
    self.has_lead = False

    self.lead_depart_arm_timer = 0
    self.lead_depart_armed = False

  def _read_params(self) -> None:
    if self.frame % int(PARAMS_UPDATE_PERIOD / DT_MDL) == 0:
      self.green_light_alert_enabled = self._params.get_bool("GreenLightAlert")
      self.lead_depart_alert_enabled = self._params.get_bool("LeadDepartAlert")

  def update_alert_trigger(self, sm: messaging.SubMaster):
    CS = sm['carState']

    model_x = sm['modelV2'].position.x
    model_stopped = bool(model_x) and model_x[-1] <= GREEN_LIGHT_X_THRESHOLD
    lead = sm['radarState'].leadOne
    self.has_lead = lead.status
    lead_dRel = lead.dRel
    lead_vLead = lead.vLead
    lead_track_id = lead.radarTrackId

    standstill = CS.standstill
    driving_gear = CS.gearShifter not in NON_DRIVING_GEARS
    self.allowed = standstill and driving_gear and not CS.gasPressed

    # Green Light Alert
    green_light_trigger = False
    green_light_context = self.allowed and not self.has_lead
    if green_light_context:
      if model_stopped:
        self.green_light_arm_timer += 1
        self.green_light_armed = self.green_light_arm_timer * DT_MDL >= GREEN_LIGHT_ARM_SEC
        self.green_light_trigger_timer = 0
      elif self.green_light_state == E2EStates.ARMED and self.green_light_armed:
        self.green_light_trigger_timer += 1
      else:
        self.green_light_trigger_timer = 0

      if self.green_light_trigger_timer * DT_MDL > TRIGGER_TIMER_THRESHOLD:
        green_light_trigger = True
    else:
      self.green_light_arm_timer = 0
      self.green_light_armed = False
      self.green_light_trigger_timer = 0

    # Lead Departure Alert
    close_lead_valid = self.has_lead and 0.0 < lead_dRel < LEAD_DEPART_MAX_DISTANCE
    if self.allowed and close_lead_valid:
      if self.last_lead_distance < 0.0 or self.last_lead_track_id != lead_track_id:
        self.last_lead_track_id = lead_track_id
        self.last_lead_distance = lead_dRel
        self.lead_depart_arm_timer = 0
        self.lead_depart_armed = False
      else:
        self.lead_depart_arm_timer += 1
        self.last_lead_distance = min(self.last_lead_distance, lead_dRel)
        if self.lead_depart_arm_timer * DT_MDL >= LEAD_DEPART_ARM_SEC:
          self.lead_depart_armed = True
    else:
      self.lead_depart_arm_timer = 0
      self.lead_depart_armed = False
      self.last_lead_distance = -1
      self.last_lead_track_id = -1

    lead_depart_trigger = False
    if self.lead_depart_state == E2EStates.ARMED and self.lead_depart_armed:
      distance_delta = lead_dRel - self.last_lead_distance
      lead_moving = lead_vLead >= LEAD_DEPART_MIN_SPEED
      plausible_delta = LEAD_DEPART_DIST_THRESHOLD < distance_delta < LEAD_DEPART_MAX_JUMP
      if lead_moving and plausible_delta:
        self.lead_depart_trigger_timer += 1
      else:
        self.lead_depart_trigger_timer = 0

      if self.lead_depart_trigger_timer * DT_MDL > TRIGGER_TIMER_THRESHOLD:
        lead_depart_trigger = True
    else:
      self.lead_depart_trigger_timer = 0

    return green_light_trigger, lead_depart_trigger

  @staticmethod
  def update_state_machine(state: int, enabled: bool, allowed: bool, triggered: bool) -> tuple[int, bool]:
    alert = False
    if state != E2EStates.INACTIVE:
      if not allowed or not enabled:
        state = E2EStates.INACTIVE

      else:
        if state == E2EStates.ARMED:
          if triggered:
            state = E2EStates.CONSUMED
            alert = True

        elif state == E2EStates.CONSUMED:
          pass

    elif state == E2EStates.INACTIVE:
      if allowed and enabled:
        state = E2EStates.ARMED

    return state, alert

  def update(self, sm: messaging.SubMaster, events_sp: EventsSP) -> None:
    self._read_params()

    green_light_trigger, lead_depart_trigger = self.update_alert_trigger(sm)

    self.prev_green_light_state = self.green_light_state
    self.prev_lead_depart_state = self.lead_depart_state

    self.green_light_state, self.green_light_alert = self.update_state_machine(
      self.green_light_state,
      self.green_light_alert_enabled,
      self.allowed and not self.has_lead and self.green_light_armed,
      green_light_trigger
    )

    self.lead_depart_state, self.lead_depart_alert = self.update_state_machine(
      self.lead_depart_state,
      self.lead_depart_alert_enabled,
      self.allowed and self.lead_depart_armed,
      lead_depart_trigger
    )

    if self.green_light_alert or self.lead_depart_alert:
      events_sp.add(custom.OnroadEventSP.EventName.e2eChime)

    self.frame += 1
