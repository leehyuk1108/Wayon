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
    fun remoteStartImpactGuard_filtersOnlyStartupWindow() {
        val requestedAt = 100_000L
        assertFalse(RemoteStartImpactGuard.isWithinSuppressionWindow(requestedAt, 99_999L))
        assertTrue(RemoteStartImpactGuard.isWithinSuppressionWindow(requestedAt, 100_000L))
        assertTrue(RemoteStartImpactGuard.isWithinSuppressionWindow(requestedAt, 145_000L))
        assertFalse(RemoteStartImpactGuard.isWithinSuppressionWindow(requestedAt, 145_001L))
    }

    @Test
    fun clearDtc_usesOfficialOperationId() {
        assertEquals(47, GmoneAccountClient.clearDtcOperationId())
    }

    @Test
    fun dtcPresentation_decodesGmRawCodesAndDescriptions() {
        assertEquals(
            GmoneAccountClient.DtcPresentation(
                "P129B",
                "연료 펌프 제어 모듈 시스템 전압 낮음",
                "파워트레인",
            ),
            GmoneAccountClient.dtcPresentation(0x129B),
        )
        assertEquals("B2B11", GmoneAccountClient.dtcPresentation(0xAB11).code)
        assertEquals("U0121", GmoneAccountClient.dtcPresentation(0xC121).code)
        assertEquals("U0140", GmoneAccountClient.dtcPresentation(0xC140).code)
        assertEquals("차량 통신 계통 고장코드", GmoneAccountClient.dtcPresentation(0xC999).description)
    }

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
                .put("rsiLvl", 4)
                .put("rvsRmng", 2)
                .put("rvsRmngTm", 17)
                .put("rvsRmngTmVld", 1)
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
        assertEquals(77.3, details.getJSONObject("fuel").getDouble("levelPercent"), 0.0)
        assertEquals(63.4633, details.getJSONObject("fuel").getDouble("levelLiters"), 0.0001)
        assertTrue(details.getJSONObject("closures").getJSONObject("doors").getBoolean("active"))
        assertFalse(details.getJSONObject("closures").getJSONObject("hood").getBoolean("active"))
        assertEquals("잠금 해제", details.getJSONObject("closures").getJSONObject("doors").getString("label"))
        assertEquals(4L, details.getJSONObject("connectivity").getLong("moduleSignalLevel"))
        assertFalse(details.getJSONObject("remoteStart").has("levelRaw"))
        assertEquals(17L, details.getJSONObject("remoteStart").getLong("remainingTimeRaw"))
        assertTrue(details.getJSONObject("remoteStart").getBoolean("remainingTimeValid"))
        assertEquals(1, details.getJSONObject("diagnostics").getInt("failedCount"))
        assertFalse(details.getJSONObject("rawStatus").has("dtc"))
        assertEquals(4.6, details.getJSONObject("runningCycles").getDouble("totalDistanceKm"), 0.0)
        assertEquals(20L, details.getJSONObject("runningCycles").getJSONArray("recent").getJSONObject(0).getLong("time"))
    }

    @Test
    fun gmoneSettingsPatch_validatesKnownRangesAndPreservesUnknownCurrentValues() {
        val current = JSONObject()
            .put("auto_door_lock", 1)
            .put("firmware_only_option", 73)
        val patch = GmoneAccountClient.validateSettingsPatch(
            JSONObject()
                .put("auto_door_lock", 0)
                .put("shock_sensor_delay_seconds", 30),
        )
        val merged = GmoneAccountClient.mergeSettings(current, patch)

        assertEquals(0, merged.getInt("auto_door_lock"))
        assertEquals(30, merged.getInt("shock_sensor_delay_seconds"))
        assertEquals(73, merged.getInt("firmware_only_option"))
    }

    @Test
    fun gmoneSettingsPatch_rejectsUnknownAndInvalidValues() {
        assertThrows(IllegalArgumentException::class.java) {
            GmoneAccountClient.validateSettingsPatch(JSONObject().put("main_light", 1))
        }
        assertThrows(IllegalArgumentException::class.java) {
            GmoneAccountClient.validateSettingsPatch(JSONObject().put("shock_sensor_delay_seconds", 3))
        }
        assertThrows(IllegalArgumentException::class.java) {
            GmoneAccountClient.validateSettingsPatch(JSONObject().put("blind_alert_speed", 101))
        }
    }

    @Test
    fun hiddenGmoneControls_useProtocolTypeAndOptionFromOfficialEnums() {
        assertEquals(
            GmoneAccountClient.ExtendedControlSpec(1, 2, "운전석 도어 잠금을 해제했습니다."),
            GmoneAccountClient.extendedControlSpec("DRIVER_DOOR_UNLOCK"),
        )
        assertEquals(4, GmoneAccountClient.extendedControlSpec("MAIN_LIGHT_OFF").controlType)
        assertEquals(0, GmoneAccountClient.extendedControlSpec("MAIN_LIGHT_OFF").requestOption)
        assertEquals(1, GmoneAccountClient.extendedControlSpec("MAIN_LIGHT_ON").requestOption)
        assertThrows(IllegalArgumentException::class.java) {
            GmoneAccountClient.extendedControlSpec("ARBITRARY_CONTROL")
        }
    }

    @Test
    fun mainVehicleControls_useVerifiedGmoneProtocolMappings() {
        val expected = mapOf(
            "VEHICLE_START" to (0 to 2),
            "VEHICLE_STOP" to (0 to 0),
            "DOOR_LOCK" to (1 to 0),
            "DOOR_UNLOCK" to (1 to 1),
            "TRUNK_CLOSE" to (2 to 0),
            "TRUNK_OPEN" to (2 to 1),
            "PANIC" to (3 to 1),
            "WINDOW_CLOSE" to (5 to 0),
            "WINDOW_OPEN" to (5 to 1),
            "SUNROOF_CLOSE" to (6 to 0),
            "SUNROOF_OPEN" to (6 to 1),
            "SUNROOF_TILT" to (6 to 3),
        )

        expected.forEach { (command, mapping) ->
            val spec = GmoneAccountClient.extendedControlSpec(command)
            assertEquals(command, mapping.first, spec.controlType)
            assertEquals(command, mapping.second, spec.requestOption)
        }
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

    @Test
    fun cloudFeed_exposesExistingLiveOpenpilotAndDeviceState() {
        val raw = JSONObject()
            .put("ignition", true)
            .put("thermalStatus", "yellow")
            .put("gps", JSONObject()
                .put("fresh", true)
                .put("timestampMillis", 1_787_073_600_000L))
            .put("openpilot", JSONObject()
                .put("available", true)
                .put("state", "enabled")
                .put("enabled", true)
                .put("active", true)
                .put("engageable", true))
        val state = JSONObject()
            .put("updated_at", "2026-08-19T04:00:00Z")
            .put("onroad", 1)
            .put("ignition", 1)
            .put("enabled", 1)
            .put("thermal_status", "yellow")
            .put("voltage_v", 13.8)
            .put("latitude", 37.5)
            .put("longitude", 126.7)
            .put("speed_mps", 20.0)
            .put("raw_json", raw.toString())
        val feed = WayonCloudFeedParser.parse(JSONObject()
            .put("state", state)
            .put("trips", JSONArray())
            .put("snapshots", JSONArray())
            .toString())

        assertTrue(feed.state?.onroad == true)
        assertTrue(feed.state?.ignition == true)
        assertTrue(feed.state?.openpilotEnabled == true)
        assertTrue(feed.state?.openpilotActive == true)
        assertTrue(feed.state?.openpilotEngageable == true)
        assertEquals("enabled", feed.state?.openpilotState)
        assertEquals("yellow", feed.state?.thermalStatus)
        assertTrue(feed.state?.gpsFresh == true)
        assertEquals(1_787_073_600_000L, feed.state?.gpsUpdatedAtEpochMs)

        val live = JSONObject(feed.state!!.toLiveStatusJson())
        assertEquals(72.0, live.getDouble("speedKph"), 0.0)
        assertTrue(live.getBoolean("openpilotActive"))
    }
}
