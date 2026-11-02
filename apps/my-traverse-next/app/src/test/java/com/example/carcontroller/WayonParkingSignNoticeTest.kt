package com.example.carcontroller

import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertEquals
import org.junit.Test

class WayonParkingSignNoticeTest {
    private val now = 1793588400000L // 2026-11-02T03:00:00Z
    private fun data() = mapOf(
        "type" to "wayon_parking_sign", "parkingEventId" to "abc123", "jobId" to "a".repeat(32),
        "occurredAt" to "2026-11-02T03:00:00.000Z", "notificationTitle" to "주차 주변 표지 인식",
        "notificationBody" to "기둥 B-12 · AI 판독, 정확한 주차 위치는 아님",
    )

    @Test fun acceptsFreshUnicodeNotice() {
        val notice = WayonParkingSignNotice.from(data(), now)!!
        assertEquals("abc123", notice.eventId)
        assertEquals(data()["notificationBody"], notice.body)
    }

    @Test fun acceptsUtcAndExplicitOffsets() {
        for (stamp in listOf("2026-11-02T03:00:00Z", "2026-11-02T12:00:00.000+09:00", "2026-11-02T03:00:00.000+00:00")) {
            assertNotNull(stamp, WayonParkingSignNotice.from(data() + ("occurredAt" to stamp), now))
        }
    }

    @Test fun rejectsStaleFutureAndMalformedTimeEvenInTestMode() {
        for (stamp in listOf("2026-11-02T02:49:59Z", "2026-11-02T03:02:01Z", "2026-11-02T03:00:00Zgarbage",
            "2026-11-32T03:00:00Z", "2026-11-02T03:00:00", "", "2026-11-02T03:00:00.000000Z")) {
            assertNull(stamp, WayonParkingSignNotice.from(data() + mapOf("occurredAt" to stamp, "test" to "true"), now))
        }
    }

    @Test fun rejectsWrongTypeIdsAndUnsafeText() {
        for ((key, value) in listOf("type" to "wayon_impact", "parkingEventId" to "../x", "parkingEventId" to "",
            "parkingEventId" to "a".repeat(129), "jobId" to "bad", "notificationTitle" to "",
            "notificationTitle" to "a".repeat(101), "notificationBody" to "a".repeat(501), "notificationBody" to "bad\ntext")) {
            assertNull("$key=$value", WayonParkingSignNotice.from(data() + (key to value), now))
        }
        assertNull(WayonParkingSignNotice.from(emptyMap(), now))
    }

    @Test fun acceptsExactFreshnessBoundaries() {
        assertNotNull(WayonParkingSignNotice.from(data(), now + WayonParkingSignNotice.MAX_AGE_MS))
        assertNotNull(WayonParkingSignNotice.from(data(), now - WayonParkingSignNotice.FUTURE_SKEW_MS))
        assertNull(WayonParkingSignNotice.from(data(), now + WayonParkingSignNotice.MAX_AGE_MS + 1))
    }
}
