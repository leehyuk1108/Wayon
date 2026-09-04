package com.example.carcontroller

import android.content.Context
import android.util.Log
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Locale
import java.util.TimeZone
import java.util.UUID
import javax.net.ssl.HttpsURLConnection
import org.json.JSONObject

object RemoteStartImpactGuard {
    private const val PREFS = "remote_start_impact_guard"
    private const val KEY_REQUESTED_AT_MS = "requested_at_ms"
    private const val KEY_REQUEST_ID = "request_id"
    internal const val SUPPRESSION_WINDOW_MS = 45_000L

    fun arm(context: Context, requestedAtMs: Long = System.currentTimeMillis()): String {
        val requestId = UUID.randomUUID().toString()
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putLong(KEY_REQUESTED_AT_MS, requestedAtMs)
            .putString(KEY_REQUEST_ID, requestId)
            .commit()
        postCloudMarker(context, "arm", requestId)
        return requestId
    }

    fun cancel(context: Context, requestId: String) {
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        if (prefs.getString(KEY_REQUEST_ID, null) == requestId) prefs.edit().clear().commit()
        postCloudMarker(context, "cancel", requestId)
    }

    fun shouldSuppress(
        context: Context,
        data: Map<String, String>,
        nowMs: Long = System.currentTimeMillis(),
    ): Boolean {
        if (data["test"] == "true") return false
        val requestedAtMs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getLong(KEY_REQUESTED_AT_MS, 0L)
        if (requestedAtMs <= 0L) return false

        val detectedAtMs = parseDetectedAt(data["detectedAt"]) ?: nowMs
        return isWithinSuppressionWindow(requestedAtMs, detectedAtMs)
    }

    internal fun isWithinSuppressionWindow(requestedAtMs: Long, detectedAtMs: Long): Boolean =
        detectedAtMs in requestedAtMs..(requestedAtMs + SUPPRESSION_WINDOW_MS)

    private fun postCloudMarker(context: Context, action: String, requestId: String) {
        val wayonKey = context.getSharedPreferences(MainActivity.PREFS_NAME, Context.MODE_PRIVATE)
            .getString(MainActivity.PREF_KEY_WAYON_CLOUD_KEY, null)
            ?.trim()
            .orEmpty()
        if (wayonKey.isBlank()) {
            Log.w("WayonImpact", "Remote-start suppression cloud credentials are unavailable")
            return
        }

        var connection: HttpsURLConnection? = null
        try {
            connection = (URL("${BuildConfig.WAYON_CLOUD_URL}/api/mobile/impact-suppression")
                .openConnection() as HttpsURLConnection).apply {
                requestMethod = "POST"
                connectTimeout = 8_000
                readTimeout = 8_000
                doOutput = true
                setRequestProperty(
                    "Authorization",
                    "Bearer $wayonKey",
                )
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Accept", "application/json")
                setRequestProperty("User-Agent", "WayonAndroid/2.0")
            }
            val body = JSONObject()
                .put("action", action)
                .put("requestId", requestId)
            connection.outputStream.bufferedWriter(Charsets.UTF_8).use { it.write(body.toString()) }
            val status = connection.responseCode
            if (status !in 200..299) Log.w("WayonImpact", "Suppression marker HTTP $status")
        } catch (error: Exception) {
            Log.w("WayonImpact", "Suppression marker request failed", error)
        } finally {
            connection?.disconnect()
        }
    }

    private fun parseDetectedAt(value: String?): Long? {
        if (value.isNullOrBlank()) return null
        val formats = listOf("yyyy-MM-dd'T'HH:mm:ss.SSSX", "yyyy-MM-dd'T'HH:mm:ssX")
        for (pattern in formats) {
            val parsed = runCatching {
                SimpleDateFormat(pattern, Locale.US).apply {
                    isLenient = false
                    timeZone = TimeZone.getTimeZone("UTC")
                }.parse(value)?.time
            }.getOrNull()
            if (parsed != null) return parsed
        }
        return null
    }
}
