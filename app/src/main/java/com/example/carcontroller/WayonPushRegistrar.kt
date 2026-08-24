package com.example.carcontroller

import android.content.Context
import android.util.Log
import com.google.firebase.messaging.FirebaseMessaging
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

object WayonPushRegistrar {
    private const val TAG = "WayonPush"
    private const val PREFS = "wayon_push"
    private const val LAST_TOKEN = "last_registered_token"
    private const val LAST_REGISTERED_AT = "last_registered_at"
    private const val REFRESH_INTERVAL_MS = 24L * 60L * 60L * 1000L
    private val executor = Executors.newSingleThreadExecutor()

    fun registerCurrentToken(context: Context) {
        if (BuildConfig.APPLICATION_ID.endsWith(".source")) return
        FirebaseMessaging.getInstance().token
            .addOnSuccessListener { token -> registerToken(context, token) }
            .addOnFailureListener { error -> Log.w(TAG, "FCM token lookup failed", error) }
    }

    fun registerToken(context: Context, token: String, force: Boolean = false) {
        if (BuildConfig.APPLICATION_ID.endsWith(".source")) return
        val appContext = context.applicationContext
        val wayonKey = appContext.getSharedPreferences(MainActivity.PREFS_NAME, Context.MODE_PRIVATE)
            .getString(MainActivity.PREF_KEY_WAYON_CLOUD_KEY, null)
            ?.trim()
            .orEmpty()
        if (token.isBlank() || wayonKey.isBlank()) {
            Log.w(TAG, "Wayon push registration is not configured")
            return
        }

        val prefs = appContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val registrationIdentity = "$token:${wayonKey.hashCode()}"
        val recentlyRegistered = prefs.getString(LAST_TOKEN, null) == registrationIdentity &&
            System.currentTimeMillis() - prefs.getLong(LAST_REGISTERED_AT, 0L) < REFRESH_INTERVAL_MS
        if (!force && recentlyRegistered) return

        executor.execute {
            try {
                val endpoint = "${BuildConfig.WAYON_CLOUD_URL}/api/push/register"
                val connection = (URL(endpoint).openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"
                    connectTimeout = 10_000
                    readTimeout = 10_000
                    doOutput = true
                    setRequestProperty("Authorization", "Bearer $wayonKey")
                    setRequestProperty("Content-Type", "application/json")
                }
                val payload = JSONObject()
                    .put("fcmToken", token)
                    .put("platform", "android")
                    .put("appVersion", BuildConfig.VERSION_NAME)
                connection.outputStream.use { output ->
                    output.write(payload.toString().toByteArray(Charsets.UTF_8))
                }

                val responseCode = connection.responseCode
                if (responseCode in 200..299) {
                    prefs.edit()
                        .putString(LAST_TOKEN, registrationIdentity)
                        .putLong(LAST_REGISTERED_AT, System.currentTimeMillis())
                        .apply()
                    Log.i(TAG, "Wayon push registration complete")
                } else {
                    Log.w(TAG, "Wayon push registration failed: HTTP $responseCode")
                }
                connection.disconnect()
            } catch (error: Exception) {
                Log.w(TAG, "Wayon push registration failed", error)
            }
        }
    }
}
