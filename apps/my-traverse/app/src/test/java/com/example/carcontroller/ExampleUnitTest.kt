package com.example.carcontroller

import org.json.JSONArray
import org.json.JSONObject
import org.junit.Test

import org.junit.Assert.*

/**
 * Example local unit test, which will execute on the development machine (host).
 *
 * See [testing documentation](http://d.android.com/tools/testing).
 */
class ExampleUnitTest {
    @Test
    fun autoRefreshPolicy_disabledNeverRequestsVehicle() {
        assertNull(VehicleRefreshPolicy.nextActiveDelayMs(false, 0L, 10_000L))
        assertFalse(VehicleRefreshPolicy.isActiveRefreshDue(false, 0L, 10_000L))
    }

    @Test
    fun autoRefreshPolicy_firstRequestIsOneHourAfterEnable() {
        assertEquals(
            VehicleRefreshPolicy.ACTIVE_REFRESH_INTERVAL_MS,
            VehicleRefreshPolicy.nextActiveDelayMs(true, 0L, 10_000L),
        )
    }

    @Test
    fun autoRefreshPolicy_becomesDueAfterOneHour() {
        val lastRequest = 10_000L
        assertEquals(
            1_000L,
            VehicleRefreshPolicy.nextActiveDelayMs(
                true,
                lastRequest,
                lastRequest + VehicleRefreshPolicy.ACTIVE_REFRESH_INTERVAL_MS - 1_000L,
            ),
        )
        assertTrue(
            VehicleRefreshPolicy.isActiveRefreshDue(
                true,
                lastRequest,
                lastRequest + VehicleRefreshPolicy.ACTIVE_REFRESH_INTERVAL_MS,
            ),
        )
    }

    @Test
    fun manualRefreshCompletion_requiresMatchingFinishedRequest() {
        val requestedAt = "2026-08-18T02:14:15.311Z"
        assertFalse(
            WayonRefreshCompletionPolicy.isComplete(
                requestedAt,
                WayonRefreshStatus(true, requestedAt, null),
            ),
        )
        assertFalse(
            WayonRefreshCompletionPolicy.isComplete(
                requestedAt,
                WayonRefreshStatus(false, "2026-08-18T01:00:00.000Z", "2026-08-18T01:00:30.000Z"),
            ),
        )
        assertTrue(
            WayonRefreshCompletionPolicy.isComplete(
                requestedAt,
                WayonRefreshStatus(false, requestedAt, "2026-08-18T02:15:00.626Z"),
            ),
        )
    }

    @Test
    fun addition_isCorrect() {
        assertEquals(4, 2 + 2)
    }

    @Test
    fun directTirePressure_isConvertedToKpa() {
        assertEquals(268.0, GmoneAccountClient.normalizeTirePressureKpa(67.0), 0.0)
        assertEquals(252.0, GmoneAccountClient.normalizeTirePressureKpa(252.0), 0.0)
    }

    @Test
    fun cloudTirePressureText_isNormalizedWithoutDoubleConversion() {
        assertEquals(
            "타이어 정보\n268 kpa\n272 kpa\n272 kpa\n280 kpa",
            MainActivity.normalizeTirePressureText("타이어 정보\n67 kpa\n68 kpa\n68 kpa\n70 kpa"),
        )
        assertEquals(
            "타이어 정보\n268 kpa\n272 kpa",
            MainActivity.normalizeTirePressureText("타이어 정보\n268 kpa\n272 kpa"),
        )
    }

    @Test
    fun directGmoneDetails_preserveUsefulStatusAndRawFields() {
        val details = GmoneAccountClient.normalizeDetails(
            JSONObject()
                .put("volt", 12.3)
                .put("btChrg", 80)
                .put("btHlth", 75)
                .put("btTmp", 35)
                .put("fCap", 82.1)
                .put("fLvl", 77.3)
                .put("door", 1)
                .put("hood", 0)
                .put("eng", 0)
                .put("rvsRmng", 2)
                .put("dtcCnt", 1)
                .put("dtc", JSONArray().put(JSONObject()
                    .put("addr", 16)
                    .put("code", 123)
                    .put("fail", 3)
                    .put("stats", 16))),
            JSONArray()
                .put(JSONObject().put("time", 20).put("dis", 3.4).put("drvTm", 120).put("fuse", 0.3))
                .put(JSONObject().put("time", 10).put("dis", 1.2).put("drvTm", 60).put("fuse", 0.1)),
        )

        assertEquals(35L, details.getJSONObject("battery12v").getLong("temperatureC"))
        assertTrue(details.getJSONObject("closures").getJSONObject("doors").getBoolean("active"))
        assertFalse(details.getJSONObject("closures").getJSONObject("hood").getBoolean("active"))
        assertEquals(1, details.getJSONObject("diagnostics").getInt("failedCount"))
        assertFalse(details.getJSONObject("rawStatus").has("dtc"))
        assertEquals(4.6, details.getJSONObject("runningCycles").getDouble("totalDistanceKm"), 0.0)
        assertEquals(20L, details.getJSONObject("runningCycles").getJSONArray("recent").getJSONObject(0).getLong("time"))
    }

    @Test
    fun cloudFeed_prefersNewerVehicleTimestampInsteadOfCollectorArrivalTime() {
        val firebaseData = JSONObject()
            .put("last_update", "2026-08-18 08:42:09")
            .put("source", "gmone-direct")
            .put("battery_level", "80")
            .put("gmone_details", JSONObject().put("battery12v", JSONObject().put("temperatureC", 34)))
        val gmoneData = JSONObject()
            .put("last_update", "2026-08-18 01:34:00")
            .put("battery_level", "90")
        val vehicleStatus = JSONObject()
            .put("ok", true)
            .put("source", "firebase+gmone-direct")
            .put("updatedAt", "2026-08-18T01:34:00Z")
            .put("data", JSONObject(gmoneData.toString()).put("gmone_details", firebaseData.getJSONObject("gmone_details")))
            .put("sources", JSONObject()
                .put("firebase", JSONObject().put("ok", true).put("updatedAt", "2026-08-18T08:42:15Z").put("data", firebaseData))
                .put("gmone", JSONObject().put("ok", true).put("updatedAt", "2026-08-18T01:34:00Z").put("data", gmoneData)))
        val feed = WayonCloudFeedParser.parse(JSONObject()
            .put("vehicleStatus", vehicleStatus)
            .put("trips", JSONArray())
            .put("snapshots", JSONArray())
            .toString())

        assertEquals("gmone-direct", feed.vehicleStatus?.source)
        assertEquals("80", feed.vehicleStatus?.data?.getString("battery_level"))
        assertEquals("2026-08-18 08:42:09", feed.vehicleStatus?.updatedAt)
        assertEquals(
            34,
            feed.vehicleStatus?.data?.getJSONObject("gmone_details")?.getJSONObject("battery12v")?.getInt("temperatureC"),
        )
    }
}
