package com.example.carcontroller

import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test

class RemoteEngineCommandPolicyTest {
    private fun details(engine: Int = 0, hood: Int = 0, starts: Int = 2, remote: Boolean = false) =
        GmoneAccountClient.normalizeDetails(JSONObject()
            .put("eng", engine).put("hood", hood).put("rvsRmng", starts).put("rvsRmngTmVld", remote))

    @Test fun parkedStartAllowed() {
        assertNull(RemoteEngineCommandPolicy.blockReason("VEHICLE_START", details(), false))
    }

    @Test fun startStillRequiresKnownSafeConditions() {
        for (value in listOf(details(engine = 1), details(hood = 1), details(starts = 0), JSONObject())) {
            assertNotNull(RemoteEngineCommandPolicy.blockReason("VEHICLE_START", value, false))
        }
        assertNotNull(RemoteEngineCommandPolicy.blockReason("VEHICLE_START", details(), true))
    }

    @Test fun stopOnlyRemoteEngineNotOrdinaryRunningEngine() {
        assertNotNull(RemoteEngineCommandPolicy.blockReason("VEHICLE_STOP", details(engine = 1), false))
        assertNull(RemoteEngineCommandPolicy.blockReason("VEHICLE_STOP", details(engine = 1, remote = true), false))
        assertNotNull(RemoteEngineCommandPolicy.blockReason("VEHICLE_STOP", details(remote = true), true))
    }
}
