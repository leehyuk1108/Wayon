package com.example.carcontroller

import android.content.Context
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.launch
import java.net.URL
import javax.net.ssl.HttpsURLConnection
import org.json.JSONObject

/** One active upload and one latest pending value. No vehicle calls or persisted credentials. */
internal object VehicleSnapshotSync {
    private data class Upload(val context: Context, val key: String, val scope: String, val payload: String)
    private val pending = Channel<Upload>(Channel.CONFLATED)
    private val worker = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    init {
        worker.launch {
            for (upload in pending) {
                val prefs = upload.context.getSharedPreferences(MainActivity.PREFS_NAME, Context.MODE_PRIVATE)
                val key = prefs.getString(MainActivity.PREF_KEY_WAYON_CLOUD_KEY, null)
                val email = GmoneAccountStore(upload.context).account()?.email
                if (key != upload.key || email == null || VehicleSnapshotPolicy.scope(email, key) != upload.scope) continue
                runCatching {
                    val connection = URL("${BuildConfig.WAYON_CLOUD_URL}/api/gmone/status").openConnection() as HttpsURLConnection
                    try {
                        connection.requestMethod = "POST"
                        connection.instanceFollowRedirects = false
                        connection.doOutput = true
                        connection.connectTimeout = 5_000
                        connection.readTimeout = 5_000
                        connection.setRequestProperty("Authorization", "Bearer ${upload.key}")
                        connection.setRequestProperty("Content-Type", "application/json")
                        val bytes = upload.payload.toByteArray(Charsets.UTF_8)
                        connection.setFixedLengthStreamingMode(bytes.size)
                        connection.outputStream.use { it.write(bytes) }
                        check(connection.responseCode in 200..299) { "HTTP ${connection.responseCode}" }
                        val response = connection.inputStream.use { stream ->
                            val out = java.io.ByteArrayOutputStream()
                            val buffer = ByteArray(1024)
                            while (true) {
                                val count = stream.read(buffer)
                                if (count < 0) break
                                check(out.size() + count <= 16 * 1024) { "Oversized acknowledgement" }
                                out.write(buffer, 0, count)
                            }
                            out.toString("UTF-8")
                        }
                        check(JSONObject(response).optBoolean("ok"))
                        Log.i("VehicleSnapshot", "Server snapshot acknowledged")
                    } finally {
                        connection.disconnect()
                    }
                }.onFailure { Log.w("VehicleSnapshot", "Snapshot upload failed: ${it.javaClass.simpleName}") }
            }
        }
    }

    fun enqueue(context: Context, key: String?, scope: String, status: WayonVehicleStatus) {
        if (key.isNullOrBlank()) return
        val body = VehicleSnapshotPolicy.upload(status, scope, System.currentTimeMillis()) ?: return
        pending.trySend(Upload(context.applicationContext, key, scope, body.toString()))
    }
}
