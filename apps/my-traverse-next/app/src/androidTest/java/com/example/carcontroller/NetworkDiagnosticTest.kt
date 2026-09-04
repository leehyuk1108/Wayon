package com.example.carcontroller

import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.core.app.ActivityScenario
import org.junit.Test
import org.junit.runner.RunWith
import android.util.Log
import java.net.URL
import javax.net.ssl.HttpsURLConnection

@RunWith(AndroidJUnit4::class)
class NetworkDiagnosticTest {
    @Test
    fun testRawNetwork() {
        Log.d("CompTest", "Starting Raw Network Test")
        try {
            val url = URL("https://www.google.com")
            val conn = url.openConnection() as HttpsURLConnection
            conn.connectTimeout = 5000
            conn.readTimeout = 5000
            conn.connect()
            val code = conn.responseCode
            Log.d("CompTest", "Network Success! Code: $code")
            conn.disconnect()
        } catch (e: Exception) {
            Log.e("CompTest", "Network Failed", e)
            throw e
        }
    }
}
