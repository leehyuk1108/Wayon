package app.hylink.mobile

import android.annotation.SuppressLint
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.net.URL
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean
import javax.net.ssl.HttpsURLConnection

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private val networkExecutor = Executors.newSingleThreadExecutor()
    private val mainHandler = Handler(Looper.getMainLooper())
    private val refreshInFlight = AtomicBoolean(false)
    private var pageReady = false
    private var activityVisible = false
    private var liveActive = false

    private val preferences by lazy { getSharedPreferences(PREFERENCES_NAME, MODE_PRIVATE) }

    private val autoRefresh = object : Runnable {
        override fun run() {
            if (activityVisible && pageReady && !liveActive) refreshWayonData()
            mainHandler.postDelayed(this, AUTO_REFRESH_INTERVAL_MS)
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG)
        webView = findViewById(R.id.webview)
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            allowFileAccess = true
            allowContentAccess = false
            allowFileAccessFromFileURLs = false
            allowUniversalAccessFromFileURLs = false
            mixedContentMode = WebSettings.MIXED_CONTENT_NEVER_ALLOW
            mediaPlaybackRequiresUserGesture = false
            userAgentString = "$userAgentString Hylink/${BuildConfig.VERSION_NAME}"
        }
        webView.addJavascriptInterface(this, "Android")
        webView.webChromeClient = WebChromeClient()
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                return request?.isForMainFrame == true && request.url.scheme != "file"
            }

            override fun onPageFinished(view: WebView?, url: String?) {
                pageReady = true
                sendNativeConfiguration()
                if (loadWayonCloudKey().isNotBlank()) refreshWayonData()
            }
        }
        webView.loadUrl("file:///android_asset/main.html")

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                webView.evaluateJavascript("window.handleHylinkBack?.() === true") { result ->
                    if (result != "true") finish()
                }
            }
        })
    }

    override fun onResume() {
        super.onResume()
        activityVisible = true
        mainHandler.removeCallbacks(autoRefresh)
        mainHandler.post(autoRefresh)
    }

    override fun onPause() {
        activityVisible = false
        mainHandler.removeCallbacks(autoRefresh)
        super.onPause()
    }

    override fun onDestroy() {
        mainHandler.removeCallbacksAndMessages(null)
        networkExecutor.shutdownNow()
        webView.removeJavascriptInterface("Android")
        webView.destroy()
        super.onDestroy()
    }

    @JavascriptInterface
    fun getWayonCloudKey(): String = loadWayonCloudKey()

    @JavascriptInterface
    fun getWayonCloudBaseUrl(): String = BuildConfig.WAYON_CLOUD_URL

    @JavascriptInterface
    fun saveWayonCloudKey(value: String) {
        val normalized = value.trim()
        preferences.edit().putString(PREFERENCE_WAYON_KEY, normalized).apply()
        runJs("window.onHylinkKeySaved?.(${JSONObject.quote(normalized)})")
        if (normalized.isNotBlank()) refreshWayonData()
    }

    @JavascriptInterface
    fun clearWayonCloudKey() {
        preferences.edit().remove(PREFERENCE_WAYON_KEY).apply()
        runJs("window.onHylinkKeyCleared?.()")
    }

    @JavascriptInterface
    fun refreshWayonData() {
        val key = loadWayonCloudKey()
        if (key.isBlank()) {
            runJs("window.onHylinkError?.('Wayon Cloud 키를 입력해 주세요.')")
            return
        }
        if (!refreshInFlight.compareAndSet(false, true)) return
        runJs("window.onHylinkLoading?.()")

        networkExecutor.execute {
            val result = JSONObject()
            val errors = JSONArray()
            try {
                HylinkApiContract.READ_ENDPOINTS.forEach { endpoint ->
                    try {
                        result.put(endpoint.name, HylinkApiContract.sanitize(endpoint.name, fetchJson(endpoint.path, key)))
                    } catch (error: Exception) {
                        Log.w(TAG, "Wayon endpoint failed: ${endpoint.path}", error)
                        errors.put(JSONObject().put("name", endpoint.name).put("message", safeMessage(error)))
                    }
                }
                result.put("receivedAt", System.currentTimeMillis())
                result.put("errors", errors)
                if (!result.has("feed")) throw IOException("현재 차량 상태를 불러오지 못했습니다.")
                runJs("window.onHylinkData?.(JSON.parse(${JSONObject.quote(result.toString())}))")
            } catch (error: Exception) {
                Log.w(TAG, "Wayon refresh failed", error)
                runJs("window.onHylinkError?.(${JSONObject.quote(safeMessage(error))})")
            } finally {
                refreshInFlight.set(false)
            }
        }
    }

    @JavascriptInterface
    fun requestTripDetail(id: String) {
        val safeId = id.trim()
        val key = loadWayonCloudKey()
        if (safeId.isBlank() || key.isBlank()) return
        networkExecutor.execute {
            try {
                val detail = fetchJson("/api/trips/${encodePathSegment(safeId)}", key)
                runJs("window.onHylinkTripDetail?.(JSON.parse(${JSONObject.quote(detail.toString())}))")
            } catch (error: Exception) {
                runJs("window.onHylinkTripError?.(${JSONObject.quote(safeMessage(error))})")
            }
        }
    }

    @JavascriptInterface
    fun requestWayonLiveSession() {
        val key = loadWayonCloudKey()
        if (key.isBlank()) {
            runJs("window.onWayonLiveSessionError?.('Wayon Cloud 키가 없습니다.')")
            return
        }
        networkExecutor.execute {
            try {
                val response = postJson(HylinkApiContract.LIVE_SESSION_ENDPOINT, key, JSONObject())
                val websocketUrl = response.getString("websocketUrl")
                val protocol = response.getString("protocol")
                runJs(
                    "window.onWayonLiveSession?.(" +
                        "${JSONObject.quote(websocketUrl)},${JSONObject.quote(protocol)})",
                )
            } catch (error: Exception) {
                Log.w(TAG, "Wayon Live session failed", error)
                runJs("window.onWayonLiveSessionError?.(${JSONObject.quote(safeMessage(error))})")
            }
        }
    }

    @JavascriptInterface
    fun setWayonLiveActive(active: Boolean) {
        liveActive = active
        if (!active && activityVisible) refreshWayonData()
    }

    private fun sendNativeConfiguration() {
        runJs(
            "window.onHylinkNativeReady?.(" +
                "${JSONObject.quote(loadWayonCloudKey())},${JSONObject.quote(BuildConfig.WAYON_CLOUD_URL)})",
        )
    }

    private fun loadWayonCloudKey(): String =
        preferences.getString(PREFERENCE_WAYON_KEY, "").orEmpty().trim()

    private fun fetchJson(path: String, key: String): JSONObject =
        requestJson("GET", path, key, null)

    private fun postJson(path: String, key: String, body: JSONObject): JSONObject =
        requestJson("POST", path, key, body)

    private fun requestJson(method: String, path: String, key: String, body: JSONObject?): JSONObject {
        val connection = (URL("${BuildConfig.WAYON_CLOUD_URL}$path").openConnection() as HttpsURLConnection).apply {
            requestMethod = method
            connectTimeout = NETWORK_TIMEOUT_MS
            readTimeout = NETWORK_TIMEOUT_MS
            useCaches = false
            setRequestProperty("Authorization", "Bearer $key")
            setRequestProperty("Accept", "application/json")
            setRequestProperty("Cache-Control", "no-cache")
            setRequestProperty("User-Agent", "HylinkAndroid/${BuildConfig.VERSION_NAME}")
            if (body != null) {
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
        }
        return try {
            if (body != null) {
                connection.outputStream.bufferedWriter(Charsets.UTF_8).use { it.write(body.toString()) }
            }
            val status = connection.responseCode
            val stream = if (status in 200..299) connection.inputStream else connection.errorStream
            val text = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
            if (status !in 200..299) {
                val message = runCatching { JSONObject(text).optString("error") }.getOrNull()
                throw IOException(message?.takeIf { it.isNotBlank() } ?: "Wayon Cloud HTTP $status")
            }
            JSONObject(text)
        } finally {
            connection.disconnect()
        }
    }

    private fun runJs(script: String) {
        mainHandler.post {
            if (pageReady && !isFinishing && !isDestroyed) webView.evaluateJavascript(script, null)
        }
    }

    private fun safeMessage(error: Exception): String = when {
        error.message?.contains("unauthorized", ignoreCase = true) == true -> "Wayon Cloud 키를 확인해 주세요."
        else -> error.message?.take(160)?.takeIf { it.isNotBlank() } ?: "Wayon Cloud 연결에 실패했습니다."
    }

    private fun encodePathSegment(value: String): String =
        java.net.URLEncoder.encode(value, Charsets.UTF_8.name()).replace("+", "%20")

    companion object {
        private const val TAG = "Hylink"
        private const val PREFERENCES_NAME = "HylinkPreferences"
        private const val PREFERENCE_WAYON_KEY = "wayon_cloud_key"
        private const val AUTO_REFRESH_INTERVAL_MS = 30_000L
        private const val NETWORK_TIMEOUT_MS = 15_000
    }
}

internal object HylinkApiContract {
    data class Endpoint(val name: String, val path: String)

    val READ_ENDPOINTS = listOf(
        Endpoint("feed", "/api/state"),
        Endpoint("trips", "/api/trips?limit=250"),
        Endpoint("snapshots", "/api/snapshots?limit=100"),
        Endpoint("impacts", "/api/impacts?limit=100"),
        Endpoint("liveCaptures", "/api/live-captures?limit=100"),
    )

    val LIVE_SESSION_ENDPOINT = "/api/live/session"

    fun sanitize(name: String, payload: JSONObject): JSONObject {
        if (name == "feed") {
            payload.remove("vehicleStatus")
            payload.remove("vehicleLock")
        }
        return payload
    }
}
