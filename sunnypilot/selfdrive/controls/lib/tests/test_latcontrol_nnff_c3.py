import math
import os

import numpy as np

from cereal import car, log, messaging
from opendbc.car.car_helpers import interfaces
from opendbc.car.gm.values import CAR as GM
from opendbc.car.vehicle_model import VehicleModel
from openpilot.common.mock.generators import generate_livePose
from openpilot.common.params import Params
from openpilot.common.realtime import DT_CTRL
from openpilot.selfdrive.car.helpers import convert_to_capnp
from openpilot.selfdrive.locationd.helpers import Pose
from openpilot.selfdrive.modeld.constants import ModelConstants
from openpilot.sunnypilot.selfdrive.car import interfaces as sunnypilot_interfaces
from openpilot.sunnypilot.selfdrive.controls.controlsd_ext import ControlsExt
from openpilot.sunnypilot.selfdrive.controls.lib.latcontrol_nnff_c3 import (
  KI,
  KP,
  VERSION,
  LatControlNNFFC3,
)
from openpilot.sunnypilot.selfdrive.controls.lib.latcontrol_torque_v0 import (
  LatControlTorque,
)


def generate_model_v2():
  model = messaging.new_message('modelV2')
  orientation = log.XYZTData.new_message()
  orientation.x = [0.0 for _ in ModelConstants.T_IDXS]
  orientation.y = [0.0 for _ in ModelConstants.T_IDXS]
  model.modelV2.orientation = orientation
  acceleration = log.XYZTData.new_message()
  acceleration.y = [0.0 for _ in ModelConstants.T_IDXS]
  model.modelV2.acceleration = acceleration
  return model.modelV2


def build_traverse(params):
  CarInterface = interfaces[GM.CHEVROLET_TRAVERSE]
  CP = CarInterface.get_non_essential_params(GM.CHEVROLET_TRAVERSE)
  CP_SP = CarInterface.get_non_essential_params_sp(
    CP, GM.CHEVROLET_TRAVERSE)
  CI = CarInterface(CP, CP_SP)
  sunnypilot_interfaces.setup_interfaces(CI, params)
  return CP.as_reader(), convert_to_capnp(CP_SP).as_reader(), CI


def test_c3_nnff_uses_original_model_pid_and_limits():
  params = Params()
  params.put_bool("NeuralNetworkLateralControl", True, block=True)
  try:
    CP, CP_SP, CI = build_traverse(params)
    controller = LatControlNNFFC3(CP, CP_SP, CI, DT_CTRL)

    assert controller.nnff_loaded
    assert os.path.basename(controller.model_path) == "CHEVROLET_TRAILBLAZER.json"
    assert math.isclose(controller.pid.k_p, KP)
    assert math.isclose(controller.pid.k_i, KI)
    assert math.isclose(controller.pid.pos_limit, 1.0)
    assert math.isclose(controller.pid.neg_limit, -1.0)
  finally:
    params.remove("NeuralNetworkLateralControl")


def test_traverse_nnlc_toggle_selects_c3_nnff_controller():
  params = Params()
  params.put_bool("NeuralNetworkLateralControl", True, block=True)
  try:
    CP, CP_SP, CI = build_traverse(params)
    controls_ext = object.__new__(ControlsExt)
    controls_ext.params = params
    controls_ext.CP = CP
    controls_ext.CP_SP = CP_SP
    stock_controller = LatControlTorque(CP, CP_SP, CI, DT_CTRL)

    selected = controls_ext.initialize_lateral_control(
      stock_controller, CI, DT_CTRL)

    assert isinstance(selected, LatControlNNFFC3)
  finally:
    params.remove("NeuralNetworkLateralControl")


def test_c3_nnff_runs_one_bounded_pid_update():
  params_store = Params()
  params_store.put_bool("NeuralNetworkLateralControl", True, block=True)
  try:
    CP, CP_SP, CI = build_traverse(params_store)
    controller = LatControlNNFFC3(CP, CP_SP, CI, DT_CTRL)
    controller.extension.update_model_v2(generate_model_v2())
    controller.extension.update_lateral_lag(0.2)
    nn_future_times = controller.nn_future_times.copy()

    CS = car.CarState.new_message()
    CS.vEgo = 15.0
    CS.aEgo = 0.0
    CS.steeringPressed = False
    live_params = log.LiveParametersData.new_message()
    pose = Pose.from_live_pose(generate_livePose().livePose)
    VM = VehicleModel(CP)

    steer, _, lac_log = controller.update(
      True, CS, VM, live_params, False, 1e-4, pose, False, 0.25)

    assert lac_log.version == VERSION
    assert math.isfinite(steer)
    assert abs(steer) <= 1.0
    assert math.isclose(lac_log.p, lac_log.error * KP, rel_tol=1e-5)
    assert math.isclose(
      lac_log.i, lac_log.error * KI * DT_CTRL, rel_tol=1e-5, abs_tol=1e-8)
    assert np.isclose(lac_log.output, steer)
    assert controller.nn_future_times == nn_future_times
  finally:
    params_store.remove("NeuralNetworkLateralControl")
