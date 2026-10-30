function shutdownNoticeData(payload, deviceId) {
  const reason = payload.reason;
  const low = reason === "low_voltage";
  const minutes = payload.offroadLimitMinutes;
  const voltage = payload.voltageV;
  const timestamp = typeof payload.occurredAt === "string" ? Date.parse(payload.occurredAt) : NaN;
  if ((!low && reason !== "offroad_timeout") ||
      !/^shutdown-[a-f0-9]{32}$/.test(payload.id || "") ||
      !Number.isFinite(timestamp) || timestamp < Date.now() - 60000 || timestamp > Date.now() + 5000 ||
      !Number.isInteger(minutes) || minutes < 0 || minutes > 525600 ||
      (voltage != null && (typeof voltage !== "number" || !Number.isFinite(voltage) || voltage <= 0 || voltage >= 30))) {
    return null;
  }
  const test = payload.test === true;
  const detail = low
    ? `배터리 저전압${voltage == null ? "" : ` (${voltage.toFixed(2)}V)`}으로 콤마가 자동 종료될 예정입니다.`
    : `오프로드 ${Number((minutes / 60).toFixed(2))}시간이 지나 콤마가 자동 종료될 예정입니다.`;
  return {
    type: "wayon_automatic_shutdown",
    vehicleEventId: payload.id,
    deviceId,
    occurredAt: new Date(timestamp).toISOString(),
    reason,
    notificationTitle: test ? "콤마 종료 알림 테스트" : "콤마 자동 종료 예정",
    notificationBody: detail + (test
      ? " 테스트 알림이며 실제 기기는 종료하지 않습니다."
      : " 시동이 켜지거나 종료 조건이 해제되면 취소됩니다."),
    test: String(test),
  };
}

async function handleShutdownNotice(payload, request, env, ctx) {
  const deviceId = authenticatedDeviceId(request);
  const data = shutdownNoticeData(payload, deviceId);
  if (!data) return json({error: "invalid_shutdown_notice"}, 400);
  if (!ctx || typeof ctx.waitUntil !== "function") return json({error: "notification_unavailable"}, 503);
  // Claim once before returning. A client timeout must not duplicate a push.
  const inserted = await env.DB.prepare(`
    INSERT OR IGNORE INTO vehicle_events (
      id, device_id, event_type, occurred_at, received_at, locked, notified_count, raw_json
    ) VALUES (?, ?, 'automatic_shutdown', ?, ?, NULL, -1, ?)
  `).bind(data.vehicleEventId, deviceId, data.occurredAt, nowIso(), JSON.stringify(data)).run();
  if (!inserted.success || typeof inserted.meta?.changes !== "number") {
    return json({error: "notification_unavailable"}, 503);
  }
  if (!inserted.meta.changes) {
    const existing = await env.DB.prepare("SELECT notified_count FROM vehicle_events WHERE id = ? AND device_id = ?")
      .bind(data.vehicleEventId, deviceId).first();
    if (!existing) return json({error: "record_conflict"}, 409);
    return json({ok: true, accepted: true, duplicate: true, id: data.vehicleEventId}, 202);
  }
  // The Worker can complete FCM after the comma disconnects. Acceptance is not
  // a phone-delivery receipt, and failures never ask the comma to stay powered.
  ctx.waitUntil((async () => {
    let sent = -2;
    try {
      const result = await sendDataNotifications(env, deviceId, data);
      sent = result.sent > 0 ? result.sent : (result.failed > 0 ? -2 : 0);
    } catch (_) {
      console.warn("Shutdown notification delivery failed");
    }
    try {
      await env.DB.prepare("UPDATE vehicle_events SET notified_count = ? WHERE id = ? AND device_id = ?")
        .bind(sent, data.vehicleEventId, deviceId).run();
    } catch (_) {
      console.warn("Shutdown notification receipt update failed");
    }
  })());
  return json({ok: true, accepted: true, id: data.vehicleEventId}, 202);
}
