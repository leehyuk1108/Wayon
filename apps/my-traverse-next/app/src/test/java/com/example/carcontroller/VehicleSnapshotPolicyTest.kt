package com.example.carcontroller

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class VehicleSnapshotPolicyTest {
    private val time = "2026-10-28T10:30:00.000Z"
    private val now = VehicleSnapshotPolicy.parseTime(time)!!
    private val scope = VehicleSnapshotPolicy.scope("one@example.test", "test-key")
    private fun status(cached: Boolean = false, updated: String = time) = WayonVehicleStatus(
        "gmone-direct-android", updated, false,
        JSONObject().put("last_update", updated).put("fuel", 50), cached = cached,
    )

    @Test fun scopeBindsBothAccountAndCloudKey() {
        assertEquals(64, scope.length)
        assertEquals(scope, VehicleSnapshotPolicy.scope(" ONE@example.test ", "test-key"))
        assertNotEquals(scope, VehicleSnapshotPolicy.scope("two@example.test", "test-key"))
        assertNotEquals(scope, VehicleSnapshotPolicy.scope("one@example.test", "other-key"))
    }

    @Test fun roundTripIsAlwaysCachedAndKeepsOriginalTime() {
        val raw = VehicleSnapshotPolicy.encode(scope, status(), now)!!
        val read = VehicleSnapshotPolicy.decode(raw, scope, now + 10_000)!!
        assertTrue(read.cached)
        assertTrue(read.stale)
        assertEquals(now, VehicleSnapshotPolicy.epoch(read))
        assertNull(VehicleSnapshotPolicy.decode(raw, "different-account", now))
        assertNull(VehicleSnapshotPolicy.decode(raw, scope, now + 8L * 86400_000))
        assertNull(VehicleSnapshotPolicy.decode("not-json", scope, now))
    }

    @Test fun timestampsNeverDefaultToNow() {
        assertEquals(now, VehicleSnapshotPolicy.parseTime("2026-10-28 19:30:00"))
        assertNull(VehicleSnapshotPolicy.parseTime("2026-10-28 19:30:00TRAILING"))
        assertNull(VehicleSnapshotPolicy.parseTime("2026-02-30 12:00:00"))
        assertFalse(VehicleSnapshotPolicy.usable(status(updated = ""), now))
        assertFalse(VehicleSnapshotPolicy.usable(status(), now - 121_000))
        assertFalse(VehicleSnapshotPolicy.usable(status(), now + 8L * 86400_000))
    }

    @Test fun credentialsAndIdentifiersDoNotReachStorageOrUpload() {
        val value = status()
        value.data.put("token", "nope").put("email", "one@example.test")
            .put("module", JSONObject().put("uuid", "nope").put("fuel", 50))
        val payload = VehicleSnapshotPolicy.upload(value, scope, now)!!
        assertEquals(time, payload.getString("vehicleUpdatedAt"))
        assertEquals(scope, payload.getString("clientScope"))
        val clean = payload.getJSONObject("status")
        assertFalse(clean.has("token"))
        assertFalse(clean.has("email"))
        assertFalse(clean.getJSONObject("module").has("uuid"))
        assertEquals(50, clean.getJSONObject("module").getInt("fuel"))
        assertNull(VehicleSnapshotPolicy.upload(status(cached = true), scope, now))
    }

    @Test fun cachedSourceStringCannotBecomeFreshCommandEvidence() {
        val observation = DirectVehicleObservation()
        observation.record(status(cached = true), scope, 1000)
        assertNull(observation.recent(scope, 1001, now))
        observation.record(status(), scope, 1000)
        assertNotNull(observation.recent(scope, 1001, now))
        assertNull(observation.recent("other-account", 1001, now))
        assertNull(observation.recent(scope, 31_001, now))
        assertNull(observation.recent(scope, 1001, now + 31_000))
        assertNull(observation.recent(scope, 999, now))
        observation.clear()
        assertNull(observation.recent(scope, 1001, now))
    }

    @Test fun fullSnapshotWinsEqualTimeWithoutAllowingOldDataToWin() {
        val full = status(cached = true)
        full.data.put("gmone_details", JSONObject().put("module", JSONObject().put("settings", JSONObject().put("x", 1))))
        assertTrue(VehicleSnapshotPolicy.rank(full) < VehicleSnapshotPolicy.rank(status()))
        val freshFull = full.copy(cached = false)
        assertTrue(VehicleSnapshotPolicy.rank(freshFull) > VehicleSnapshotPolicy.rank(full))
    }

    @Test fun productionStoredEndpointContractStaysCachedEvenWithDirectSource() {
        val envelope = JSONObject().put("vehicleStatus", JSONObject().put("ok", true)
            .put("source", "gmone-direct-android").put("updatedAt", time).put("stale", false)
            .put("clientScope", scope).put("data", status().data))
        val parsed = WayonCloudFeedParser.parse(envelope.toString()).vehicleStatus!!
        assertTrue(parsed.cached)
        assertEquals(scope, parsed.clientScope)
        assertEquals(now, VehicleSnapshotPolicy.epoch(parsed))
        assertNull(VehicleSnapshotPolicy.upload(parsed, scope, now))
        assertNull(WayonCloudFeedParser.parse("{\"vehicleStatus\":null}").vehicleStatus)
    }

    @Test fun storedEndpointPreservesTopLevelDetailsWithoutMergedFeed() {
        val envelope = JSONObject().put("vehicleStatus", JSONObject().put("ok", true)
            .put("source", "gmone-direct").put("updatedAt", time).put("clientScope", scope)
            .put("data", status().data)
            .put("module", JSONObject().put("settings", JSONObject().put("all_function_stop", 1)))
            .put("health", JSONObject().put("dtcCount", 2))
            .put("diagnostic", JSONObject().put("pollCount", 3)))
        val parsed = WayonCloudFeedParser.parse(envelope.toString()).vehicleStatus!!
        val details = parsed.data.getJSONObject("gmone_details")
        assertEquals(1, details.getJSONObject("module").getJSONObject("settings").getInt("all_function_stop"))
        assertEquals(2, details.getJSONObject("diagnostics").getInt("dtcCount"))
        assertEquals(3, details.getJSONObject("refresh").getJSONObject("collector").getInt("pollCount"))
        assertTrue(parsed.cached)
        val observation = DirectVehicleObservation()
        observation.record(parsed, scope, 100)
        assertNull(observation.recent(scope, 101, now))
    }
}
