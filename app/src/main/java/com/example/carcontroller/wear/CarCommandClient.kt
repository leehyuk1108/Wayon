package com.example.carcontroller.wear

import android.content.Context
import com.example.carcontroller.MainActivity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.IOException
import java.net.URL
import javax.net.ssl.HttpsURLConnection

object CarCommandClient {
    suspend fun send(context: Context, command: String): Boolean {
        val prefs = context.getSharedPreferences(MainActivity.PREFS_NAME, Context.MODE_PRIVATE)
        val baseApiUrl = prefs.getString(MainActivity.PREF_KEY_API_URL, null)
        return send(baseApiUrl, command)
    }

    suspend fun send(baseApiUrl: String?, command: String): Boolean = withContext(Dispatchers.IO) {
        if (baseApiUrl.isNullOrBlank()) return@withContext false

        var connection: HttpsURLConnection? = null
        return@withContext try {
            connection = (URL("$baseApiUrl&cmd=$command").openConnection() as HttpsURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 5000
                readTimeout = 5000
            }
            connection.responseCode in 200..299
        } catch (_: IOException) {
            false
        } finally {
            connection?.disconnect()
        }
    }
}
