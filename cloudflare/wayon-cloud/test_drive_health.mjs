import assert from "node:assert/strict";
import { buildTripHealthSummary } from "./src/worker.js";

const start = Date.parse("2026-09-04T01:00:00Z");
const records = [
  {
    type: "heart_rate",
    start_time: start - 600_000,
    end_time: start + 600_000,
    values: {
      series: [
        { start_time: start - 300_000, value: 70 },
        { start_time: start - 120_000, value: 72 },
        { start_time: start - 30_000, value: 71 },
        { start_time: start + 10_000, value: 72 },
        { start_time: start + 40_000, value: 88 },
        { start_time: start + 70_000, value: 92 },
        { start_time: start + 100_000, value: 75 },
        { start_time: start + 160_000, value: 73 },
      ],
    },
  },
  {
    type: "watch_hrv_5m",
    start_time: start,
    end_time: start + 300_000,
    values: { signal_quality_percent: 92, rmssd_ms: 41 },
  },
  {
    type: "watch_driver_sensors_1m",
    start_time: start + 30_000,
    end_time: start + 90_000,
    values: {
      eda_mean_us: 2.4,
      eda_p90_us: 3.1,
      eda_phasic_rise_count: 2,
      eda_sample_count: 45,
      skin_temperature_mean_c: 33.2,
      ambient_temperature_mean_c: 24.1,
      skin_temperature_sample_count: 18,
      motion_rms_mps2: 1.2,
      motion_p95_mps2: 2.6,
      moving_percent: 22,
      accelerometer_sample_count: 600,
    },
  },
  {
    type: "sleep",
    start_time: start - 10 * 3_600_000,
    end_time: start - 2 * 3_600_000,
    values: { sleep_score: 87, duration_seconds: 28_800 },
  },
];

const report = buildTripHealthSummary(records, {
  started_at: new Date(start).toISOString(),
  ended_at: new Date(start + 180_000).toISOString(),
}, {
  timeline: [
    { time: new Date(start + 10_000).toISOString(), opActive: false },
    { time: new Date(start + 40_000).toISOString(), opActive: true },
    { time: new Date(start + 70_000).toISOString(), opActive: true },
    { time: new Date(start + 100_000).toISOString(), opActive: false },
    { time: new Date(start + 160_000).toISOString(), opActive: false },
  ],
  moments: [{
    time: new Date(start + 40_000).toISOString(),
    type: "close_lead_acquired",
    severity: "high",
    title: "가까운 선행차 진입",
    detail: "거리 18 m",
  }],
});

assert.equal(report.available, true);
assert.equal(report.context.sleepScore, 87);
assert.equal(report.hrv.validWindowCount, 1);
assert.ok(report.heartRate.peakAboveBaselineBpm > 15);
assert.equal(report.topStressMoments[0].type, "close_lead_acquired");
assert.ok(report.topStressMoments[0].heartRateDeltaBpm > 10);
assert.equal(report.sensors.available, true);
assert.equal(report.sensors.eda.available, true);
assert.equal(report.sensors.temperature.averageSkinC, 33.2);
assert.equal(report.sensors.motion.movingPercent, 22);

console.log("drive health tests passed");
