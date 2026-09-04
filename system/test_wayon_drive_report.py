from types import SimpleNamespace

from openpilot.system.wayon_drive_report import DriveReportAccumulator


def message(which, mono_s, payload):
  return SimpleNamespace(which=lambda: which, logMonoTime=int(mono_s * 1e9), **{which: payload})


def car_state(speed, accel=0.0, steering=False, brake=False, gas=False):
  return SimpleNamespace(vEgo=speed, vEgoCluster=0.0, aEgo=accel, steeringPressed=steering,
                         brakePressed=brake, gasPressed=gas)


def test_drive_report_counts_op_usage_and_harsh_stop():
  report = DriveReportAccumulator()
  report.update(message("selfdriveState", 0.0, SimpleNamespace(
    active=True, enabled=True, alertType="", alertStatus="normal")))
  report.update(message("carState", 0.0, car_state(4.0)))
  report.update(message("carState", 0.1, car_state(2.0, -1.0)))
  report.update(message("carState", 0.2, car_state(0.7, -1.7)))
  report.update(message("carState", 0.3, car_state(0.1, -1.5)))

  result = report.finalize([])
  assert result["automation"]["opUsagePercent"] == 100.0
  assert result["comfort"]["stopCount"] == 1
  assert result["comfort"]["harshStopCount"] == 1
  assert any(moment["type"] == "harsh_stop" for moment in result["moments"])


def test_drive_report_tracks_distraction_and_close_lead():
  report = DriveReportAccumulator()
  vision = SimpleNamespace(isDistracted=True, faceDetected=True)
  report.update(message("driverMonitoringState", 0.0, SimpleNamespace(
    visionPolicyState=vision, alertLevel="one")))
  report.update(message("driverMonitoringState", 1.0, SimpleNamespace(
    visionPolicyState=vision, alertLevel="one")))
  lead = SimpleNamespace(status=True, dRel=18.0, vRel=-4.0)
  report.update(message("radarState", 1.1, SimpleNamespace(leadOne=lead)))

  result = report.finalize([])
  assert result["attention"]["alertCount"] == 1
  assert result["longitudinal"]["leadAcquisitionCount"] == 1
  assert any(moment["type"] == "close_lead_acquired" for moment in result["moments"])


def test_drive_report_deduplicates_sustained_hard_braking():
  report = DriveReportAccumulator()
  for index in range(30):
    report.update(message("carState", index * 0.1, car_state(15.0, -3.0)))
  result = report.finalize([])
  assert result["comfort"]["hardBrakingCount"] == 1
