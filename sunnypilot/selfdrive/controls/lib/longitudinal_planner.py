"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""

import math

from cereal import messaging, custom
from opendbc.car import structs
from openpilot.common.constants import CV
from openpilot.selfdrive.car.cruise import V_CRUISE_MAX
from openpilot.sunnypilot.selfdrive.controls.lib.dec.dec import DynamicExperimentalController
from openpilot.sunnypilot.selfdrive.controls.lib.e2e_alerts_helper import E2EAlertsHelper
from openpilot.sunnypilot.selfdrive.controls.lib.smart_cruise_control.smart_cruise_control import SmartCruiseControl
from openpilot.sunnypilot.selfdrive.controls.lib.speed_limit.speed_limit_assist import SpeedLimitAssist
from openpilot.sunnypilot.selfdrive.controls.lib.speed_limit.speed_limit_resolver import SpeedLimitResolver
from openpilot.sunnypilot.selfdrive.selfdrived.events import EventsSP
from openpilot.sunnypilot.models.helpers import get_active_bundle
from openpilot.sunnypilot.selfdrive.controls.lib.wayon_carrot_long_profile import is_enabled

DecState = custom.LongitudinalPlanSP.DynamicExperimentalControl.DynamicExperimentalControlState
LongitudinalPlanSource = custom.LongitudinalPlanSP.LongitudinalPlanSource

ICBM_MIN_TARGET_KPH = 20.0
ICBM_COAST_ENTRY_MARGIN_KPH = 3.0
ICBM_TRACKING_DEADBAND_KPH = 0.5
ICBM_TRACKING_DECEL_MIN_MPS2 = 0.12
ICBM_TRACKING_DECEL_GAIN_MPS2_PER_KPH = 0.10
ICBM_TRACKING_DECEL_MAX_MPS2 = 0.45


def apply_icbm_target(icbm: custom.IntelligentCruiseButtonManagement, v_cruise: float) -> float:
  """Apply the existing ICBM camera/section target as an OP-long cruise ceiling."""
  target_kph = float(icbm.automaticTargetSpeedKph)
  if not icbm.automaticControlActive or not math.isfinite(target_kph):
    return v_cruise
  if not ICBM_MIN_TARGET_KPH <= target_kph <= V_CRUISE_MAX:
    return v_cruise
  return min(v_cruise, target_kph * CV.KPH_TO_MS)


def apply_icbm_accel_target(icbm: custom.IntelligentCruiseButtonManagement, v_ego: float,
                            a_target: float, v_cruise: float) -> float:
  """Release propulsion early and gently catch up when the vehicle trails a falling ICBM ceiling."""
  target_kph = float(icbm.automaticTargetSpeedKph)
  if not icbm.automaticControlActive or not math.isfinite(target_kph):
    return a_target
  if not ICBM_MIN_TARGET_KPH <= target_kph <= V_CRUISE_MAX:
    return a_target

  target_ms = target_kph * CV.KPH_TO_MS
  if target_ms >= v_cruise or target_ms > v_ego + ICBM_COAST_ENTRY_MARGIN_KPH * CV.KPH_TO_MS:
    return a_target

  speed_error_kph = (v_ego - target_ms) * CV.MS_TO_KPH
  control_source = str(getattr(icbm, "controlSource", ""))
  required_accel = float(getattr(icbm, "requiredAccel", 0.0))
  if control_source != "camera" or speed_error_kph <= ICBM_TRACKING_DEADBAND_KPH:
    # On GM SDGM, zero acceleration maps to zero gas and zero friction brake.
    return min(a_target, required_accel if required_accel < -0.08 else 0.0)

  # The camera profile is intentionally shallow.  Add only enough feedback to
  # prevent MPC/actuator lag from accumulating as the ceiling falls, while
  # keeping early camera approaches in a coast-first regime.
  tracking_decel = ICBM_TRACKING_DECEL_MIN_MPS2 + (
    speed_error_kph - ICBM_TRACKING_DEADBAND_KPH
  ) * ICBM_TRACKING_DECEL_GAIN_MPS2_PER_KPH
  tracking_decel = min(ICBM_TRACKING_DECEL_MAX_MPS2, tracking_decel)
  predicted_decel = required_accel if math.isfinite(required_accel) and required_accel < -0.08 else 0.0
  return min(a_target, -tracking_decel, predicted_decel)


class LongitudinalPlannerSP:
  def __init__(self, CP: structs.CarParams, CP_SP: structs.CarParamsSP, mpc):
    self.events_sp = EventsSP()
    self.resolver = SpeedLimitResolver()
    self.dec = DynamicExperimentalController(CP, mpc)
    self.scc = SmartCruiseControl(is_enabled(CP))
    self.resolver = SpeedLimitResolver()
    self.sla = SpeedLimitAssist(CP, CP_SP)
    self.generation = int(model_bundle.generation) if (model_bundle := get_active_bundle()) else None
    self.source = LongitudinalPlanSource.cruise
    self.e2e_alerts_helper = E2EAlertsHelper()

    self.output_v_target = 0.
    self.output_a_target = 0.
    self.traffic_stop_active = False
    self.traffic_stop_state = 0
    self.traffic_stop_signal = 0
    self.traffic_stop_distance = 1000.0
    self.traffic_stop_model_distance = 1000.0

  def is_e2e(self, sm: messaging.SubMaster) -> bool:
    experimental_mode = sm['selfdriveState'].experimentalMode
    if not self.dec.active():
      return experimental_mode

    return experimental_mode and self.dec.mode() == "blended"

  def update_targets(self, sm: messaging.SubMaster, v_ego: float, a_ego: float, v_cruise: float) -> tuple[float, float]:
    CS = sm['carState']
    v_cruise_cluster_kph = min(CS.vCruiseCluster, V_CRUISE_MAX)
    v_cruise_cluster = v_cruise_cluster_kph * CV.KPH_TO_MS

    long_enabled = sm['carControl'].enabled
    long_override = sm['carControl'].cruiseControl.override

    # Smart Cruise Control
    self.scc.update(sm, long_enabled, long_override, v_ego, a_ego, v_cruise)

    # Speed Limit Resolver
    self.resolver.update(v_ego, sm)

    # Speed Limit Assist
    has_speed_limit = self.resolver.speed_limit_valid or self.resolver.speed_limit_last_valid
    self.sla.update(long_enabled, long_override, v_ego, a_ego, v_cruise_cluster, self.resolver.speed_limit,
                    self.resolver.speed_limit_final_last, has_speed_limit, self.resolver.distance, self.events_sp)

    # ICBM continues to own the proven Navdy camera and section-control state
    # machine. Under OP long its target caps cruise directly instead of sending
    # synthetic stock ACC button presses.
    icbm = sm['selfdriveStateSP'].intelligentCruiseButtonManagement
    icbm_v_cruise = apply_icbm_target(icbm, v_cruise)
    icbm_a_target = apply_icbm_accel_target(icbm, v_ego, a_ego, v_cruise)

    targets = {
      LongitudinalPlanSource.cruise: (icbm_v_cruise, icbm_a_target),
      LongitudinalPlanSource.sccVision: (self.scc.vision.output_v_target, self.scc.vision.output_a_target),
      LongitudinalPlanSource.sccMap: (self.scc.map.output_v_target, self.scc.map.output_a_target),
      LongitudinalPlanSource.speedLimitAssist: (self.sla.output_v_target, self.sla.output_a_target),
    }

    self.source = min(targets, key=lambda k: targets[k][0])
    self.output_v_target, self.output_a_target = targets[self.source]
    return self.output_v_target, self.output_a_target

  def update(self, sm: messaging.SubMaster) -> None:
    self.events_sp.clear()
    self.dec.update(sm)
    self.e2e_alerts_helper.update(sm, self.events_sp)

  def publish_longitudinal_plan_sp(self, sm: messaging.SubMaster, pm: messaging.PubMaster) -> None:
    plan_sp_send = messaging.new_message('longitudinalPlanSP')

    plan_sp_send.valid = sm.all_checks(service_list=['carState', 'controlsState'])

    longitudinalPlanSP = plan_sp_send.longitudinalPlanSP
    longitudinalPlanSP.longitudinalPlanSource = self.source
    longitudinalPlanSP.vTarget = float(self.output_v_target)
    longitudinalPlanSP.aTarget = float(self.output_a_target)
    longitudinalPlanSP.events = self.events_sp.to_msg()

    # Dynamic Experimental Control
    dec = longitudinalPlanSP.dec
    dec.state = DecState.blended if self.dec.mode() == 'blended' else DecState.acc
    dec.enabled = self.dec.enabled()
    dec.active = self.dec.active()

    # Smart Cruise Control
    smartCruiseControl = longitudinalPlanSP.smartCruiseControl
    # Vision Control
    sccVision = smartCruiseControl.vision
    sccVision.state = self.scc.vision.state
    sccVision.vTarget = float(self.scc.vision.output_v_target)
    sccVision.aTarget = float(self.scc.vision.output_a_target)
    sccVision.currentLateralAccel = float(self.scc.vision.current_lat_acc)
    sccVision.maxPredictedLateralAccel = float(self.scc.vision.max_pred_lat_acc)
    sccVision.enabled = self.scc.vision.is_enabled
    sccVision.active = self.scc.vision.is_active
    # Map Control
    sccMap = smartCruiseControl.map
    sccMap.state = self.scc.map.state
    sccMap.vTarget = float(self.scc.map.output_v_target)
    sccMap.aTarget = float(self.scc.map.output_a_target)
    sccMap.enabled = self.scc.map.is_enabled
    sccMap.active = self.scc.map.is_active

    # Speed Limit
    speedLimit = longitudinalPlanSP.speedLimit
    resolver = speedLimit.resolver
    resolver.speedLimit = float(self.resolver.speed_limit)
    resolver.speedLimitLast = float(self.resolver.speed_limit_last)
    resolver.speedLimitFinal = float(self.resolver.speed_limit_final)
    resolver.speedLimitFinalLast = float(self.resolver.speed_limit_final_last)
    resolver.speedLimitValid = self.resolver.speed_limit_valid
    resolver.speedLimitLastValid = self.resolver.speed_limit_last_valid
    resolver.speedLimitOffset = float(self.resolver.speed_limit_offset)
    resolver.distToSpeedLimit = float(self.resolver.distance)
    resolver.source = self.resolver.source
    assist = speedLimit.assist
    assist.state = self.sla.state
    assist.enabled = self.sla.is_enabled
    assist.active = self.sla.is_active
    assist.vTarget = float(self.sla.output_v_target)
    assist.aTarget = float(self.sla.output_a_target)

    # E2E Alerts
    e2eAlerts = longitudinalPlanSP.e2eAlerts
    e2eAlerts.greenLightAlert = self.e2e_alerts_helper.green_light_alert
    e2eAlerts.leadDepartAlert = self.e2e_alerts_helper.lead_depart_alert

    trafficStop = longitudinalPlanSP.trafficStop
    trafficStop.active = bool(self.traffic_stop_active)
    trafficStop.state = ("inactive", "stopping", "stopped")[int(self.traffic_stop_state)]
    trafficStop.signal = ("off", "red", "green")[int(self.traffic_stop_signal)]
    trafficStop.stopDistance = float(self.traffic_stop_distance)
    trafficStop.modelDistance = float(self.traffic_stop_model_distance)

    pm.send('longitudinalPlanSP', plan_sp_send)
