# Xiaoge Vision on Wayon

`lane_markingd` is a comma-side service that runs both Xiaoge ONNX models and
serves the diagnostic/configuration page on port 8082.

- `lane.onnx` classifies the nearest left/right road markings.
- `v_asm_model.onnx` evaluates the selected polygon on the wide road camera.
- Lane changes are permitted only for a confirmed dashed boundary.
- Fresh V-ASM detections are OR-merged into OEM `leftBlindspot` and
  `rightBlindspot`; they can never clear an OEM warning.
- V-ASM runs at 30-120 km/h, only for the requested lane-change side, and only
  when the computed target-lane width is at least 3.0 m.
- Lane state expires after 1.25 seconds and V-ASM state after 1.5 seconds.

Open `http://<comma-ip>:8082/` to view camera snapshots, model status,
confidence and latency, edit left/right wide-camera polygons, and adjust
threshold, smoothing, and inference intervals. Polygon overrides are stored in
the ignored local file `v_asm_config.json`.

Navdy does not run either model. It only reads the comma-produced lane and
blindspot values for display.
