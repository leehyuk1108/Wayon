package com.example.carcontroller

import org.junit.Assert.*
import org.junit.Test

class VehicleStartupGateTest {
    @Test fun cloudPaintsBeforeDirectAndNeverReplacesNewerSnapshot() {
        val gate = VehicleStartupGate<String>()
        val generation = gate.begin(true, true)
        gate.complete(generation, false, "old", 100)
        assertFalse(gate.loading)
        assertTrue(gate.refreshing)
        assertEquals("old", gate.value)
        gate.complete(generation, true, "new", 200)
        assertFalse(gate.loading)
        assertEquals("new", gate.value)
        gate.complete(generation, false, "old-again", 100)
        assertEquals("new", gate.value)
    }

    @Test fun directSnapshotDoesNotWaitForCloud() {
        val gate = VehicleStartupGate<String>()
        val generation = gate.begin(true, true)
        gate.complete(generation, true, "new", 200)
        assertFalse(gate.loading)
        assertEquals("new", gate.value)
    }

    @Test fun directFailureUsesCloudFallback() {
        val gate = VehicleStartupGate<String>()
        val generation = gate.begin(true, true)
        gate.complete(generation, false, "cloud", 200)
        gate.complete(generation, true, null, null)
        assertFalse(gate.loading)
        assertEquals("cloud", gate.value)
    }

    @Test fun bothFailuresFinishLoadingWithoutOldData() {
        val gate = VehicleStartupGate<String>()
        val oldGeneration = gate.begin(true, true)
        gate.complete(oldGeneration, true, "previous-session", 200)
        val generation = gate.begin(true, true)
        assertNull(gate.value)
        assertFalse(gate.complete(oldGeneration, false, "late-response", 400))
        gate.complete(generation, true, null, null)
        assertTrue(gate.loading)
        gate.complete(generation, false, null, null)
        assertFalse(gate.loading)
        assertNull(gate.value)
    }

    @Test fun cloudOnlyAndNoAccount() {
        val gate = VehicleStartupGate<String>()
        var generation = gate.begin(false, true)
        gate.complete(generation, false, "cloud", 200)
        assertFalse(gate.loading)
        assertEquals("cloud", gate.value)
        generation = gate.begin(false, false)
        assertFalse(gate.loading)
        assertNull(gate.value)
        gate.complete(generation, true, "login-after-launch", 300)
        assertEquals("login-after-launch", gate.value)
    }

    @Test fun localCachePaintsWithoutCompletingRequests() {
        val gate = VehicleStartupGate<String>()
        val generation = gate.begin(true, true)
        gate.offerCached(generation, "local", 100)
        assertFalse(gate.loading)
        assertTrue(gate.refreshing)
        gate.complete(generation, true, null, null)
        gate.complete(generation, false, null, null)
        assertEquals("local", gate.value)
        assertFalse(gate.refreshing)
    }

    @Test fun equalTimePrefersFreshBasicOverFullCache() {
        val gate = VehicleStartupGate<String>()
        val gen = gate.begin(true, true)
        gate.offerCached(gen, "full-cache", 100, 2)
        gate.complete(gen, true, "basic-direct", 100, 4)
        assertEquals("basic-direct", gate.value)
        gate.complete(gen, true, "full-direct", 100, 6)
        gate.complete(gen, false, "full-server", 100, 2)
        assertEquals("full-direct", gate.value)
        gate.complete(gen, true, "new-basic", 200, 4)
        assertEquals("new-basic", gate.value)
    }

    @Test fun serverOnlyStartupFinishesAtServerResponseWithoutDirectWait() {
        val gate = VehicleStartupGate<String>()
        val gen = gate.begin(false, true)
        assertTrue(gate.loading)
        assertNull(gate.value)
        gate.complete(gen, false, "server", 200)
        assertEquals("server", gate.value)
        assertFalse(gate.loading)
        assertFalse(gate.refreshing)
    }

    @Test fun serverOnlyFailureNeverRestoresPreviousSession() {
        val gate = VehicleStartupGate<String>()
        val old = gate.begin(false, true)
        gate.complete(old, false, "previous", 200)
        val gen = gate.begin(false, true)
        gate.complete(gen, false, null, null)
        assertNull(gate.value)
        assertFalse(gate.loading)
        assertFalse(gate.refreshing)
        assertFalse(gate.complete(old, false, "late-old-account", 300))
        assertNull(gate.value)
    }

    @Test fun periodicServerFailureKeepsOnlyThisSessionsServerResponse() {
        val gate = VehicleStartupGate<String>()
        val gen = gate.begin(false, true)
        gate.complete(gen, false, "server", 200)
        gate.complete(gen, false, null, null)
        assertEquals("server", gate.value)
        gate.complete(gen, false, "older", 100)
        assertEquals("server", gate.value)
        gate.complete(gen, false, "newer", 300)
        assertEquals("newer", gate.value)
    }
}
