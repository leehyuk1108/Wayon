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
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import java.util.Locale

class WayonMessagingService : FirebaseMessagingService() {
    override fun onNewToken(token: String) {
        WayonPushRegistrar.registerToken(this, token, force = true)
    }

    override fun onMessageReceived(message: RemoteMessage) {
        when (message.data["type"]) {
            "wayon_impact" -> WayonImpactNotifications.show(this, message.data)
            "wayon_door_lock" -> WayonDoorLockNotifications.show(this, message.data)
            "wayon_parking_unlocked" -> WayonParkingNotifications.show(this, message.data)
        }
    }
}

object WayonDoorLockNotifications {
    private const val CHANNEL_ID = "wayon_door_lock_alerts"

    fun ensureChannel(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val channel = NotificationChannel(
            CHANNEL_ID,
            "차량 잠금 알림",
            NotificationManager.IMPORTANCE_HIGH,
        ).apply {
            description = "차량 잠금이 활성화되거나 해제되면 알려줍니다"
            enableVibration(true)
            vibrationPattern = longArrayOf(0, 180, 120, 280)
            lockscreenVisibility = android.app.Notification.VISIBILITY_PRIVATE
        }
        context.getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }

    fun show(context: Context, data: Map<String, String>) {
        ensureChannel(context)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ActivityCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) !=
            PackageManager.PERMISSION_GRANTED
        ) return

        val locked = data["locked"] == "true"
        val isTest = data["test"] == "true"
        val title = when {
            isTest -> "차량 잠금 알림 테스트"
            locked -> "차량 잠금 활성화"
            else -> "차량 잠금 해제"
        }
        val detail = if (locked) {
            "차량 잠금이 활성화되었습니다."
        } else {
            "차량 잠금이 해제되었습니다."
        }
        val eventId = data["vehicleEventId"].orEmpty()
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            putExtra("wayonVehicleEventId", eventId)
        }
        val pendingIntent = PendingIntent.getActivity(
            context,
            eventId.hashCode(),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentTitle(title)
            .setContentText(detail)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_STATUS)
            .setVisibility(NotificationCompat.VISIBILITY_PRIVATE)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()

        val notificationId = eventId.hashCode().let { if (it == 0) 9301 else it }
        (context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager)
            .notify(notificationId, notification)
    }
}

object WayonParkingNotifications {
    private const val CHANNEL_ID = "wayon_parking_alerts"

    fun ensureChannel(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val channel = NotificationChannel(
            CHANNEL_ID,
            "주차 후 미잠금 알림",
            NotificationManager.IMPORTANCE_HIGH,
        ).apply {
            description = "주차 후 차량이 잠기지 않으면 현재 위치와 함께 알려줍니다"
            enableVibration(true)
            vibrationPattern = longArrayOf(0, 250, 150, 450)
            lockscreenVisibility = android.app.Notification.VISIBILITY_PRIVATE
        }
        context.getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }

    fun show(context: Context, data: Map<String, String>) {
        ensureChannel(context)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ActivityCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) !=
            PackageManager.PERMISSION_GRANTED
        ) return

        val eventId = data["vehicleEventId"].orEmpty()
        val delaySeconds = data["delaySeconds"]?.toIntOrNull()?.coerceAtLeast(0) ?: 180
        val minutes = maxOf(1, (delaySeconds + 59) / 60)
        val latitude = data["latitude"]?.toDoubleOrNull()
        val longitude = data["longitude"]?.toDoubleOrNull()
        val location = if (latitude != null && longitude != null) {
            String.format(Locale.KOREA, "%.5f, %.5f", latitude, longitude)
        } else {
            "위치 정보 확인 중"
        }
        val detail = "차량이 ${minutes}분 동안 잠기지 않았습니다."
        val body = "$detail\n현재 위치: $location"
        val title = if (data["test"] == "true") "차량 미잠금 알림 테스트" else "차량이 잠기지 않았습니다"
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            putExtra("wayonVehicleEventId", eventId)
            if (latitude != null) putExtra("wayonLatitude", latitude)
            if (longitude != null) putExtra("wayonLongitude", longitude)
        }
        val pendingIntent = PendingIntent.getActivity(
            context,
            eventId.hashCode(),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentTitle(title)
            .setContentText("${minutes}분간 미잠금 · $location")
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_REMINDER)
            .setVisibility(NotificationCompat.VISIBILITY_PRIVATE)
            .setLocalOnly(false)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()

        val notificationId = eventId.hashCode().let { if (it == 0) 9401 else it }
        (context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager)
            .notify(notificationId, notification)
    }
}

object WayonImpactNotifications {
    private const val CHANNEL_ID = "wayon_impact_alerts"

    fun ensureChannel(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val channel = NotificationChannel(
            CHANNEL_ID,
            "주차 충격 감지",
            NotificationManager.IMPORTANCE_HIGH,
        ).apply {
            description = "주차 중 차량 충격이 감지되면 알려줍니다"
            enableVibration(true)
            vibrationPattern = longArrayOf(0, 250, 150, 450)
            lockscreenVisibility = android.app.Notification.VISIBILITY_PRIVATE
        }
        context.getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }

    fun show(context: Context, data: Map<String, String>) {
        ensureChannel(context)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ActivityCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) !=
            PackageManager.PERMISSION_GRANTED
        ) return

        val isTest = data["test"] == "true"
        val severity = when (data["severity"]) {
            "severe" -> "강한"
            "moderate" -> "중간"
            else -> "가벼운"
        }
        val peakG = data["peakDynamicG"]?.toDoubleOrNull()
        val detail = if (peakG != null) {
            String.format(Locale.KOREA, "%s 충격 · %.2f g", severity, peakG)
        } else {
            "$severity 충격이 감지됐습니다"
        }
        val title = if (isTest) "Wayon 충격 알림 테스트" else "주차 충격 감지"

        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            action = "CMD_WAYON_LIVE"
            putExtra("wayonImpactId", data["impactId"])
        }
        val pendingIntent = PendingIntent.getActivity(
            context,
            data["impactId"].orEmpty().hashCode(),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentTitle(title)
            .setContentText(detail)
            .setStyle(NotificationCompat.BigTextStyle().bigText(
                if (isTest) "$detail\nCloud와 My Traverse 알림 연결이 정상입니다." else detail,
            ))
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setVisibility(NotificationCompat.VISIBILITY_PRIVATE)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()

        val notificationId = data["impactId"].orEmpty().hashCode().let { if (it == 0) 9201 else it }
        (context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager)
            .notify(notificationId, notification)
    }
}
