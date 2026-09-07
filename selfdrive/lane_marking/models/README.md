# Comma ONNX lane-marking model

`lane.onnx` classifies the nearest left and right road markings as solid or
dashed. It was imported from jixiexiaoge's CarrotPilot work at commit
`7051df704ccdc9be47a173e062c3abba5fc8c01f`.

- SHA-256: `d3761c185daf33897ff3ff5edf28115c5dc829c06c538033accb616d6c67528c`
- Size: `13,194,895` bytes
- Input: normalized `1x3x416x416` grayscale NCHW
- Outputs: YOLOv8-Seg `output0` and `output1`

The model runs on comma and its result feeds lane-change safety directly.
Navdy is only an optional display consumer. Yellow/center-line semantics are
intentionally not consumed yet. Lane geometry and the steering path continue
to come from openpilot `modelV2`.

`v_asm_model.onnx` is the second Xiaoge Vision model. It evaluates the selected
left or right polygon on the wide road camera and OR-merges detections with the
vehicle OEM blindspot state.

- SHA-256: `00247ede5159dff9a0768c171095711d40f1ee109ac7b5e24adce344fe4ba6f9`
- Size: `9,625,905` bytes
