package com.example.carcontroller

import org.junit.Assert.*
import org.junit.Test

class VehicleStartupGateTest {
    @Test fun olderCloudWaitsForDirectSnapshot() {
        val gate = VehicleStartupGate<String>()
        val generation = gate.begin(true, true)
        gate.complete(generation, false, "old", 100)
        assertTrue(gate.loading)
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
}
