package com.example.carcontroller

import java.io.IOException
import org.junit.Assert.*
import org.junit.Test

class GmoneResultPollerTest {
    private var clock = 0L
    private val waits = mutableListOf<Long>()
    private fun poller() = GmoneResultPoller(
        nowMs = { clock },
        sleepMs = { waits.add(it); clock += it },
    )

    @Test fun completedResultIsDeliveredOnFirstCheck() {
        assertEquals("done", poller().await { "done" })
        assertEquals(listOf(250L), waits)
    }

    @Test fun normalCompletionHasAtMostOneSecondPollingDelay() {
        for (readyAt in listOf(500L, 3_000L, 5_100L, 8_100L, 11_900L)) {
            clock = 0
            waits.clear()
            assertEquals("done", poller().await { if (clock >= readyAt) "done" else null })
            assertTrue("readyAt=$readyAt deliveredAt=$clock", clock - readyAt in 0L..1_000L)
        }
    }

    @Test fun timeoutBacksOffAndBoundsRequestCount() {
        var calls = 0
        assertThrows(IOException::class.java) {
            poller().await<String> { calls++; null }
        }
        assertEquals(30_000L, clock)
        assertTrue(calls <= 20)
        assertTrue(waits.contains(2_000L))
        assertTrue(waits.contains(5_000L))
    }

    @Test fun slowResponsesDoNotProduceCatchUpBursts() {
        val starts = mutableListOf<Long>()
        assertThrows(IOException::class.java) {
            poller().await<String> { starts.add(clock); clock += 4_000L; null }
        }
        val gaps = starts.zipWithNext().map { (first, second) -> second - first }
        assertTrue(gaps.dropLast(1).all { it >= 5_000L })
        // The final wait may be shortened to the deadline, but never overlaps a request.
        assertTrue(gaps.last() > 4_000L)
        assertTrue(starts.last() <= 30_000L)
        assertTrue(clock <= 34_000L)
    }

    @Test fun transportFailureIsNotRetried() {
        var calls = 0
        val failure = IOException("connection lost")
        val actual = assertThrows(IOException::class.java) {
            poller().await<String> { calls++; throw failure }
        }
        assertSame(failure, actual)
        assertEquals(1, calls)
    }

    @Test fun interruptedWaitNeverRequestsAnotherResult() {
        var called = false
        assertThrows(InterruptedException::class.java) {
            GmoneResultPoller(nowMs = { clock }, sleepMs = { throw InterruptedException() })
                .await<String> { called = true; null }
        }
        assertFalse(called)
    }
}
