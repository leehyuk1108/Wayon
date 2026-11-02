package com.example.carcontroller

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.util.Log
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat
import java.text.ParsePosition
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.TimeZone
import org.json.JSONObject

internal data class WayonParkingSignNotice(val eventId: String, val title: String, val body: String) {
    companion object {
        internal const val MAX_AGE_MS = 10 * 60 * 1000L
        internal const val FUTURE_SKEW_MS = 2 * 60 * 1000L

        fun from(data: Map<String, String>, nowMs: Long = System.currentTimeMillis()): WayonParkingSignNotice? {
            if (data["type"] != "wayon_parking_sign") return null
            val id = data["parkingEventId"].orEmpty()
            val title = data["notificationTitle"].orEmpty()
            val body = data["notificationBody"].orEmpty()
            if (!id.matches(Regex("[A-Za-z0-9_-]{1,128}")) ||
                !data["jobId"].orEmpty().matches(Regex("[a-f0-9]{32}")) ||
                title.isBlank() || title.length > 100 || body.isBlank() || body.length > 500 ||
                (title + body).any { Character.isISOControl(it) }) return null
            val timestamp = data["occurredAt"].orEmpty()
            if (!timestamp.matches(Regex("\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?(Z|[+-]\\d{2}:\\d{2})"))) return null
            val pattern = if (timestamp.contains('.')) "yyyy-MM-dd'T'HH:mm:ss.SSSXXX" else "yyyy-MM-dd'T'HH:mm:ssXXX"
            val position = ParsePosition(0)
            val occurredAt = SimpleDateFormat(pattern, Locale.US).apply {
                isLenient = false
                timeZone = TimeZone.getTimeZone("UTC")
            }.parse(timestamp, position)?.time ?: return null
            if (position.index != timestamp.length || occurredAt < nowMs - MAX_AGE_MS ||
                occurredAt > nowMs + FUTURE_SKEW_MS) return null
            return WayonParkingSignNotice(id, title, body)
        }
    }
}

object WayonParkingSignNotifications {
    private const val CHANNEL_ID = "wayon_parking_sign_alerts"
    private const val PREFS = "wayon_parking_sign_delivery"
    private const val RETENTION_MS = 24 * 60 * 60 * 1000L

    fun ensureChannel(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val channel = NotificationChannel(CHANNEL_ID, "주차 표지 인식", NotificationManager.IMPORTANCE_HIGH).apply {
            description = "주차 사진에서 읽힌 층과 기둥 번호를 알려줍니다. 정확한 주차 위치 확정은 아닙니다."
            enableVibration(true)
            lockscreenVisibility = android.app.Notification.VISIBILITY_PRIVATE
        }
        context.getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }

    @Synchronized
    fun show(context: Context, data: Map<String, String>) {
        val now = System.currentTimeMillis()
        val notice = WayonParkingSignNotice.from(data, now) ?: return
        ensureChannel(context)
        val manager = context.getSystemService(NotificationManager::class.java)
        if (!manager.areNotificationsEnabled() || (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ActivityCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) !=
            PackageManager.PERMISSION_GRANTED)) return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O &&
            manager.getNotificationChannel(CHANNEL_ID)?.importance == NotificationManager.IMPORTANCE_NONE) return
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val recent = runCatching { JSONObject(prefs.getString("recent", "{}") ?: "{}") }.getOrElse { JSONObject() }
        val retained = recent.keys().asSequence().map { it to recent.optLong(it) }
            .filter { (_, received) -> received in (now - RETENTION_MS)..now }
            .sortedByDescending { it.second }.take(127).toList()
        if (retained.any { it.first == notice.eventId }) return
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
            .setOnlyAlertOnce(true)
            .setContentIntent(pending)
            .build()
        manager.notify(notice.eventId, 0, notification)
        val next = JSONObject()
        retained.forEach { (id, received) -> next.put(id, received) }
        next.put(notice.eventId, now)
        prefs.edit().putString("recent", next.toString()).apply()
        Log.i("WayonParkingSign", "Parking sign notification posted")
    }
}
