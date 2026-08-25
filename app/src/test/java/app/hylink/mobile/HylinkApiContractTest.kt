package app.hylink.mobile

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import org.json.JSONObject

class HylinkApiContractTest {
    @Test
    fun readEndpointsContainOnlyWayonReadFeatures() {
        val paths = HylinkApiContract.READ_ENDPOINTS.map { it.path }

        assertTrue(paths.contains("/api/state"))
        assertTrue(paths.any { it.startsWith("/api/trips") })
        assertTrue(paths.any { it.startsWith("/api/snapshots") })
        assertTrue(paths.any { it.startsWith("/api/impacts") })
        assertTrue(paths.any { it.startsWith("/api/live-captures") })
        assertFalse(paths.any { it.contains("gmone", ignoreCase = true) })
        assertFalse(paths.any { it.contains("command", ignoreCase = true) })
        assertFalse(paths.any { it.contains("control", ignoreCase = true) })
    }

    @Test
    fun liveEndpointCreatesOnlyACameraSession() {
        assertTrue(HylinkApiContract.LIVE_SESSION_ENDPOINT == "/api/live/session")
    }

    @Test
    fun feedDropsBundledAccountVehicleStatus() {
        val payload = JSONObject()
            .put("state", JSONObject().put("onroad", false))
            .put("vehicleStatus", JSONObject().put("source", "account"))
            .put("vehicleLock", JSONObject().put("known", true))

        val sanitized = HylinkApiContract.sanitize("feed", payload)

        assertTrue(sanitized.has("state"))
        assertFalse(sanitized.has("vehicleStatus"))
        assertFalse(sanitized.has("vehicleLock"))
    }
}
