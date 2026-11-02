async function handleWebTrips(request, env) {
  if (!authorize(request, env, false)) return json({ error: "unauthorized" }, 401);
  if (request.method !== "GET") return json({ error: "method_not_allowed" }, 405);
  const deviceId = authenticatedDeviceId(request);
  if (!deviceId) return json({ error: "unauthorized" }, 401);
  const limit = boundedLimit(new URL(request.url).searchParams.get("limit"), 25, 1000);
  try {
    const { results } = await env.DB.prepare(`
      SELECT id, device_id, started_at, ended_at, duration_s, distance_m,
        start_lat, start_lon, end_lat, end_lon, route_point_count,
        source, route_name, segment_count, avg_speed_mps, max_speed_mps
      FROM trips WHERE device_id = ? ORDER BY ended_at DESC LIMIT ?
    `).bind(deviceId, limit).all();
    if (!Array.isArray(results)) return json({ error: "web_trips_unavailable" }, 503);
    return json({ trips: results });
  } catch {
    return json({ error: "web_trips_unavailable" }, 503);
  }
}
__name(handleWebTrips, "handleWebTrips");
