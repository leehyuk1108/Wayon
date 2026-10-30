package com.example.carcontroller

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat

internal data class WayonPowerNotice(val eventId: String, val title: String, val body: String) {
    companion object {
        fun from(data: Map<String, String>): WayonPowerNotice? {
            if (data["type"] != "wayon_automatic_shutdown" ||
                data["reason"] !in setOf("low_voltage", "offroad_timeout")) return null
            val id = data["vehicleEventId"].orEmpty()
            val title = data["notificationTitle"].orEmpty()
            val body = data["notificationBody"].orEmpty()
            if (!id.matches(Regex("shutdown-[a-f0-9]{32}")) ||
                title.isBlank() || title.length > 100 || body.isBlank() || body.length > 500) return null
            return WayonPowerNotice(id, title, body)
        }
    }
}

object WayonPowerNotifications {
    private const val CHANNEL_ID = "wayon_power_alerts"

    fun ensureChannel(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val channel = NotificationChannel(CHANNEL_ID, "콤마 전원 알림", NotificationManager.IMPORTANCE_HIGH).apply {
            description = "저전압이나 장시간 대기로 콤마가 자동 종료될 때 알려줍니다"
            enableVibration(true)
            lockscreenVisibility = android.app.Notification.VISIBILITY_PRIVATE
        }
        context.getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }

    fun show(context: Context, data: Map<String, String>) {
        val notice = WayonPowerNotice.from(data) ?: return
        ensureChannel(context)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ActivityCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) !=
            PackageManager.PERMISSION_GRANTED) return
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        val pending = PendingIntent.getActivity(context, notice.eventId.hashCode(), intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification_chevrolet)
            .setContentTitle(notice.title)
            .setContentText(notice.body)
            .setStyle(NotificationCompat.BigTextStyle().bigText(notice.body))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_STATUS)
            .setVisibility(NotificationCompat.VISIBILITY_PRIVATE)
            .setAutoCancel(true)
            .setContentIntent(pending)
            .build()
        context.getSystemService(NotificationManager::class.java).notify(notice.eventId, 0, notification)
    }
}
