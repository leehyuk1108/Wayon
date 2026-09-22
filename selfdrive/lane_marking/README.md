# ONNX vision trial

The lane and V-ASM ONNX models and inference logic are ported from
[`carrotpilot` `wip` at `9cc61ad`](https://github.com/leehyuk1108/carrotpilot/tree/9cc61ad4083746143aedcc00ee12a49ea7e987bd/openpilot/selfdrive/carrot/xiaoge).
Both models run through OpenCV DNN on the CPU, not the Qualcomm DSP.

On the four-core comma device, synthetic offroad inference measured about
0.95-0.98 CPU seconds per lane sample and 0.36-0.38 CPU seconds per V-ASM
sample after warmup. `lane_onnx_shadow` runs onroad at low priority with a
shared 20% one-core budget and skips inference when reported load or
temperature is high. It writes observations to `/dev/shm/wayon_onnx_vision.json`.

The Navdy bridge reads fresh ONNX lane classifications and does not start the
previous image-based solid/dashed/yellow classifier. ONNX does not identify
yellow centerlines; unknown or stale lane classifications block lane changes.
V-ASM observations are recorded only and are not connected to `carState` or
steering/longitudinal control. Synthetic inference and unit tests do not
establish real-world lane or blindspot accuracy.
