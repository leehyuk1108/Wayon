package com.example.carcontroller

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.SystemClock
import android.util.Log
import com.google.android.gms.tasks.Tasks
import com.google.firebase.database.ktx.database
import com.google.firebase.ktx.Firebase
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.URL
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import javax.net.ssl.HttpsURLConnection

internal object VehicleRefreshPolicy {
    const val ACTIVE_REFRESH_INTERVAL_MS = 60L * 60L * 1000L

    fun nextActiveDelayMs(enabled: Boolean, lastRequestAtMs: Long, nowMs: Long): Long? {
        if (!enabled) return null
        if (lastRequestAtMs <= 0L) return ACTIVE_REFRESH_INTERVAL_MS
        return (lastRequestAtMs + ACTIVE_REFRESH_INTERVAL_MS - nowMs).coerceAtLeast(0L)
    }

    fun isActiveRefreshDue(enabled: Boolean, lastRequestAtMs: Long, nowMs: Long): Boolean {
        val delay = nextActiveDelayMs(enabled, lastRequestAtMs, nowMs) ?: return false
        return delay == 0L
    }
}

object VehicleRefreshScheduler {
    const val PREF_KEY_AUTO_REFRESH_ENABLED = "AUTO_REFRESH_ENABLED"
    const val PREF_KEY_LAST_AUTO_REFRESH_REQUEST_MS = "LAST_AUTO_REFRESH_REQUEST_MS"
    const val PREF_KEY_LAST_PASSIVE_FEED_JSON = "LAST_PASSIVE_FEED_JSON"
    const val PREF_KEY_LAST_PASSIVE_FEED_AT_MS = "LAST_PASSIVE_FEED_AT_MS"

    private const val ACTION_ACTIVE_REFRESH = "com.example.carcontroller.AUTO_VEHICLE_REFRESH"
    private const val ACTION_PASSIVE_SYNC = "com.example.carcontroller.PASSIVE_VEHICLE_SYNC"
    private const val ACTIVE_REQUEST_CODE = 8101
    private const val PASSIVE_REQUEST_CODE = 8102
    private const val PASSIVE_SYNC_INTERVAL_MS = 15L * 60L * 1000L
    private const val PASSIVE_SYNC_INITIAL_DELAY_MS = 60L * 1000L

    fun initialize(context: Context) {
        schedulePassiveSync(context)
        if (isAutoRefreshEnabled(context)) scheduleNextActiveRefresh(context)
        else cancelActiveRefresh(context)
    }

    fun isAutoRefreshEnabled(context: Context): Boolean = preferences(context)
        .getBoolean(PREF_KEY_AUTO_REFRESH_ENABLED, true)

    fun hasSavedAutoRefreshSetting(context: Context): Boolean =
        preferences(context).contains(PREF_KEY_AUTO_REFRESH_ENABLED)

    fun setAutoRefreshEnabled(context: Context, enabled: Boolean) {
        val wasEnabled = isAutoRefreshEnabled(context)
        preferences(context).edit().putBoolean(PREF_KEY_AUTO_REFRESH_ENABLED, enabled).apply()
        if (enabled) {
            if (!wasEnabled) {
                preferences(context).edit().putLong(PREF_KEY_LAST_AUTO_REFRESH_REQUEST_MS, System.currentTimeMillis()).apply()
            }
            scheduleNextActiveRefresh(context)
        } else {
            cancelActiveRefresh(context)
        }
        schedulePassiveSync(context)
        Log.i("VehicleRefresh", "Automatic vehicle refresh ${if (enabled) "enabled" else "disabled"}; passive sync remains enabled")
    }

    fun recordVehicleRefreshRequest(context: Context, requestedAtMs: Long = System.currentTimeMillis()) {
        preferences(context).edit().putLong(PREF_KEY_LAST_AUTO_REFRESH_REQUEST_MS, requestedAtMs).apply()
        if (isAutoRefreshEnabled(context)) scheduleNextActiveRefresh(context, requestedAtMs)
    }

    fun cachedPassiveFeed(context: Context): String? = preferences(context)
        .getString(PREF_KEY_LAST_PASSIVE_FEED_JSON, null)
        ?.takeIf { it.isNotBlank() }

    internal fun scheduleNextActiveRefresh(context: Context, nowMs: Long = System.currentTimeMillis()) {
        val prefs = preferences(context)
        val delayMs = VehicleRefreshPolicy.nextActiveDelayMs(
            enabled = isAutoRefreshEnabled(context),
            lastRequestAtMs = prefs.getLong(PREF_KEY_LAST_AUTO_REFRESH_REQUEST_MS, 0L),
            nowMs = nowMs,
        ) ?: run {
            cancelActiveRefresh(context)
            return
        }
        alarmManager(context).setAndAllowWhileIdle(
            AlarmManager.ELAPSED_REALTIME_WAKEUP,
            SystemClock.elapsedRealtime() + delayMs,
            pendingIntent(context, ACTION_ACTIVE_REFRESH, ACTIVE_REQUEST_CODE),
        )
        Log.d("VehicleRefresh", "Next automatic vehicle refresh scheduled in ${delayMs / 1000}s")
    }

    internal fun schedulePassiveSync(context: Context) {
        alarmManager(context).setInexactRepeating(
            AlarmManager.ELAPSED_REALTIME_WAKEUP,
            SystemClock.elapsedRealtime() + PASSIVE_SYNC_INITIAL_DELAY_MS,
            PASSIVE_SYNC_INTERVAL_MS,
            pendingIntent(context, ACTION_PASSIVE_SYNC, PASSIVE_REQUEST_CODE),
        )
    }

    internal fun cancelActiveRefresh(context: Context) {
        alarmManager(context).cancel(pendingIntent(context, ACTION_ACTIVE_REFRESH, ACTIVE_REQUEST_CODE))
    }

    internal fun handleActiveRefresh(context: Context) {
        val prefs = preferences(context)
        val nowMs = System.currentTimeMillis()
        if (!VehicleRefreshPolicy.isActiveRefreshDue(
                isAutoRefreshEnabled(context),
                prefs.getLong(PREF_KEY_LAST_AUTO_REFRESH_REQUEST_MS, 0L),
                nowMs,
            )
        ) {
            scheduleNextActiveRefresh(context, nowMs)
            return
        }

        recordVehicleRefreshRequest(context, nowMs)
        requestVehicleRefresh(context)
        Log.i("VehicleRefresh", "Hourly automatic vehicle refresh request accepted")
    }

    internal fun handlePassiveSync(context: Context) {
        val key = preferences(context)
            .getString(MainActivity.PREF_KEY_WAYON_CLOUD_KEY, null)
            ?.takeIf { it.isNotBlank() }
            ?: return
        val connection = (URL("${BuildConfig.WAYON_CLOUD_URL}/api/json").openConnection() as HttpsURLConnection).apply {
            requestMethod = "GET"
            useCaches = false
            connectTimeout = 8_000
            readTimeout = 8_000
            setRequestProperty("Authorization", "Bearer $key")
            setRequestProperty("Accept", "application/json")
            setRequestProperty("Cache-Control", "no-cache")
            setRequestProperty("User-Agent", "WayonAndroid/${BuildConfig.VERSION_NAME}")
        }
        try {
            val responseCode = connection.responseCode
            if (responseCode !in 200..299) error("HTTP $responseCode")
            val body = BufferedReader(InputStreamReader(connection.inputStream, Charsets.UTF_8)).use { it.readText() }
            preferences(context).edit()
                .putString(PREF_KEY_LAST_PASSIVE_FEED_JSON, body)
                .putLong(PREF_KEY_LAST_PASSIVE_FEED_AT_MS, System.currentTimeMillis())
                .apply()
            Log.i("VehicleRefresh", "Passive Wayon data sync complete; no vehicle refresh requested")
        } finally {
            connection.disconnect()
        }
    }

    private fun requestVehicleRefresh(context: Context) {
        val key = preferences(context)
            .getString(MainActivity.PREF_KEY_WAYON_CLOUD_KEY, null)
            ?.takeIf { it.isNotBlank() }
        if (key != null) {
            val connection = (URL("${BuildConfig.WAYON_CLOUD_URL}/api/gmone/refresh").openConnection() as HttpsURLConnection).apply {
                requestMethod = "POST"
                doOutput = true
                useCaches = false
                connectTimeout = 8_000
                readTimeout = 8_000
                setRequestProperty("Authorization", "Bearer $key")
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Accept", "application/json")
            }
            try {
                connection.outputStream.use { it.write("{}".toByteArray(Charsets.UTF_8)) }
                val responseCode = connection.responseCode
                if (responseCode !in 200..299) error("HTTP $responseCode")
            } finally {
                connection.disconnect()
            }
            return
        }

        if (BuildConfig.FIREBASE_CONFIGURED) {
            val task = Firebase.database(BuildConfig.FIREBASE_DATABASE_URL)
                .reference.child("car_status").child("cmd_refresh")
                .setValue(System.currentTimeMillis())
            Tasks.await(task, 8, TimeUnit.SECONDS)
            return
        }
        error("No vehicle refresh route is configured")
    }

    private fun preferences(context: Context) = context.applicationContext
        .getSharedPreferences(MainActivity.PREFS_NAME, Context.MODE_PRIVATE)

    private fun alarmManager(context: Context) =
        context.getSystemService(Context.ALARM_SERVICE) as AlarmManager

    private fun pendingIntent(context: Context, action: String, requestCode: Int): PendingIntent {
        val intent = Intent(context, VehicleRefreshReceiver::class.java).setAction(action)
        return PendingIntent.getBroadcast(
            context,
            requestCode,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
    }

    internal fun isActiveAction(action: String?): Boolean = action == ACTION_ACTIVE_REFRESH
    internal fun isPassiveAction(action: String?): Boolean = action == ACTION_PASSIVE_SYNC
}

class VehicleRefreshReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            VehicleRefreshScheduler.initialize(context)
            return
        }
        val pendingResult = goAsync()
        EXECUTOR.execute {
            try {
                when {
                    VehicleRefreshScheduler.isActiveAction(intent.action) ->
                        VehicleRefreshScheduler.handleActiveRefresh(context)
                    VehicleRefreshScheduler.isPassiveAction(intent.action) ->
                        VehicleRefreshScheduler.handlePassiveSync(context)
                }
            } catch (error: Exception) {
                Log.w("VehicleRefresh", "Scheduled vehicle synchronization failed: ${error.message}")
            } finally {
                if (VehicleRefreshScheduler.isActiveAction(intent.action) &&
                    VehicleRefreshScheduler.isAutoRefreshEnabled(context)
                ) {
                    VehicleRefreshScheduler.scheduleNextActiveRefresh(context)
                }
                pendingResult.finish()
            }
        }
    }

    companion object {
        private val EXECUTOR = Executors.newSingleThreadExecutor()
    }
}
