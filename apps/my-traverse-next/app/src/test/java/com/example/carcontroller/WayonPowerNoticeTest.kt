package com.example.carcontroller

import org.junit.Assert.*
import org.junit.Test

class WayonPowerNoticeTest {
    private fun data() = mapOf(
        "type" to "wayon_automatic_shutdown", "reason" to "low_voltage",
        "vehicleEventId" to "shutdown-${"a".repeat(32)}",
        "notificationTitle" to "콤마 자동 종료 예정",
        "notificationBody" to "배터리 저전압 (11.20V)으로 콤마가 자동 종료될 예정입니다.",
    )

    @Test fun validReasonsKeepServerText() {
        for (reason in listOf("low_voltage", "offroad_timeout")) {
            val result = WayonPowerNotice.from(data() + ("reason" to reason))!!
            assertEquals(data()["notificationTitle"], result.title)
            assertEquals(data()["notificationBody"], result.body)
        }
    }

    @Test fun rejectsMalformedAndOtherNotifications() {
        for ((key, value) in listOf("type" to "wayon_door_lock", "reason" to "manual",
            "vehicleEventId" to "", "vehicleEventId" to "invalid",
            "notificationTitle" to " ", "notificationBody" to "", "notificationBody" to "x".repeat(501))) {
            assertNull(WayonPowerNotice.from(data() + (key to value)))
        }
        assertNull(WayonPowerNotice.from(emptyMap()))
    }

    @Test fun testNoticeIsClearlyLabeled() {
        val result = WayonPowerNotice.from(data() + mapOf(
            "test" to "true", "notificationTitle" to "콤마 종료 알림 테스트",
            "notificationBody" to "테스트 알림이며 실제 기기는 종료하지 않습니다.",
        ))!!
        assertTrue(result.title.contains("테스트"))
        assertTrue(result.body.contains("종료하지 않습니다"))
    }
}
