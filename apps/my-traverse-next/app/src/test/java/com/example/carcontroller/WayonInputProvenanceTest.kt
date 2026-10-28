package com.example.carcontroller

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class WayonInputProvenanceTest {
    private fun live(raw: JSONObject?, legacyVoltage: Any = JSONObject.NULL): JSONObject {
        val state = JSONObject()
            .put("updated_at", "2026-10-28T01:00:00Z")
            .put("onroad", 0)
            .put("voltage_v", legacyVoltage)
        if (raw != null) state.put("raw_json", raw.toString())
        val feed = WayonCloudFeedParser.parse(JSONObject().put("state", state).toString())
        return JSONObject(feed.state!!.toLiveStatusJson())
    }

    @Test
    fun qualifiedVehicleInputSurvivesActualCloudFlattening() {
        val input = JSONObject()
            .put("qualified", true)
            .put("fresh", true)
            .put("kind", "vehicleInputEstimate")
            .put("voltageV", 13.8)
        val device = JSONObject().put("voltageV", 5.0)
        val result = live(JSONObject().put("vehicleInput", input).put("deviceInput", device))
        assertTrue(input.similar(result.getJSONObject("vehicleInput")))
        assertTrue(device.similar(result.getJSONObject("deviceInput")))
        assertTrue(result.isNull("voltageV"))
        assertFalse(result.has("battery12v"))
    }

    @Test
    fun absentOrNullProvenanceIsNotInventedFromLegacyOrDeviceVoltage() {
        for (raw in listOf(null, JSONObject(), JSONObject()
            .put("vehicleInput", JSONObject.NULL)
            .put("deviceInput", JSONObject().put("voltageV", 5.0)))) {
            val result = live(raw, 5.0)
            assertTrue(result.isNull("vehicleInput"))
            assertEquals(5.0, result.getDouble("voltageV"), 0.0)
            assertFalse(result.has("battery12v"))
        }
    }

    @Test
    fun negativeQualificationIsPassedThroughWithoutPromotion() {
        val input = JSONObject().put("qualified", false).put("fresh", false)
            .put("kind", "vehicleInputEstimate").put("voltageV", JSONObject.NULL)
        val result = live(JSONObject().put("vehicleInput", input))
        assertTrue(input.similar(result.getJSONObject("vehicleInput")))
    }
}
