import hashlib
from pathlib import Path
import zipfile

from openpilot.common.basedir import BASEDIR


ROOT = Path(BASEDIR)
MODEL = ROOT / "selfdrive/lane_marking/models/lane.onnx"
VASM_MODEL = ROOT / "selfdrive/lane_marking/models/v_asm_model.onnx"
WHEEL = ROOT / "third_party/wheels/opencv_python_headless-4.13.0.92-cp37-abi3-manylinux_2_28_aarch64.whl"


def sha256(path: Path) -> str:
  digest = hashlib.sha256()
  with path.open("rb") as file:
    for chunk in iter(lambda: file.read(1024 * 1024), b""):
      digest.update(chunk)
  return digest.hexdigest()


def test_bundled_onnx_model_matches_reviewed_source():
  assert MODEL.stat().st_size == 13_194_895
  assert sha256(MODEL) == "d3761c185daf33897ff3ff5edf28115c5dc829c06c538033accb616d6c67528c"
  assert VASM_MODEL.stat().st_size == 9_625_905
  assert sha256(VASM_MODEL) == "00247ede5159dff9a0768c171095711d40f1ee109ac7b5e24adce344fe4ba6f9"


def test_bundled_opencv_wheel_is_valid_for_c4_arm64():
  assert WHEEL.stat().st_size == 35_010_236
  assert sha256(WHEEL) == "eb60e36b237b1ebd40a912da5384b348df8ed534f6f644d8e0b4f103e272ba7d"
  with zipfile.ZipFile(WHEEL) as wheel:
    names = wheel.namelist()
  assert any(name.endswith("cv2/cv2.abi3.so") for name in names)
  assert any(name.endswith("opencv_python_headless-4.13.0.92.dist-info/METADATA") for name in names)


def test_both_c3_launchers_bootstrap_onnx_before_manager():
  for launcher_path in (
      ROOT / "launch_chffrplus.sh",
      ROOT / "sunnypilot/system/hardware/c3/launch_chffrplus.sh",
  ):
    launcher = launcher_path.read_text()
    assert 'source "$DIR/selfdrive/lane_marking/onnx_env.sh"' in launcher
    assert launcher.index("bootstrap_lane_marking_onnx") < launcher.index("./manager.py")


def test_lane_marking_service_is_managed_independently_from_navdy():
  process_config = (ROOT / "system/manager/process_config.py").read_text()
  navdy_bridge = (ROOT / "selfdrive/navdy/navdy_op_bridge.py").read_text()

  assert 'PythonProcess("lane_markingd", "selfdrive.lane_markingd", always_run' in process_config
  assert "OnnxLaneMarkingClassifier" not in navdy_bridge
  assert "lane_marking_classifier.submit" not in navdy_bridge


def test_lane_worker_yields_to_driving_processes():
  launcher = (ROOT / "selfdrive/lane_markingd.py").read_text()
  server = (ROOT / "selfdrive/lane_marking/server.py").read_text()

  assert "os.nice(10)" in launcher
  assert "cv2.setNumThreads(2)" in server
  assert "LANE_INFERENCE_YIELD_SECONDS = 0.03" in server
  assert "time.sleep(LANE_INFERENCE_YIELD_SECONDS)" in server


def test_xiaoge_web_and_visual_bsd_are_wired_into_comma():
  server = (ROOT / "selfdrive/lane_marking/server.py").read_text()
  card = (ROOT / "selfdrive/car/card.py").read_text()
  web = (ROOT / "selfdrive/lane_marking/web.html").read_text()

  assert "PORT = 8082" in server
  assert "VISION_STREAM_WIDE_ROAD" in server
  assert 'BlindspotStateReader()' in card
  assert "merge_visual_blindspot" in card
  assert "V-ASM" in web
