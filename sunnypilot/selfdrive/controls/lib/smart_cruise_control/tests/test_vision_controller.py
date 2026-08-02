"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""
import numpy as np

import cereal.messaging as messaging
from cereal import custom, log
from openpilot.common.params import Params
from openpilot.common.realtime import DT_MDL
from openpilot.selfdrive.car.cruise import V_CRUISE_UNSET
from openpilot.selfdrive.modeld.constants import ModelConstants
from openpilot.sunnypilot.selfdrive.controls.lib.smart_cruise_control.vision_controller import (
  SmartCruiseControlVision,
  _CURVE_CONFIRM_TIME,
)

VisionState = custom.LongitudinalPlanSP.SmartCruiseControl.VisionState


def generate_modelV2():
  model = messaging.new_message('modelV2')
  position = log.XYZTData.new_message()
  speed = 30
  position.x = [float(x) for x in (speed + 0.5) * np.array(ModelConstants.T_IDXS)]
  model.modelV2.position = position
  orientation = log.XYZTData.new_message()
  curvature = 0.05
  orientation.x = [float(curvature) for _ in ModelConstants.T_IDXS]
  orientation.y = [0.0 for _ in ModelConstants.T_IDXS]
  model.modelV2.orientation = orientation
  orientationRate = log.XYZTData.new_message()
  orientationRate.z = [0.0 for _ in ModelConstants.T_IDXS]
  model.modelV2.orientationRate = orientationRate
  velocity = log.XYZTData.new_message()
  velocity.x = [float(x) for x in (speed + 0.5) * np.ones_like(ModelConstants.T_IDXS)]
  velocity.x[0] = float(speed)  # always start at current speed
  model.modelV2.velocity = velocity
  acceleration = log.XYZTData.new_message()
  acceleration.x = [float(x) for x in np.zeros_like(ModelConstants.T_IDXS)]
  acceleration.y = [float(y) for y in np.zeros_like(ModelConstants.T_IDXS)]
  model.modelV2.acceleration = acceleration

  return model


def set_curve(model, curvature: float, start_idx: int, end_idx: int | None = None):
  end_idx = len(model.modelV2.velocity.x) if end_idx is None else end_idx
  yaw_rate = np.zeros(len(model.modelV2.velocity.x))
  velocity = np.asarray(model.modelV2.velocity.x)
  yaw_rate[start_idx:end_idx] = curvature * velocity[start_idx:end_idx]
  model.modelV2.orientationRate.z = [float(rate) for rate in yaw_rate]


def generate_carState():
  car_state = messaging.new_message('carState')
  speed = 30
  v_cruise = 50
  car_state.carState.vEgo = float(speed)
  car_state.carState.standstill = False
  car_state.carState.vCruise = float(v_cruise * 3.6)

  return car_state


def generate_controlsState():
  controls_state = messaging.new_message('controlsState')
  controls_state.controlsState.curvature = 0.05

  return controls_state


class TestSmartCruiseControlVision:

  def setup_method(self):
    self.params = Params()
    self.reset_params()
    self.scc_v = SmartCruiseControlVision()

    mdl = generate_modelV2()
    cs = generate_carState()
    controls_state = generate_controlsState()
    self.sm = {'modelV2': mdl.modelV2, 'carState': cs.carState, 'controlsState': controls_state.controlsState}

  def reset_params(self):
    self.params.put_bool("SmartCruiseControlVision", True, block=True)

  def test_initial_state(self):
    assert self.scc_v.state == VisionState.disabled
    assert not self.scc_v.is_active
    assert self.scc_v.output_v_target == V_CRUISE_UNSET
    assert self.scc_v.output_a_target == 0.

  def test_system_disabled(self):
    self.params.put_bool("SmartCruiseControlVision", False, block=True)
    self.scc_v.enabled = self.params.get_bool("SmartCruiseControlVision")

    for _ in range(int(10. / DT_MDL)):
      self.scc_v.update(self.sm, True, False, 0., 0., 0.)
    assert self.scc_v.state == VisionState.disabled
    assert not self.scc_v.is_active

  def test_disabled(self):
    for _ in range(int(10. / DT_MDL)):
      self.scc_v.update(self.sm, False, False, 0., 0., 0.)
    assert self.scc_v.state == VisionState.disabled

  def test_transition_disabled_to_enabled(self):
    for _ in range(int(10. / DT_MDL)):
      self.scc_v.update(self.sm, True, False, 0., 0., 0.)
    assert self.scc_v.state == VisionState.enabled

  def test_single_point_curve_spike_is_filtered(self):
    mdl = generate_modelV2()
    set_curve(mdl, curvature=0.02, start_idx=12, end_idx=13)
    self.sm["modelV2"] = mdl.modelV2

    for _ in range(int(1. / DT_MDL)):
      self.scc_v.update(self.sm, True, False, 30., 0.0, 40.)

    assert self.scc_v.max_pred_lat_acc == 0.
    assert self.scc_v.state == VisionState.enabled

  def test_persistent_curve_requires_temporal_confirmation(self):
    mdl = generate_modelV2()
    set_curve(mdl, curvature=0.005, start_idx=8, end_idx=18)
    self.sm["modelV2"] = mdl.modelV2

    confirm_frames = int(_CURVE_CONFIRM_TIME / DT_MDL)
    for _ in range(confirm_frames - 1):
      self.scc_v.update(self.sm, True, False, 30., 0.0, 40.)
      assert self.scc_v.state != VisionState.entering

    self.scc_v.update(self.sm, True, False, 30., 0.0, 40.)
    assert self.scc_v.state == VisionState.entering
    assert self.scc_v.output_v_target < 40.

  def test_far_curve_allows_more_speed_than_near_curve(self):
    near = generate_modelV2()
    far = generate_modelV2()
    positions = np.linspace(0., 160., len(ModelConstants.T_IDXS))
    near.modelV2.position.x = [float(x) for x in positions]
    far.modelV2.position.x = [float(x) for x in positions]
    set_curve(near, curvature=0.006, start_idx=4, end_idx=18)
    set_curve(far, curvature=0.006, start_idx=20)

    self.scc_v.v_ego = 30.
    self.sm["modelV2"] = near.modelV2
    near_target, _ = self.scc_v._distance_speed_profile(self.sm)
    self.sm["modelV2"] = far.modelV2
    far_target, _ = self.scc_v._distance_speed_profile(self.sm)

    assert far_target > near_target

  def test_curve_target_recovers_more_slowly_than_it_decreases(self):
    curve = generate_modelV2()
    set_curve(curve, curvature=0.006, start_idx=5, end_idx=20)
    self.sm["modelV2"] = curve.modelV2
    self.scc_v.update(self.sm, True, False, 30., 0.0, 40.)
    initial = self.scc_v.v_target

    self.scc_v.v_target = 40.
    self.scc_v._filter_target(initial)
    decrease = 40. - self.scc_v.v_target

    self.scc_v.v_target = initial
    self.scc_v._filter_target(40.)
    increase = self.scc_v.v_target - initial

    assert decrease > increase

  # TODO-SP: mock modelV2 data to test other states
