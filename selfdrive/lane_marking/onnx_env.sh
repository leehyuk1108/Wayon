#!/usr/bin/env bash

LANE_MARKING_ONNX_OPENCV_VERSION="4.13.0.92"
LANE_MARKING_ONNX_WHEEL="opencv_python_headless-${LANE_MARKING_ONNX_OPENCV_VERSION}-cp37-abi3-manylinux_2_28_aarch64.whl"

function bootstrap_lane_marking_onnx {
  local pydeps_dir="$DIR/pydeps"
  local wheel_path="$DIR/third_party/wheels/$LANE_MARKING_ONNX_WHEEL"
  export PYTHONPATH="$pydeps_dir:$DIR${PYTHONPATH:+:$PYTHONPATH}"

  if python3 -c "import cv2; assert cv2.__version__ == '4.13.0'; assert hasattr(cv2.dnn, 'readNetFromONNX')" >/dev/null 2>&1; then
    return 0
  fi
  if [ ! -f "$wheel_path" ]; then
    echo "Lane marking ONNX disabled: missing $wheel_path"
    return 1
  fi

  mkdir -p "$pydeps_dir"
  if ! python3 -m pip install --no-index --no-deps --upgrade \
      --target "$pydeps_dir" "$wheel_path"; then
    echo "Lane marking ONNX disabled: bundled OpenCV installation failed"
    return 1
  fi
  python3 -c "import cv2; assert cv2.__version__ == '4.13.0'; assert hasattr(cv2.dnn, 'readNetFromONNX')"
}
