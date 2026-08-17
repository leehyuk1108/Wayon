package com.example.carcontroller

// (import ... 문들은 기존과 동일)
import android.Manifest
import android.bluetooth.BluetoothA2dp
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothHeadset
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.content.pm.PackageManager
import androidx.core.content.ContextCompat
import kotlinx.coroutines.Job
import com.google.firebase.database.ktx.database
import com.google.firebase.ktx.Firebase

import android.annotation.SuppressLint
import android.app.AlarmManager
import android.app.AlertDialog
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.SharedPreferences
import android.location.Address
import android.location.Geocoder
import android.location.Location
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.SystemClock
import android.util.Log
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.localbroadcastmanager.content.LocalBroadcastManager
import com.example.carcontroller.wear.WearSync
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.io.BufferedReader
import java.io.FileReader
import java.io.IOException
import java.io.InputStreamReader
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import java.util.concurrent.ConcurrentHashMap
import javax.net.ssl.HttpsURLConnection
import org.json.JSONObject

class MainActivity : AppCompatActivity(), CoroutineScope by CoroutineScope(Dispatchers.Main) {

    // ‼️ [NEW] Handle Widget Commands
    private var pendingWidgetAction: String? = null

    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleWidgetCommand(intent)
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (hasFocus && intent?.action == "CMD_WAYON_LIVE") {
            handleWidgetCommand(intent)
        }
    }

    fun handleWidgetCommand(intent: Intent?) {
        if (intent == null) return
        val action = intent.action
        Log.d("MainActivity", "Received Intent Action: $action")

        // If page not loaded, queue execution
        if (!isPageLoaded && action != null && action.startsWith("CMD_")) {
            pendingWidgetAction = action
            Log.d("MainActivity", "Page not loaded. Queuing action: $action")
            return
        }

        when (action) {
            "CMD_START_ENGINE" -> runJs("requestStartEngine()")
            "CMD_STOP_ENGINE" -> runJs("requestStopEngine()")
            "CMD_LOCK_DOOR" -> runJs("requestDoorLock()")
            "CMD_UNLOCK_DOOR" -> runJs("requestDoorUnlock()")
            "CMD_WAYON_LIVE" -> if (hasWindowFocus()) {
                runJs("closeSnapshotViewer();closeSnapshotHistory();switchTab('tab-extras');startWayonLiveView()")
                this.intent?.action = null
            }
            "REFRESH_FROM_WIDGET" -> triggerRefresh()
        }
    }

    @JavascriptInterface
    fun requestWayonLiveSession() {
        if (BuildConfig.WAYON_LIVE_TOKEN.isBlank() ||
            BuildConfig.WAYON_DEVICE_ID.isBlank()
        ) {
            runJs("onWayonLiveSessionError('Live 인증 설정이 없습니다.')")
            return
        }

        launch(Dispatchers.IO) {
            var connection: HttpsURLConnection? = null
            try {
                connection = (URL("${BuildConfig.WAYON_CLOUD_URL}/api/live/session")
                    .openConnection() as HttpsURLConnection).apply {
                    requestMethod = "POST"
                    connectTimeout = 8_000
                    readTimeout = 8_000
                    doOutput = true
                    setRequestProperty(
                        "Authorization",
                        "Bearer ${BuildConfig.WAYON_LIVE_TOKEN}",
                    )
                    setRequestProperty("Content-Type", "application/json")
                }

                connection.outputStream.bufferedWriter(Charsets.UTF_8).use { writer ->
                    writer.write(JSONObject().put("deviceId", BuildConfig.WAYON_DEVICE_ID).toString())
                }

                val status = connection.responseCode
                val stream = if (status in 200..299) connection.inputStream else connection.errorStream
                val response = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
                if (status !in 200..299) throw IOException("Live session HTTP $status")

                val payload = JSONObject(response)
                val websocketUrl = payload.getString("websocketUrl")
                val protocol = payload.getString("protocol")
                runJs("onWayonLiveSession(${JSONObject.quote(websocketUrl)},${JSONObject.quote(protocol)})")
            } catch (error: Exception) {
                Log.w("WayonLive", "Live session request failed", error)
                runJs("onWayonLiveSessionError('차량 Live 연결에 실패했습니다.')")
            } finally {
                connection?.disconnect()
            }
        }
    }

    @JavascriptInterface
    fun setWayonLiveActive(active: Boolean) {
        if (active) {
            stopWayonCloudAutoRefresh()
        } else if (isActivityVisible) {
            refreshWayonCloudFeed(showResult = false)
            startWayonCloudAutoRefresh()
        }
    }

    companion object {
        var isActivityVisible: Boolean = false
        const val PREFS_NAME = "CarAppPrefs"
        const val PREF_KEY_API_URL = "BASE_API_URL"
        const val PREF_KEY_WAYON_CLOUD_KEY = "WAYON_CLOUD_VIEW_TOKEN"
        const val PREF_KEY_LOCATION_LAT = "LAST_LAT"
        const val PREF_KEY_LOCATION_LON = "LAST_LON"
        const val PREF_KEY_LOCATION_TIME = "LAST_TIME"
        const val PREF_KEY_MAC_ADDRESS = "MY_CHEVROLET_MAC_ADDRESS"
        const val ACTION_REQUEST_STATUS = "ACTION_REQUEST_STATUS"
        private val WAYON_CLOUD_JSON_URL = "${BuildConfig.WAYON_CLOUD_URL}/api/json"
        private val WAYON_CLOUD_TRIPS_URL = "${BuildConfig.WAYON_CLOUD_URL}/api/trips?limit=1000"
        private val WAYON_CLOUD_GMONE_REFRESH_URL = "${BuildConfig.WAYON_CLOUD_URL}/api/gmone/refresh"
        private const val WAYON_CLOUD_AUTO_REFRESH_INTERVAL_MS = 15_000L

        internal fun normalizeTirePressureText(raw: String): String {
            val pressurePattern = Regex("""(?i)(\d+(?:\.\d+)?)\s*kpa""")
            return pressurePattern.replace(raw) { match ->
                val pressure = match.groupValues[1].toDoubleOrNull() ?: return@replace match.value
                val kpa = if (pressure > 0.0 && pressure < 100.0) pressure * 4.0 else pressure
                val formatted = if (kpa % 1.0 == 0.0) {
                    kpa.toLong().toString()
                } else {
                    String.format(Locale.US, "%.1f", kpa).trimEnd('0').trimEnd('.')
                }
                "$formatted kpa"
            }
        }
    }

    private val PREF_KEY_ASKED_BACKGROUND_LOCATION = "ASKED_BACKGROUND_LOCATION"
    private var baseApiUrl: String? = null
    private lateinit var prefs: SharedPreferences
    private lateinit var gmoneAccountStore: GmoneAccountStore
    private var wayonCloudHistoryJson: String? = null
    private var wayonCloudRefreshJob: Job? = null
    private var wayonCloudTripsRefreshJob: Job? = null
    private var wayonCloudAutoRefreshJob: Job? = null
    private var wayonCloudFullHistoryLoaded = false
    private var latestVehicleStatusEpochMs = 0L
    private val wayonAddressCache = ConcurrentHashMap<String, String>()

    private fun carStatusReference(): com.google.firebase.database.DatabaseReference? {
        if (!BuildConfig.FIREBASE_CONFIGURED) return null
        return runCatching {
            Firebase.database(BuildConfig.FIREBASE_DATABASE_URL).reference.child("car_status")
        }.onFailure {
            Log.w("MainActivity", "Firebase is not available", it)
        }.getOrNull()
    }

    // ‼️ [NEW] Public refresh method for Widgets & JS
    fun triggerRefresh() {
        Log.d("MainActivity", "REFRESH_REQUESTED: Triggered internally")
        lastRefreshRequestTime = System.currentTimeMillis()

        if (WayonCloudMode.isEnabled(this)) {
            val key = loadWayonCloudKeyFromPrefs()?.takeIf { it.isNotBlank() } ?: return
            launch(Dispatchers.IO) {
                try {
                    requestWayonGmoneRefresh(key)
                    launch(Dispatchers.Main) {
                        showJsStatus("HYUKLEE-SERVER에 차량 조회를 요청했습니다.", "success")
                        refreshWayonCloudFeed(showResult = false)
                    }
                } catch (error: Exception) {
                    Log.w("MainActivity", "Wayon GMOne refresh request failed", error)
                    launch(Dispatchers.Main) {
                        showJsStatus("차량 조회 요청 실패: ${error.message ?: "unknown"}", "danger")
                    }
                }
            }
            return
        }

        launch(Dispatchers.Main) {
            showJsStatus("차량 데이터 새로고침 요청 중...", "info")
            val db = carStatusReference()
            if (db == null) {
                showJsStatus("Firebase 설정이 없습니다.", "danger")
                return@launch
            }

            // 1. Send Refresh Command
            db.child("cmd_refresh").setValue(System.currentTimeMillis())

            // 2. Fetch latest data
            db.get().addOnSuccessListener {
                val range = it.child("range").getValue(String::class.java) ?: "--"
                val battery = it.child("battery").getValue(String::class.java) ?: "--"
                val batteryLevel = it.child("battery_level").getValue(String::class.java) ?: "--"
                val mileage = it.child("mileage").getValue(String::class.java) ?: "--"
                val fuel = it.child("fuel").getValue(String::class.java) ?: "--"
                val lastUpdate = it.child("last_update").getValue(String::class.java) ?: "--"
                val oil = it.child("oil").getValue(String::class.java) ?: "--"
                val tirePressure = normalizeTirePressureText(
                    it.child("tire_pressure").getValue(String::class.java) ?: "--",
                )
                val rawTirePressureAll = it.child("tire_pressure_all").getValue(String::class.java) ?: "--"
                val tirePressureAll = normalizeTirePressureText(
                    rawTirePressureAll.takeUnless { value -> value.isBlank() || value == "--" } ?: tirePressure,
                )

                runJs("updateCarStatus('$range', '$battery', '$batteryLevel', '$mileage', '$fuel', '$lastUpdate', '$oil', '$tirePressure', '$tirePressureAll')")

                lastFuel = fuel
                lastTime = lastUpdate
                lastOil = oil
                lastTireList = tirePressureAll
                showJsStatus("새로고침 요청 완료", "success")
            }.addOnFailureListener {
                showJsStatus("통신 실패: ${it.message}", "danger")
            }
        }
    }

    // ‼️ [NEW] Helper to update widget storage
    // ‼️ [NEW] Helper to update widget storage
    private fun updateWidgetData(fuel: String?, range: String?, oil: String?, battery: String?, batteryLevel: String?, lastUpdate: String?, odometer: String?, tirePressure: String?) {
        val widgetPrefs = getSharedPreferences("widget_data", Context.MODE_PRIVATE)
        with(widgetPrefs.edit()) {

            // ‼️ Fuel Calculation: Liters -> % (Traverse Tank = 82L)
            var fuelPercent = "--"
            if (fuel != null && fuel != "--") {
                 val cleanFuel = fuel.replace("L", "").replace("%", "").trim()
                 val fuelVal = cleanFuel.toDoubleOrNull()

                 if (fuelVal != null) {
                     // Heuristic: If explicitly "L" or (val > 1 and !contains("%")), treat as Liters
                     // User said "70L corresponds to 85%". 70/82 = 0.853.
                     // If original string had "%", keep it.
                     if (fuel.contains("%")) {
                         fuelPercent = String.format("%.0f", fuelVal)
                     } else {
                         // Assume Liters (Default Traverse Capacity ~82L)
                         // Clamp to 100% just in case
                         var percent = (fuelVal / 82.0) * 100
                         if (percent > 100) percent = 100.0
                         fuelPercent = String.format("%.0f", percent)
                     }
                 } else {
                     fuelPercent = cleanFuel
                 }
            }

            putString("fuel", fuelPercent)
            putString("range", range ?: "--")
            putString("oil", oil ?: "--")
            putString("battery", battery ?: "--")
            putString("batteryLevel", batteryLevel ?: "--")
            putString("lastUpdate", lastUpdate ?: "--:--")
            putString("odometer", odometer ?: "--")
            putString("tire_pressure", tirePressure ?: "--")
            apply()
        }
        val intent = Intent(this, com.example.carcontroller.widget.DashboardWidget::class.java)
        intent.action = "com.example.carcontroller.UPDATE_WIDGET"
        sendBroadcast(intent)
    }

    private lateinit var myWebView: WebView

    private lateinit var locationClient: FusedLocationProviderClient

    // --- 상태 관리 변수 ---
    private var isEngineOn = false
    private var isVentilating = false
    private var isHeatEjecting = false
    private var currentEngineTimerString = ""
    private var currentVentilationTimerString = ""
    private var currentHeatEjectTimerString = ""

    private var currentDrivingTime: String = "00:00:00"
    private var currentDrivingDistance: String = "0.0 km"

    private var isBluetoothConnected = false
    private var isBluetoothConnected_VIRTUAL = false

    private var lastKnownAddress: String = "저장된 위치 없음"
    private var lastKnownTime: String = ""

    private val apiDelay = 5000L
    private var lastApiCallTime: Long = 0
    private val apiCooldownMs = 1000L

    private var isPageLoaded = false
    private var isSetupDialogShowing = false

    // [NEW] Track Refresh Request Time
    private var lastRefreshRequestTime: Long = 0

    private data class StatusTuple(val message: String, val timeString: String, val icon: String, val isActive: Boolean)

    // --- Bluetooth 프로필 프록시 ---
    private var a2dpProfile: BluetoothA2dp? = null
    private var headsetProfile: BluetoothHeadset? = null

    private val bluetoothProfileListener = object : BluetoothProfile.ServiceListener {
        override fun onServiceConnected(profile: Int, proxy: BluetoothProfile) {
            when (profile) {
                BluetoothProfile.A2DP -> {
                    a2dpProfile = proxy as BluetoothA2dp
                    Log.d("MainActivity", "A2DP profile connected")
                }
                BluetoothProfile.HEADSET -> {
                    headsetProfile = proxy as BluetoothHeadset
                    Log.d("MainActivity", "HEADSET profile connected")
                }
            }
            checkBluetoothStatus()
            updateDashboardStatus()
        }

        override fun onServiceDisconnected(profile: Int) {
            when (profile) {
                BluetoothProfile.A2DP -> {
                    a2dpProfile = null
                    Log.d("MainActivity", "A2DP profile disconnected")
                }
                BluetoothProfile.HEADSET -> {
                    headsetProfile = null
                    Log.d("MainActivity", "HEADSET profile disconnected")
                }
            }
            checkBluetoothStatus()
            updateDashboardStatus()
        }
    }

    // === ‼️ 1. 통합 권한 요청 런처 ===
    private val requestAllPermissionsLauncher =
        registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { permissions ->

            if (permissions[Manifest.permission.ACCESS_FINE_LOCATION] == true) {
                askBackgroundLocationPermission()
            } else if (permissions.containsKey(Manifest.permission.ACCESS_FINE_LOCATION)) {
                Toast.makeText(this, "위치 권한이 거부되었습니다.", Toast.LENGTH_SHORT).show()
            }

            if (permissions[Manifest.permission.BLUETOOTH_CONNECT] == true &&
                permissions[Manifest.permission.BLUETOOTH_SCAN] == true
            ) {
                checkBluetoothStatus()
                updateDashboardStatus()
            } else if (permissions.containsKey(Manifest.permission.BLUETOOTH_CONNECT)) {
                Toast.makeText(this, "블루투스 권한이 거부되었습니다.", Toast.LENGTH_SHORT).show()
            }

            if (permissions[Manifest.permission.POST_NOTIFICATIONS] == false) {
                Toast.makeText(this, "알림 권한이 거부되었습니다.", Toast.LENGTH_SHORT).show()
            }
        }

    private val requestBackgroundLocationLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { isGranted: Boolean ->
            if (isGranted) {
                // (백그라운드) 위치 권한 허용됨
            } else {
                Toast.makeText(this, "백그라운드 위치 권한이 필요합니다.", Toast.LENGTH_SHORT).show()
            }
        }

    // (TimerService -> UI)
    private val timerUpdateReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            val isRunning = intent?.getBooleanExtra(TimerService.EXTRA_IS_RUNNING, false) ?: false
            val timeString = intent?.getStringExtra(TimerService.EXTRA_TIME_STRING) ?: ""
            val taskType = intent?.getStringExtra(TimerService.EXTRA_TASK_TYPE) ?: ""

            when (taskType) {
                "ENGINE" -> {
                    isEngineOn = isRunning
                    currentEngineTimerString = if (isRunning) timeString else ""
                    if (isRunning) {
                        runJs("updateEngineUI(true)") // ‼️ (Fix) Restore UI state
                        runJs("updateEngineTimer('$timeString')")
                    } else {
                        runJs("updateEngineUI(false)")
                    }
                }
                "VENTILATION" -> {
                    isVentilating = isRunning
                    currentVentilationTimerString = if (isRunning) timeString else ""
                    runJs("updateVentilationUI($isRunning, '$timeString')")
                }
                "HEAT_EJECT" -> {
                    isHeatEjecting = isRunning
                    currentHeatEjectTimerString = if (isRunning) timeString else ""
                    runJs("updateHeatEjectUI($isRunning, '$timeString')")
                }
            }

            updateDashboardStatus()
        }
    }

    // ‼️ (신규) DrivingService -> UI
    private val drivingUpdateReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            currentDrivingTime = intent?.getStringExtra(DrivingService.EXTRA_DRIVING_TIME) ?: "00:00:00"
            currentDrivingDistance = intent?.getStringExtra(DrivingService.EXTRA_DRIVING_DISTANCE) ?: "0.0 km"

            updateDashboardStatus()
        }
    }

    // ‼️ (New) Firebase Caching Variables
    private var lastFuel: String? = null
    private var lastMileage: String? = null
    private var lastOil: String? = null
    private var lastTireList: String? = null
    private var lastRange: String? = null
    private var lastBattery: String? = null
    private var lastBatteryLevel: String? = null
    private var lastTire: String? = null
    private var lastTime: String? = null
    private var lastRefreshStatus: String = "" // [NEW] Cache for status

    // ‼️ (New) Receiver for Save Completion
    private val drivingSavedReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            Log.d("MainActivity", "Received ACTION_DRIVING_SAVED")
            loadAndShowLocationData()
            showJsStatus("주행 기록이 저장되었습니다.", "success")
            updateDashboardStatus()
        }
    }

    // (Android OS -> UI) 블루투스 이벤트 수신
    @SuppressLint("MissingPermission")
    private val mainActivityBluetoothReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            val action = intent.action
            Log.d("MainActivity", "Bluetooth Event Received: $action")

            if (!hasBluetoothConnectPermission()) {
                Log.w("MainActivity", "BT Receiver: CONNECT permission missing.")
                return
            }

            checkBluetoothStatus()
            updateDashboardStatus()
        }
    }

    // ‼️ (New) Firebase Listener for Car Status
    private val firebaseListener = object : com.google.firebase.database.ValueEventListener {
        override fun onDataChange(snapshot: com.google.firebase.database.DataSnapshot) {
            val fuel = snapshot.child("fuel").getValue(String::class.java) ?: "--"
            val mileage = snapshot.child("mileage").getValue(String::class.java) ?: "--"
            val oil = snapshot.child("oil").getValue(String::class.java) ?: "--"
            val range = snapshot.child("range").getValue(String::class.java) ?: "--"
            val battery = snapshot.child("battery").getValue(String::class.java) ?: "--"
            val batteryLevel = snapshot.child("battery_level").getValue(String::class.java) ?: "--"
            val tirePressure = normalizeTirePressureText(
                snapshot.child("tire_pressure").getValue(String::class.java) ?: "--",
            )
            val rawTirePressureAll = snapshot.child("tire_pressure_all").getValue(String::class.java) ?: "--" // [NEW] Read list
            val tirePressureAll = normalizeTirePressureText(
                rawTirePressureAll.takeUnless { it.isBlank() || it == "--" } ?: tirePressure,
            )
            val lastUpdateStr = snapshot.child("last_update").getValue(String::class.java)
            val refreshStatus = snapshot.child("refresh_status").getValue(String::class.java) ?: ""

            // [NEW] Read Auto Refresh Setting (Default: true)
            val autoRefreshFn = snapshot.child("setting_auto_refresh").getValue(Boolean::class.java) ?: true
            runJs("updateSettingsUI($autoRefreshFn)")

            if (WayonCloudMode.isEnabled(this@MainActivity)) {
                Log.d("MainActivity", "Ignoring Firebase vehicle values while Wayon Cloud mode is active")
                return
            }

            // [NEW] Edge Trigger: Only show when status CHANGES to 'success'
            // This covers both Manual (Button) and Auto (10min) refreshes.
            if (refreshStatus == "success" && lastRefreshStatus != "success") {
                 val displayTime = lastUpdateStr ?: "Just now"
                 showJsStatus("새로고침 및 수집 완료 ($displayTime)", "success")
            }
            lastRefreshStatus = refreshStatus // Update cache

            Log.d("MainActivity", "Firebase Update: Status=$refreshStatus (Prev=$lastRefreshStatus)")

            // Cache data
            lastFuel = fuel
            lastMileage = mileage
            lastOil = oil
            lastTireList = tirePressureAll
            lastRange = range
            lastBattery = battery
            lastBatteryLevel = batteryLevel
            lastTire = tirePressure
            lastTime = lastUpdateStr

            // Send to WebView if loaded
                runJs("updateCarStatus('$range', '$battery', '$batteryLevel', '$mileage', '$fuel', '${lastUpdateStr ?: ""}', '$oil', '$tirePressure', '$tirePressureAll')")

            // ‼️ [NEW] Update Widget data
            // ‼️ [NEW] Update Widget data
            updateWidgetData(fuel, range, oil, battery, batteryLevel, lastUpdateStr, mileage, tirePressureAll)
            WearSync.syncStatus(
                context = this@MainActivity,
                range = range,
                battery = battery,
                batteryLevel = batteryLevel,
                mileage = mileage,
                fuel = fuel,
                lastUpdate = lastUpdateStr ?: "",
                oil = oil,
                tirePressure = tirePressure,
                tirePressureAll = tirePressureAll,
            )
        }

        override fun onCancelled(error: com.google.firebase.database.DatabaseError) {
            Log.w("MainActivity", "Firebase Load Cancelled", error.toException())
        }
    }


    // ======================================================

    @SuppressLint("SetJavaScriptEnabled", "AddJavascriptInterface")


    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // ‼️ (New) Register instance for Static Receiver
        GlobalHelper.registerActivity(this)


        prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        gmoneAccountStore = GmoneAccountStore(this)
        baseApiUrl = loadUrlFromPrefs()
        WearSync.syncApiUrl(this, baseApiUrl)

        locationClient = LocationServices.getFusedLocationProviderClient(this)

        WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG)
        myWebView = findViewById(R.id.webview)
        myWebView.settings.javaScriptEnabled = true
        myWebView.settings.domStorageEnabled = true

        myWebView.addJavascriptInterface(this, "Android")

        myWebView.webChromeClient = object : android.webkit.WebChromeClient() {
            override fun onConsoleMessage(consoleMessage: android.webkit.ConsoleMessage?): Boolean {
                Log.d("WebViewConsole", "${consoleMessage?.message()} -- From line ${consoleMessage?.lineNumber()} of ${consoleMessage?.sourceId()}")
                return true
            }
        }

        myWebView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
                Log.d("MainActivity", "WebView page loaded.")
                isPageLoaded = true
                loadAndShowLocationData() // ‼️ (수정) 함수 이름 변경
                loadWayonCloudKeyFromPrefs()?.takeIf { it.isNotBlank() }?.let { key ->
                    runJs("updateWayonCloudKeyInput(${jsQuote(key)})")
                }
                updateGmoneAccountUi()
                refreshWayonCloudFeed(showResult = false)
                startWayonCloudAutoRefresh()
                updateDashboardStatus()

                // [NEW] Send cached car status on reload
                if (lastFuel != null || lastMileage != null) {
                    val safeFuel = lastFuel ?: "--"
                    val safeMileage = lastMileage ?: "--"
                    val safeOil = lastOil ?: "--"
                    val safeRange = lastRange ?: "--"
                    val safeBat = lastBattery ?: "--"
                    val safeBatLevel = lastBatteryLevel ?: "--"
                    val safeTire = lastTire ?: "--"
                    val safeTireList = lastTireList ?: ""
                    val safeTime = lastTime ?: ""

                    runJs("updateCarStatus('$safeRange', '$safeBat', '$safeBatLevel', '$safeMileage', '$safeFuel', '$safeTime', '$safeOil', '$safeTire', '$safeTireList')")
                }

                if (pendingWidgetAction != null) {
                    Log.d("MainActivity", "Executing pending widget action: $pendingWidgetAction")
                    val action = pendingWidgetAction
                    pendingWidgetAction = null // Clear queue

                    val intent = Intent(action)
                    handleWidgetCommand(intent)
                }

                isSetupComplete()
            }
        }



        myWebView.loadUrl("file:///android_asset/main.html")

        askAllPermissions()

        // TimerService용 브로드캐스트
        LocalBroadcastManager.getInstance(this).registerReceiver(
            timerUpdateReceiver, IntentFilter(TimerService.BROADCAST_TIMER_UPDATE)
        )

        // (신규) DrivingService용 브로드캐스트
        LocalBroadcastManager.getInstance(this).registerReceiver(
            drivingUpdateReceiver, IntentFilter(DrivingService.BROADCAST_DRIVING_UPDATE)
        )
        // ‼️ (New) Reigster Saved Receiver
        LocalBroadcastManager.getInstance(this).registerReceiver(
            drivingSavedReceiver, IntentFilter(DrivingService.ACTION_DRIVING_SAVED)
        )



        // Bluetooth 브로드캐스트 리시버 등록
        val filter = IntentFilter().apply {
            addAction(BluetoothDevice.ACTION_ACL_CONNECTED)
            addAction(BluetoothDevice.ACTION_ACL_DISCONNECTED)
            addAction(BluetoothA2dp.ACTION_CONNECTION_STATE_CHANGED)
            addAction(BluetoothHeadset.ACTION_CONNECTION_STATE_CHANGED)
        }
        registerReceiver(mainActivityBluetoothReceiver, filter)

        carStatusReference()?.addValueEventListener(firebaseListener)


        // Bluetooth 프로필 프록시 요청
        val bluetoothManager = getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
        val adapter = bluetoothManager.adapter
        adapter?.getProfileProxy(this, bluetoothProfileListener, BluetoothProfile.A2DP)
        adapter?.getProfileProxy(this, bluetoothProfileListener, BluetoothProfile.HEADSET)

        // ‼️ [NEW] Handle Widget Command on Launch
        handleWidgetCommand(intent)
    }

    override fun onResume() {
        super.onResume()
        isActivityVisible = true
        requestServiceStatusUpdate()

        if (isSetupComplete()) {
            checkBluetoothStatus()
            updateDashboardStatus()
            loadAndShowLocationData() // ‼️ (수정) 함수 이름 변경
        }
        refreshWayonCloudFeed(showResult = false)
        startWayonCloudAutoRefresh()
    }

    override fun onPause() {
        super.onPause()
        isActivityVisible = false
        stopWayonCloudAutoRefresh()
        runJs("stopWayonLiveView()")
    }

    override fun onDestroy() {
        stopWayonCloudAutoRefresh()
        wayonCloudRefreshJob?.cancel()
        wayonCloudRefreshJob = null
        wayonCloudTripsRefreshJob?.cancel()
        wayonCloudTripsRefreshJob = null
        LocalBroadcastManager.getInstance(this).unregisterReceiver(timerUpdateReceiver)
        LocalBroadcastManager.getInstance(this).unregisterReceiver(drivingUpdateReceiver)
        LocalBroadcastManager.getInstance(this).unregisterReceiver(drivingSavedReceiver)

        unregisterReceiver(mainActivityBluetoothReceiver)
        // unregisterReceiver(widgetCommandReceiver) Removal

        // ‼️ Unregister GlobalHelper
        GlobalHelper.unregisterActivity()


        // Bluetooth 프로필 프록시 해제
        try {
            val bluetoothManager = getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
            val adapter = bluetoothManager.adapter
            a2dpProfile?.let { adapter?.closeProfileProxy(BluetoothProfile.A2DP, it) }
            headsetProfile?.let { adapter?.closeProfileProxy(BluetoothProfile.HEADSET, it) }
        } catch (e: Exception) {
            e.printStackTrace()
        }

        super.onDestroy()
    }

    // --- 헬퍼 함수 ---

    private fun isSetupComplete(): Boolean {
        if (!isPageLoaded) return false
        if (isSetupDialogShowing) return false

        val savedMacAddress = prefs.getString(PREF_KEY_MAC_ADDRESS, null)
        if (savedMacAddress == null) {
            runJs("switchTab('tab-settings')")

            launch(Dispatchers.Main) {
                isSetupDialogShowing = true
                AlertDialog.Builder(this@MainActivity)
                    .setTitle("필수 설정")
                    .setMessage("앱을 정상적으로 사용하려면, 페어링 목록에서 차량 선택 버튼을 눌러 'myChevrolet' 기기를 등록하세요.")
                    .setPositiveButton("확인", null)
                    .setCancelable(false)
                    .setOnDismissListener {
                        isSetupDialogShowing = false
                    }
                    .show()
            }
            return false
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_BACKGROUND_LOCATION) != PackageManager.PERMISSION_GRANTED) {
                if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED) {
                    val alreadyAsked = prefs.getBoolean(PREF_KEY_ASKED_BACKGROUND_LOCATION, false)

                    if (!alreadyAsked) {
                        launch(Dispatchers.Main) {
                            isSetupDialogShowing = true
                            AlertDialog.Builder(this@MainActivity)
                                .setTitle("필수 설정")
                                .setMessage("자동 주차 위치 저장을 위해, 앱의 위치 권한을 '항상 허용'으로 변경해야 합니다. 앱 설정 화면으로 이동합니다.")
                                .setPositiveButton("권한 설정하기") { _, _ ->
                                    prefs.edit().putBoolean(PREF_KEY_ASKED_BACKGROUND_LOCATION, true).apply()

                                    val intent = Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
                                    val uri = Uri.fromParts("package", packageName, null)
                                    intent.data = uri
                                    startActivity(intent)
                                }
                                .setNegativeButton("나중에") { _, _ ->
                                    prefs.edit().putBoolean(PREF_KEY_ASKED_BACKGROUND_LOCATION, true).apply()
                                }
                                .setCancelable(false)
                                .setOnDismissListener {
                                    isSetupDialogShowing = false
                                }
                                .show()
                        }
                    }
                }
            }
        }

        return true
    }


    private fun requestServiceStatusUpdate() {
        val intent = Intent(this, TimerService::class.java).apply {
            action = ACTION_REQUEST_STATUS
        }
        startService(intent)
    }

    private fun runJs(script: String) {
        val callName = script.substringBefore('(').take(80)
        if (!isPageLoaded) {
            Log.w("MainActivity", "Page not loaded, skipping JS call: $callName")
            return
        }

        launch {
            Log.d("MainActivity", "Running JS: $callName")
            myWebView.loadUrl("javascript:$script")
        }
    }

    // (통합 권한 요청)
    private fun askAllPermissions() {
        val permissionsToRequest = mutableListOf<String>()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(Manifest.permission.BLUETOOTH_CONNECT)
            }
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_SCAN) != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(Manifest.permission.BLUETOOTH_SCAN)
            }
        }
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            permissionsToRequest.add(Manifest.permission.ACCESS_FINE_LOCATION)
        }

        if (permissionsToRequest.isNotEmpty()) {
            requestAllPermissionsLauncher.launch(permissionsToRequest.toTypedArray())
        }
    }

    private fun askBackgroundLocationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_BACKGROUND_LOCATION) != PackageManager.PERMISSION_GRANTED) {
                requestBackgroundLocationLauncher.launch(Manifest.permission.ACCESS_BACKGROUND_LOCATION)
            }
        }
    }

    // --- 권한 헬퍼 ---

    private fun hasBluetoothConnectPermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED
        } else {
            true
        }
    }

    @SuppressLint("MissingPermission")
    private fun hasBluetoothScanPermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED &&
                    ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_SCAN) == PackageManager.PERMISSION_GRANTED)
        } else {
            (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED)
        }
    }

    // ======================================

    @SuppressLint("MissingPermission")
    private fun checkBluetoothStatus() {
        if (!hasBluetoothScanPermission()) {
            isBluetoothConnected = false
            Log.w("MainActivity", "checkBluetoothStatus: BT/Location Permissions not granted.")
            return
        }

        try {
            val bluetoothManager = getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
            val adapter = bluetoothManager.adapter ?: run {
                isBluetoothConnected = false
                Log.w("MainActivity", "checkBluetoothStatus: Adapter null.")
                return
            }

            if (!adapter.isEnabled) {
                isBluetoothConnected = false
                Log.w("MainActivity", "checkBluetoothStatus: Adapter disabled.")
                return
            }

            val savedMacAddress = prefs.getString(PREF_KEY_MAC_ADDRESS, null)

            if (savedMacAddress == null) {
                Log.w("MainActivity", "checkBluetoothStatus: MAC Address not saved. Please use 'Select Car' button in settings.")
                if (isBluetoothConnected) {
                    isBluetoothConnected = false
                    Log.d("MainActivity", "Bluetooth DISCONNECTED (MAC address missing). Stopping DrivingService & Saving location.")
                    launch {
                        stopDrivingServiceAndSaveLocation()
                    }
                }
                return
            }

            val gattDevices = bluetoothManager.getConnectedDevices(BluetoothProfile.GATT)
            val a2dpDevices = a2dpProfile?.connectedDevices ?: emptyList()
            val headsetDevices = headsetProfile?.connectedDevices ?: emptyList()

            val allConnectedDevices = (gattDevices + a2dpDevices + headsetDevices).toSet()

            val previousState = isBluetoothConnected

            isBluetoothConnected = allConnectedDevices.any { it.address == savedMacAddress }

            if (!previousState && isBluetoothConnected) {
                Log.d("MainActivity", "Bluetooth just CONNECTED. Cancelling remote tasks & Starting DrivingService.")
                cancelAllRemoteTasksOnBtConnect()
                startDrivingService()
            } else if (previousState && !isBluetoothConnected) {
                Log.d("MainActivity", "Bluetooth just DISCONNECTED. Stopping DrivingService & Saving location.")
                launch {
                    stopDrivingServiceAndSaveLocation()
                }
            }

            if (previousState != isBluetoothConnected) {
                Log.d("MainActivity", "checkBluetoothStatus: State CHANGED to $isBluetoothConnected")
            }

        } catch (e: Exception) {
            e.printStackTrace()
            isBluetoothConnected = false
        }
    }

    private fun cancelAllRemoteTasksOnBtConnect() {
        if (isEngineOn) {
            Log.d("MainActivity", "BT Connected: Stopping Engine timer.")
            isEngineOn = false
            stopTimerService("ENGINE")
            runJs("updateEngineUI(false)")
        }

        if (isVentilating) {
            Log.d("MainActivity", "BT Connected: Stopping Ventilation macro.")
            isVentilating = false
            stopTimerService("VENTILATION")
            runJs("updateVentilationUI(false, '')")
            setExtrasButtonsDisabled(false)
        }

        if (isHeatEjecting) {
            Log.d("MainActivity", "BT Connected: Stopping Heat Eject macro timer.")
            isHeatEjecting = false
            stopTimerService("HEAT_EJECT")
            runJs("updateHeatEjectUI(false, '')")
            setExtrasButtonsDisabled(false)
        }
    }

    private fun updateDashboardStatus() {
        val isBtOn = isBluetoothConnected || isBluetoothConnected_VIRTUAL

        val (message, timeString, icon, isActive) = when {
            isBtOn -> StatusTuple(
                "주행중",
                "$currentDrivingDistance|$currentDrivingTime",
                "car",
                true
            )
            isHeatEjecting -> StatusTuple("열 배출 모드 실행 중", "($currentHeatEjectTimerString)", "temperature-high", true)
            isVentilating -> StatusTuple("환기 모드 실행 중", "($currentVentilationTimerString)", "wind", true)
            isEngineOn -> StatusTuple("시동 켜짐", "($currentEngineTimerString 남음)", "power-off", true)
            else -> StatusTuple(lastKnownAddress, lastKnownTime, "map-marker-alt", false)
        }
        runJs("updateDashboardStatus('$message', '$timeString', '$icon', $isActive, $isBtOn)")
    }

    private fun setButtonFeedback(buttonId: String, state: String, cmdKey: String? = null) {
        val commandArg = cmdKey?.let { "'$it'" } ?: "null"
        runJs("setButtonFeedback('$buttonId', '$state', $commandArg)")
    }

    private fun setExtrasButtonsDisabled(disabled: Boolean) {
        runJs("setExtrasButtonsDisabled($disabled)")
    }

    private fun showJsStatus(message: String, type: String, duration: Long = 2000) {
        runJs("showStatus('$message', '$type', $duration)")
    }

    private fun saveUrlToPrefs(url: String) {
        prefs.edit().putString(PREF_KEY_API_URL, url).apply()
    }

    private fun loadUrlFromPrefs(): String? {
        return prefs.getString(PREF_KEY_API_URL, null)
    }

    private fun saveWayonCloudKeyToPrefs(key: String) {
        wayonCloudHistoryJson = null
        wayonCloudFullHistoryLoaded = false
        prefs.edit().putString(PREF_KEY_WAYON_CLOUD_KEY, key).apply()
        if (WayonCloudMode.isEnabled(this)) {
            WayonCloudMode.clearLocalTrackingState(this)
            stopService(Intent(this, DrivingService::class.java))
        }
    }

    private fun loadWayonCloudKeyFromPrefs(): String? =
        prefs.getString(PREF_KEY_WAYON_CLOUD_KEY, null)

    private fun updateGmoneAccountUi(message: String? = null) {
        val account = gmoneAccountStore.account()
        runJs(
            "updateGmoneAccountState(${account != null}, ${jsQuote(account?.email)}, " +
                "${jsQuote(message ?: if (account != null) "로그인됨" else "로그인 필요")}, false)",
        )
    }

    private fun jsQuote(value: String?): String = JSONObject.quote(value.orEmpty())

    private fun startWayonCloudAutoRefresh() {
        if (!isActivityVisible || !isPageLoaded || loadWayonCloudKeyFromPrefs().isNullOrBlank()) return
        if (wayonCloudAutoRefreshJob?.isActive == true) return

        wayonCloudAutoRefreshJob = launch {
            while (isActivityVisible && isPageLoaded && !loadWayonCloudKeyFromPrefs().isNullOrBlank()) {
                refreshWayonCloudFeed(showResult = false)
                delay(WAYON_CLOUD_AUTO_REFRESH_INTERVAL_MS)
            }
        }
    }

    private fun stopWayonCloudAutoRefresh() {
        wayonCloudAutoRefreshJob?.cancel()
        wayonCloudAutoRefreshJob = null
    }

    private fun refreshWayonCloudFeed(showResult: Boolean) {
        val key = loadWayonCloudKeyFromPrefs()?.takeIf { it.isNotBlank() } ?: return
        if (wayonCloudRefreshJob?.isActive == true) return

        wayonCloudRefreshJob = launch(Dispatchers.IO) {
            try {
                val parsed = WayonCloudFeedParser.parse(fetchWayonCloudGet(WAYON_CLOUD_JSON_URL, key))
                    .withLatestTripLocationFallback()
                val stateLocation = resolveWayonAddress(
                    parsed.state?.latitude,
                    parsed.state?.longitude,
                    "위치 정보 없음",
                )
                val feed = withResolvedWayonAddresses(parsed)
                launch(Dispatchers.Main) {
                    applyWayonCloudFeed(feed, stateLocation)
                    if (showResult) showJsStatus("Wayon Cloud 데이터를 불러왔습니다.", "success")
                }
            } catch (error: Exception) {
                Log.w("MainActivity", "Wayon Cloud refresh failed", error)
                launch(Dispatchers.Main) {
                    runJs("markWayonCloudUnavailable(${jsQuote("Wayon Cloud 정보 수신 실패")})")
                    runJs("updateWayonDriveUnavailable(${jsQuote("Cloud 연결 실패")})")
                    if (showResult) {
                        showJsStatus("Wayon Cloud 연결 실패: ${error.message ?: "unknown"}", "danger", 4000)
                    }
                }
            }
        }
    }

    private fun refreshWayonCloudTrips(showResult: Boolean) {
        val key = loadWayonCloudKeyFromPrefs()?.takeIf { it.isNotBlank() } ?: return
        if (wayonCloudTripsRefreshJob?.isActive == true) return

        wayonCloudTripsRefreshJob = launch(Dispatchers.IO) {
            try {
                val feed = withResolvedWayonAddresses(
                    WayonCloudFeedParser.parse(fetchWayonCloudGet(WAYON_CLOUD_TRIPS_URL, key)),
                )
                val historyJson = feed.historyJson
                launch(Dispatchers.Main) {
                    wayonCloudHistoryJson = historyJson
                    wayonCloudFullHistoryLoaded = true
                    runJs("onWayonCloudHistoryUpdated()")
                    if (showResult) showJsStatus("전체 주행 이력을 불러왔습니다.", "success")
                }
            } catch (error: Exception) {
                Log.w("MainActivity", "Wayon Cloud trips refresh failed", error)
                launch(Dispatchers.Main) {
                    runJs("onWayonCloudHistoryUpdated()")
                    if (showResult) {
                        showJsStatus("주행 이력 연결 실패: ${error.message ?: "unknown"}", "danger", 4000)
                    }
                }
            }
        }
    }

    private fun withResolvedWayonAddresses(feed: WayonCloudFeed): WayonCloudFeed = feed.copy(
        history = feed.history.map { trip ->
            trip.copy(
                startAddress = resolveWayonAddress(
                    trip.startLatitude,
                    trip.startLongitude,
                    trip.startAddress,
                ),
                endAddress = resolveWayonAddress(
                    trip.endLatitude,
                    trip.endLongitude,
                    trip.endAddress,
                ),
            )
        },
    )

    @Suppress("DEPRECATION")
    private fun resolveWayonAddress(latitude: Double?, longitude: Double?, fallback: String): String {
        if (latitude == null || longitude == null) return fallback
        val cacheKey = String.format(Locale.US, "%.5f,%.5f", latitude, longitude)
        wayonAddressCache[cacheKey]?.let { return it }

        val resolved = try {
            Geocoder(this, Locale.KOREAN)
                .getFromLocation(latitude, longitude, 1)
                ?.firstOrNull()
                ?.getAddressLine(0)
                ?.replace("대한민국", "")
                ?.trim()
                ?.takeIf { it.isNotBlank() }
                ?: fallback
        } catch (error: Exception) {
            Log.w("MainActivity", "Wayon Cloud address lookup failed", error)
            fallback
        }
        wayonAddressCache[cacheKey] = resolved
        return resolved
    }

    private fun fetchWayonCloudGet(url: String, key: String): String {
        val connection = URL(url).openConnection() as HttpsURLConnection
        connection.requestMethod = "GET"
        connection.useCaches = false
        connection.connectTimeout = 10_000
        connection.readTimeout = 10_000
        connection.setRequestProperty("Authorization", "Bearer $key")
        connection.setRequestProperty("Accept", "application/json")
        connection.setRequestProperty("Cache-Control", "no-cache")
        connection.setRequestProperty("User-Agent", "WayonAndroid/1.0")

        return try {
            val responseCode = connection.responseCode
            if (responseCode !in 200..299) throw IOException("HTTP $responseCode")
            BufferedReader(InputStreamReader(connection.inputStream, Charsets.UTF_8)).use { it.readText() }
        } finally {
            connection.disconnect()
        }
    }

    private fun requestWayonGmoneRefresh(key: String) {
        val connection = URL(WAYON_CLOUD_GMONE_REFRESH_URL).openConnection() as HttpsURLConnection
        connection.requestMethod = "POST"
        connection.doOutput = true
        connection.useCaches = false
        connection.connectTimeout = 10_000
        connection.readTimeout = 10_000
        connection.setRequestProperty("Authorization", "Bearer $key")
        connection.setRequestProperty("Content-Type", "application/json")
        connection.setRequestProperty("Accept", "application/json")
        return try {
            connection.outputStream.use { it.write("{}".toByteArray(Charsets.UTF_8)) }
            val responseCode = connection.responseCode
            if (responseCode !in 200..299) throw IOException("HTTP $responseCode")
            Unit
        } finally {
            connection.disconnect()
        }
    }

    private fun applyWayonCloudFeed(feed: WayonCloudFeed, stateLocationText: String) {
        if (!wayonCloudFullHistoryLoaded) wayonCloudHistoryJson = feed.historyJson
        runJs("updateWayonCloudSnapshots(${jsQuote(feed.snapshotsJson)})")
        applyWayonVehicleStatus(feed.vehicleStatus)

        val state = feed.state
        if (state == null) {
            runJs("markWayonCloudUnavailable(${jsQuote("Wayon Cloud 상태 정보 없음")})")
            runJs("updateWayonDriveUnavailable(${jsQuote("상태 정보 없음")})")
            runJs("onWayonCloudDataUpdated()")
            return
        }

        val voltage = state.voltageV?.let { String.format(Locale.US, "%.1f", it) } ?: "--"
        val gpsTime = state.gpsUpdatedAtDisplay
        lastKnownAddress = stateLocationText
        lastKnownTime = gpsTime

        if (state.latitude != null && state.longitude != null) {
            prefs.edit()
                .putString(PREF_KEY_LOCATION_LAT, state.latitude.toString())
                .putString(PREF_KEY_LOCATION_LON, state.longitude.toString())
                .putString(PREF_KEY_LOCATION_TIME, gpsTime)
                .putString(DrivingService.PREF_KEY_LOCATION_ADDRESS, stateLocationText)
                .apply()
        }

        val latitude = state.latitude?.let { String.format(Locale.US, "%.6f", it) } ?: "null"
        val longitude = state.longitude?.let { String.format(Locale.US, "%.6f", it) } ?: "null"
        runJs(
            "updateWayonCloudState(${jsQuote(voltage)}, ${jsQuote(gpsTime)}, " +
                "${jsQuote(if (state.onroad) "ONROAD" else "OFFROAD")}, ${jsQuote(state.speedText)}, " +
                "$latitude, $longitude, ${jsQuote(stateLocationText)})",
        )

        val latestTrip = feed.latestTrip
        runJs(
            "updateSavedLocation(${jsQuote(stateLocationText)}, ${jsQuote(gpsTime)}, " +
                "${jsQuote(latestTrip?.distance ?: "-- km")}, " +
                "${jsQuote(latestTrip?.duration ?: "--:--:--")}, " +
                "${jsQuote(latestTrip?.avgSpeed ?: "-- km/h")}, " +
                "${jsQuote(latestTrip?.topSpeed ?: "-- km/h")})",
        )

        val telemetry = state.rawJson ?: JSONObject()
        telemetry.put("cloudUpdatedAt", state.updatedAt)
        telemetry.put("cloudLatitude", state.latitude)
        telemetry.put("cloudLongitude", state.longitude)
        telemetry.put("cloudVoltageV", state.voltageV)
        telemetry.put("cloudSpeedMps", state.speedMps)
        state.doorLocked?.let { telemetry.put("cloudDoorLocked", it) }
        state.doorLockUpdatedAt?.let { telemetry.put("cloudDoorLockUpdatedAt", it) }
        runJs("updateWayonDriveState(${jsQuote(telemetry.toString())})")
        runJs("onWayonCloudDataUpdated()")
    }

    private fun applyWayonVehicleStatus(vehicleStatus: WayonVehicleStatus?) {
        val status = vehicleStatus ?: return
        val data = status.data
        val statusEpochMs = parseVehicleStatusEpoch(
            data.optString("last_update", "").takeIf { it.isNotBlank() } ?: status.updatedAt,
        )
        if (statusEpochMs != null && statusEpochMs + 1_000L < latestVehicleStatusEpochMs) {
            Log.d(
                "MainActivity",
                "Skipped older vehicle status from ${status.source}; latest=$latestVehicleStatusEpochMs candidate=$statusEpochMs",
            )
            return
        }
        fun value(name: String): String = data.optString(name, "")
            .takeUnless { it.isBlank() || it.equals("null", ignoreCase = true) }
            ?: "--"

        val range = value("range")
        val battery = value("battery")
        val batteryLevel = value("battery_level")
        val mileage = value("mileage")
        val fuel = value("fuel")
        val oil = value("oil")
        val tirePressure = normalizeTirePressureText(value("tire_pressure"))
        val tirePressureAll = normalizeTirePressureText(
            value("tire_pressure_all").takeUnless { it == "--" } ?: tirePressure,
        )
        val lastUpdate = value("last_update").takeUnless { it == "--" }
            ?: status.updatedAt.orEmpty()

        runJs(
            "updateCarStatus(${jsQuote(range)}, ${jsQuote(battery)}, ${jsQuote(batteryLevel)}, " +
                "${jsQuote(mileage)}, ${jsQuote(fuel)}, ${jsQuote(lastUpdate)}, ${jsQuote(oil)}, " +
                "${jsQuote(tirePressure)}, ${jsQuote(tirePressureAll)})",
        )

        lastFuel = fuel
        lastMileage = mileage
        lastOil = oil
        lastTireList = tirePressureAll
        lastRange = range
        lastBattery = battery
        lastBatteryLevel = batteryLevel
        lastTire = tirePressure
        lastTime = lastUpdate
        updateWidgetData(fuel, range, oil, battery, batteryLevel, lastUpdate, mileage, tirePressureAll)
        WearSync.syncStatus(
            context = this,
            range = range,
            battery = battery,
            batteryLevel = batteryLevel,
            mileage = mileage,
            fuel = fuel,
            lastUpdate = lastUpdate,
            oil = oil,
            tirePressure = tirePressure,
            tirePressureAll = tirePressureAll,
        )
        if (statusEpochMs != null) {
            latestVehicleStatusEpochMs = maxOf(latestVehicleStatusEpochMs, statusEpochMs)
        }
        Log.d("MainActivity", "Applied vehicle status from ${status.source}; stale=${status.stale}")
    }

    private fun parseVehicleStatusEpoch(value: String?): Long? {
        val text = value?.trim().orEmpty()
        if (text.isBlank()) return null
        val formats = listOf(
            "yyyy-MM-dd'T'HH:mm:ss.SSSXXX" to TimeZone.getTimeZone("UTC"),
            "yyyy-MM-dd'T'HH:mm:ssXXX" to TimeZone.getTimeZone("UTC"),
            "yyyy-MM-dd HH:mm:ss" to TimeZone.getTimeZone("Asia/Seoul"),
        )
        for ((pattern, timeZone) in formats) {
            val parsed = runCatching {
                SimpleDateFormat(pattern, Locale.US).apply {
                    isLenient = false
                    this.timeZone = timeZone
                }.parse(text)
            }.getOrNull()
            if (parsed != null) return parsed.time
        }
        return null
    }

    private fun checkApiCooldown(buttonId: String?): Boolean {
        if (baseApiUrl.isNullOrEmpty()) {
            launch(Dispatchers.Main) {
                runJs("switchTab('tab-settings')")
                runJs("populateApiUrl('(API 키 없음)')")
                showJsStatus("API 키를 먼저 입력하고 저장하세요.", "danger", 3000)
            }
            return false
        }

        val currentTime = SystemClock.elapsedRealtime()
        if (currentTime - lastApiCallTime < apiCooldownMs) {
            launch(Dispatchers.Main) {
                runJs("updateDashboardStatus('명령이 너무 빠릅니다.', '', 'exclamation-triangle', true, false)")

                if (buttonId != null) {
                    setButtonFeedback(buttonId, "cooldown")
                }

                delay(2000)
                updateDashboardStatus()
            }
            return false
        }
        lastApiCallTime = currentTime
        return true
    }

    // --- 네이티브 API 호출 ---
    private suspend fun sendCommandInternal(cmd: String): Boolean {
        if (baseApiUrl.isNullOrEmpty()) {
            launch(Dispatchers.Main) {
                showJsStatus("API 키가 설정되지 않았습니다.", "danger")
            }
            return false
        }

        val fullUrl = "$baseApiUrl&cmd=$cmd"
        return try {
            kotlinx.coroutines.withContext(Dispatchers.IO) {
                var connection: HttpsURLConnection? = null
                try {
                    val url = URL(fullUrl)
                    connection = (url.openConnection() as HttpsURLConnection).apply {
                        requestMethod = "GET"
                        connectTimeout = 5000
                        readTimeout = 5000
                    }
                    connection.responseCode in 200..299
                } finally {
                    connection?.disconnect()
                }
            }
        } catch (e: IOException) {
            e.printStackTrace()
            false
        }
    }

    // --- 서비스 시작/중지 ---
    private fun startTimerService(taskType: String, duration: Long) {
        if (baseApiUrl.isNullOrEmpty()) {
            launch(Dispatchers.Main) {
                showJsStatus("API 키가 설정되지 않았습니다.", "danger")
            }
            return
        }

        val intent = Intent(this@MainActivity, TimerService::class.java).apply {
            action = TimerService.ACTION_START_TIMER
            putExtra("TIMER_DURATION", duration)
            putExtra("TASK_TYPE", taskType)
            putExtra("BASE_API_URL", baseApiUrl)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
    }

    private fun stopTimerService(taskType: String) {
        val intent = Intent(this@MainActivity, TimerService::class.java).apply {
            action = TimerService.ACTION_STOP_TIMER
            putExtra("TASK_TYPE", taskType)
        }
        startService(intent)
    }

    private fun startDrivingService() {
        if (WayonCloudMode.isEnabled(this)) {
            WayonCloudMode.clearLocalTrackingState(this)
            stopService(Intent(this, DrivingService::class.java))
            Log.d("MainActivity", "Wayon Cloud enabled; skipping local driving service.")
            return
        }

        val intent = Intent(this, DrivingService::class.java).apply {
            action = DrivingService.ACTION_START_DRIVING
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
    }

    private fun stopDrivingService() {
        val intent = Intent(this, DrivingService::class.java).apply {
            action = DrivingService.ACTION_STOP_DRIVING
        }
        startService(intent)
    }

    // ‼️ (신규) 중지 -> 딜레이 -> UI 갱신을 위한 헬퍼
    private fun stopDrivingServiceAndSaveLocation() {
        if (WayonCloudMode.isEnabled(this)) {
            stopService(Intent(this, DrivingService::class.java))
            refreshWayonCloudFeed(showResult = false)
            return
        }

        stopDrivingService() // 1. 중지 명령 (DrivingService가 비동기로 저장 시작)

        showJsStatus("주행 기록 저장 중...", "warning")

        // 3. ‼️ Fallback: If broadcast doesn't arrive in 3s, reload anyway
        launch {
             delay(3000)
             loadAndShowLocationData()
        }
    }

    // ‼️ (삭제) saveLastKnownLocation() 함수
    // (이 로직은 DrivingService.saveDrivingSessionAndLocation로 이동했음)

    // ‼️ (수정) 함수 이름 및 로직 변경
    private fun convertLocationToAddress(latString: String, lonString: String, timeString: String,
                                         dist: String, driveTime: String, avgSpeed: String, topSpeed: String) {
        launch(Dispatchers.IO) {
            val addressText = try {
                val geocoder = Geocoder(this@MainActivity, Locale.KOREAN)
                val lat = latString.toDouble()
                val lon = lonString.toDouble()

                @Suppress("DEPRECATION")
                val addresses: MutableList<Address>? = geocoder.getFromLocation(lat, lon, 1)

                if (addresses != null && addresses.isNotEmpty()) {
                    addresses[0].getAddressLine(0)
                } else {
                    "주소를 찾을 수 없음"
                }
            } catch (e: IOException) {
                e.printStackTrace()
                "주소 변환 실패"
            }

            // UI 스레드로 복귀하여 HTML 업데이트
            launch(Dispatchers.Main) {
                lastKnownAddress = addressText
                lastKnownTime = "($timeString)"

                // ‼️ (수정) 6개 인자 모두 전달
                runJs("updateSavedLocation('$addressText', '($timeString)', '$dist', '$driveTime', '$avgSpeed', '$topSpeed')")
                updateDashboardStatus()
            }
        }
    }

    // ‼️ (수정) 함수 이름 및 로직 변경
    private fun loadAndShowLocationData() {
        // 1. 모든 키를 SharedPreferences에서 읽어옵니다.
        val lat = prefs.getString(PREF_KEY_LOCATION_LAT, null)
        val lon = prefs.getString(PREF_KEY_LOCATION_LON, null)
        val time = prefs.getString(PREF_KEY_LOCATION_TIME, null)

        val dist = prefs.getString(DrivingService.PREF_KEY_LAST_DRIVE_DIST, "-- km")!!
        val driveTime = prefs.getString(DrivingService.PREF_KEY_LAST_DRIVE_TIME, "--:--:--")!!
        val avgSpeed = prefs.getString(DrivingService.PREF_KEY_LAST_DRIVE_AVG_SPEED, "-- km/h")!!
        val topSpeed = prefs.getString(DrivingService.PREF_KEY_LAST_DRIVE_TOP_SPEED, "-- km/h")!!

        if (lat != null && lon != null && time != null) {
            // (주소 변환은 비동기로 실행됨)
            runJs("updateSavedLocation('주소 변환 중...', '($time)', '$dist', '$driveTime', '$avgSpeed', '$topSpeed')")
            convertLocationToAddress(lat, lon, time, dist, driveTime, avgSpeed, topSpeed)
        } else {
            // (기본값 로드)
            lastKnownAddress = "저장된 위치 없음"
            lastKnownTime = ""
            runJs("updateSavedLocation(lastKnownAddress, lastKnownTime, '$dist', '$driveTime', '$avgSpeed', '$topSpeed')")
            updateDashboardStatus()
        }
    }
    // ============================================

    // --- WebView 인터페이스 ---
    // inner class WebAppInterface { // Merged into MainActivity

        @JavascriptInterface
        fun saveApiUrl(dirtyUrl: String) {
            val requiredPrefix = "https://mp.gmone.co.kr/api?"

            if (!dirtyUrl.startsWith(requiredPrefix)) {
                showJsStatus("잘못된 URL입니다. $requiredPrefix 로 시작해야 합니다.", "danger", 4000)
                return
            }

            val cleanUrl = if (dirtyUrl.contains("&cmd=")) {
                dirtyUrl.substringBefore("&cmd=")
            } else {
                dirtyUrl
            }

            baseApiUrl = cleanUrl
            saveUrlToPrefs(cleanUrl)
            WearSync.syncApiUrl(this@MainActivity, cleanUrl)

            showJsStatus("API 키가 성공적으로 저장되었습니다.", "success")
            runJs("updateApiUrlInput('$cleanUrl')")
        }

        @JavascriptInterface
        fun saveWayonCloudKey(rawKey: String) {
            val cleanKey = rawKey.trim()
            if (cleanKey.isEmpty()) {
                showJsStatus("Wayon Cloud Key를 입력하세요.", "danger", 3000)
                return
            }

            saveWayonCloudKeyToPrefs(cleanKey)
            showJsStatus("Wayon Cloud Key가 저장되었습니다.", "success")
            runJs("updateWayonCloudKeyInput(${jsQuote(cleanKey)})")
            refreshWayonCloudFeed(showResult = true)
            startWayonCloudAutoRefresh()
        }

        @JavascriptInterface
        fun loadInitialApiUrl() {
            val savedUrl = loadUrlFromPrefs()
            if (savedUrl.isNullOrEmpty()) {
                runJs("populateApiUrl('(API 키 없음)')")
            } else {
                runJs("updateApiUrlInput(${jsQuote(savedUrl)})")
            }

            val savedWayonKey = loadWayonCloudKeyFromPrefs()
            if (savedWayonKey.isNullOrEmpty()) {
                runJs("populateWayonCloudKey('(Wayon Cloud Key 없음)')")
            } else {
                runJs("updateWayonCloudKeyInput(${jsQuote(savedWayonKey)})")
            }
            updateGmoneAccountUi()
        }

        @JavascriptInterface
        fun loginGmone(rawEmail: String, password: String) {
            val email = rawEmail.trim()
            if (!android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches() || password.isBlank()) {
                showJsStatus("멀티팩 아이디와 비밀번호를 확인하세요.", "danger", 3000)
                return
            }
            runJs("updateGmoneAccountState(false, ${jsQuote(email)}, ${jsQuote("로그인 확인 중")}, true)")
            launch(Dispatchers.IO) {
                try {
                    val result = GmoneAccountClient.login(email, password)
                    gmoneAccountStore.save(email, password)
                    launch(Dispatchers.Main) {
                        updateGmoneAccountUi("로그인됨 · 차량 ${result.vehicleCount}대")
                        showJsStatus("멀티팩 계정에 로그인했습니다.", "success")
                    }
                } catch (error: Exception) {
                    Log.w("GmoneAccount", "GMOne login failed: ${error.message}")
                    launch(Dispatchers.Main) {
                        runJs(
                            "updateGmoneAccountState(false, ${jsQuote(email)}, " +
                                "${jsQuote(error.message ?: "로그인 실패")}, false)",
                        )
                        showJsStatus(error.message ?: "멀티팩 로그인에 실패했습니다.", "danger", 4000)
                    }
                }
            }
        }

        @JavascriptInterface
        fun logoutGmone() {
            gmoneAccountStore.clear()
            updateGmoneAccountUi("로그아웃됨")
            showJsStatus("멀티팩 계정에서 로그아웃했습니다.", "success")
        }

        @JavascriptInterface
        fun refreshGmoneAccount() {
            val account = gmoneAccountStore.account()
            val password = gmoneAccountStore.password()
            if (account == null || password.isNullOrBlank()) {
                updateGmoneAccountUi("다시 로그인해 주세요")
                showJsStatus("멀티팩 로그인이 필요합니다.", "danger")
                return
            }
            runJs(
                "updateGmoneAccountState(true, ${jsQuote(account.email)}, " +
                    "${jsQuote("차량 조회 중")}, true)",
            )
            launch(Dispatchers.IO) {
                try {
                    val result = GmoneAccountClient.fetchVehicleStatus(account.email, password)
                    launch(Dispatchers.Main) {
                        applyWayonVehicleStatus(
                            WayonVehicleStatus(
                                source = "gmone-direct-android",
                                updatedAt = result.updatedAt,
                                stale = false,
                                data = result.data,
                            ),
                        )
                        updateGmoneAccountUi("차량 조회 완료")
                        showJsStatus("멀티팩 차량 정보를 불러왔습니다.", "success")
                    }
                } catch (error: Exception) {
                    Log.w("GmoneAccount", "Direct vehicle refresh failed: ${error.message}")
                    launch(Dispatchers.Main) {
                        updateGmoneAccountUi(error.message ?: "차량 조회 실패")
                        showJsStatus(error.message ?: "차량 조회에 실패했습니다.", "danger", 4000)
                    }
                }
            }
        }

        @SuppressLint("MissingPermission")
        @JavascriptInterface
        fun showPairedDeviceList() {
            if (!hasBluetoothScanPermission()) {
                showJsStatus("블루투스/위치 권한이 없습니다.", "danger")
                return
            }

            val bluetoothManager = getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
            val adapter = bluetoothManager.adapter
            if (adapter == null || !adapter.isEnabled) {
                showJsStatus("블루투스가 꺼져있습니다.", "danger")
                return
            }

            val pairedDevices = adapter.bondedDevices
            if (pairedDevices.isEmpty()) {
                showJsStatus("페어링된 기기가 없습니다.", "danger")
                return
            }

            val deviceList = pairedDevices.map {
                "${it.name ?: "이름 없음"} (${it.address})"
            }.toTypedArray()

            val deviceMap = pairedDevices.associateBy { "${it.name ?: "이름 없음"} (${it.address})" }

            launch(Dispatchers.Main) {
                AlertDialog.Builder(this@MainActivity)
                    .setTitle("차량 선택 (myChevrolet)")
                    .setItems(deviceList) { _, which ->
                        val selectedKey = deviceList[which]
                        val selectedDevice = deviceMap[selectedKey]

                        if (selectedDevice != null) {
                            prefs.edit().putString(PREF_KEY_MAC_ADDRESS, selectedDevice.address).apply()
                            Log.d("WebAppInterface", "Vehicle Bluetooth identifier saved")
                            showJsStatus("'${selectedDevice.name ?: "이름 없음"}' 기기가 등록되었습니다.", "success")
                            checkBluetoothStatus()
                            updateDashboardStatus()
                        }
                    }
                    .setNegativeButton("취소", null)
                    .show()
            }
        }

        @SuppressLint("MissingPermission")
        @JavascriptInterface
        fun refreshDeviceList() {
            if (!hasBluetoothScanPermission()) {
                showJsStatus("블루투스/위치 권한이 없습니다.", "danger")
                runJs("updateDeviceList('<p><i>블루투스 스캔 권한이 없습니다. (근처 기기 또는 위치)</i></p>')")
                return
            }

            val bluetoothManager = getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
            val adapter = bluetoothManager.adapter
            if (adapter == null || !adapter.isEnabled) {
                runJs("updateDeviceList('<p><i>블루투스가 꺼져있습니다.</i></p>')")
                return
            }

            val gattDevices = bluetoothManager.getConnectedDevices(BluetoothProfile.GATT)
            val a2dpDevices = a2dpProfile?.connectedDevices ?: emptyList()
            val headsetDevices = headsetProfile?.connectedDevices ?: emptyList()

            val allConnectedDevices = (gattDevices + a2dpDevices + headsetDevices).toSet()

            if (allConnectedDevices.isEmpty()) {
                runJs("updateDeviceList('<p><i>현재 연결된 기기 없음.</i></p>')")
                return
            }

            val htmlBuilder = StringBuilder()
            val savedMacAddress = prefs.getString(PREF_KEY_MAC_ADDRESS, null)

            allConnectedDevices.forEach { device ->
                val deviceName = if (device.name == null) {
                    "<span style=\"color: var(--danger-color);\"><i>null</i></span>"
                } else {
                    "<b>${device.name}</b>"
                }

                htmlBuilder.append("<p style=\"font-size: 14px; margin-bottom: 10px;\">")
                htmlBuilder.append("<b>Name:</b> $deviceName<br>")
                htmlBuilder.append("<b>Address:</b> ${device.address}")

                if (device.address == savedMacAddress) {
                    htmlBuilder.append(" <span style=\"color: var(--success-color);\">(등록된 기기)</span>")
                }

                htmlBuilder.append("</p><hr style=\"border-color: var(--border-color);\">")
            }

            val escapedHtml = htmlBuilder.toString().replace("'", "\\'")
            runJs("updateDeviceList('$escapedHtml')")
        }

        @JavascriptInterface
        fun toggleBluetoothTest() {
            val wasConnected = isBluetoothConnected_VIRTUAL
            isBluetoothConnected_VIRTUAL = !isBluetoothConnected_VIRTUAL

            if (!wasConnected && isBluetoothConnected_VIRTUAL) {
                Log.d("MainActivity", "Virtual BT just CONNECTED. Cancelling remote tasks.")
                cancelAllRemoteTasksOnBtConnect()
                startDrivingService()
            }

            if (wasConnected && !isBluetoothConnected_VIRTUAL) {
                launch {
                    stopDrivingServiceAndSaveLocation()
                }
            }

            runJs("updateBluetoothDebugStatus($isBluetoothConnected_VIRTUAL)")

            launch(Dispatchers.Main) {
                val status = if (isBluetoothConnected_VIRTUAL) "ON (VIRTUAL)" else "OFF (VIRTUAL)"
                showJsStatus("블루투스 테스트: $status", "success")
                setButtonFeedback("btnToggleBluetooth", "success")
                updateDashboardStatus()
            }
        }

        @JavascriptInterface
        fun checkBluetoothStatusForDebug() {
            runJs("updateBluetoothDebugStatus(${isBluetoothConnected || isBluetoothConnected_VIRTUAL})")
        }

    @JavascriptInterface
    fun loadSavedLocation() {
        val lat = prefs.getString(PREF_KEY_LOCATION_LAT, null)
        val lon = prefs.getString(PREF_KEY_LOCATION_LON, null)
        val time = prefs.getString(PREF_KEY_LOCATION_TIME, "-")
        var address = prefs.getString(DrivingService.PREF_KEY_LOCATION_ADDRESS, "") ?: ""

        val latVal = lat?.toDoubleOrNull() ?: 37.5665
        val lonVal = lon?.toDoubleOrNull() ?: 126.9780

        if (address.isEmpty() && lat != null && lon != null) {
            launch(Dispatchers.IO) {
                try {
                    val geocoder = Geocoder(this@MainActivity, Locale.KOREAN)
                    @Suppress("DEPRECATION")
                    val addresses = geocoder.getFromLocation(latVal, lonVal, 1)
                    if (!addresses.isNullOrEmpty()) {
                        address = addresses[0].getAddressLine(0)
                        prefs.edit().putString(DrivingService.PREF_KEY_LOCATION_ADDRESS, address).apply()
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                }
                launch(Dispatchers.Main) {
                    runJs("updateParkingMap($latVal, $lonVal, '$time', '$address')")
                }
            }
        } else {
            runOnUiThread {
                runJs("updateParkingMap($latVal, $lonVal, '$time', '$address')")
            }
        }
    }

    @SuppressLint("MissingPermission")
    @JavascriptInterface
    fun refreshMyLocation() {
        val hasFineLocation = ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.ACCESS_FINE_LOCATION,
        ) == PackageManager.PERMISSION_GRANTED
        val hasCoarseLocation = ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.ACCESS_COARSE_LOCATION,
        ) == PackageManager.PERMISSION_GRANTED

        if (!hasFineLocation && !hasCoarseLocation) {
            runJs("updateMyLocation(null, null, null, ${jsQuote("위치 권한 없음")})")
            return
        }

        locationClient.getCurrentLocation(
            Priority.PRIORITY_BALANCED_POWER_ACCURACY,
            CancellationTokenSource().token,
        ).addOnSuccessListener { location ->
            if (location == null) {
                runJs("updateMyLocation(null, null, null, ${jsQuote("현재 위치 없음")})")
                return@addOnSuccessListener
            }
            val time = SimpleDateFormat("HH:mm", Locale.KOREA).format(Date(location.time))
            runJs(
                "updateMyLocation(${location.latitude}, ${location.longitude}, " +
                    "${location.accuracy}, ${jsQuote(time)})",
            )
        }.addOnFailureListener { error ->
            Log.w("MainActivity", "Phone location refresh failed", error)
            runJs("updateMyLocation(null, null, null, ${jsQuote("위치 확인 실패")})")
        }
    }

    @JavascriptInterface
    fun openSavedLocationMap() {
        val lat = prefs.getString(PREF_KEY_LOCATION_LAT, null)
        val lon = prefs.getString(PREF_KEY_LOCATION_LON, null)

        if (lat != null && lon != null) {
            try {
                val label = "주차 위치"
                val uriString = "geo:$lat,$lon?q=$lat,$lon($label)"
                val intent = Intent(Intent.ACTION_VIEW, Uri.parse(uriString))
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                startActivity(intent)
            } catch (e: Exception) {
                e.printStackTrace()
                launch(Dispatchers.Main) {
                    showJsStatus("지도 앱을 실행할 수 없습니다.", "danger")
                }
            }
        } else {
            launch(Dispatchers.Main) {
                showJsStatus("저장된 주차 위치가 없습니다.", "danger")
            }
        }
    }

    @JavascriptInterface
    fun handleClick(cmdKey: String, cmdName: String, buttonId: String) {
        Log.d("MainActivity", "handleClick called: $cmdKey, $cmdName, $buttonId")
        val isBtOn = isBluetoothConnected || isBluetoothConnected_VIRTUAL
        if ((buttonId == "btnEngineStart" || buttonId == "btnEngineStop") && isBtOn) {
            launch(Dispatchers.Main) {
                runJs("updateDashboardStatus('ACC ON 상태에서는 원격 시동 사용이 불가합니다', '', 'exclamation-triangle', true, $isBtOn)")
                delay(2000)
                updateDashboardStatus()
            }
            return
        }

        if (!checkApiCooldown(buttonId)) {
            Log.d("MainActivity", "checkApiCooldown returned false for $buttonId")
            return
        }

        if (buttonId == "btnEngineStop" && isEngineOn) {
            handleEngineStop(buttonId)
            return
        }

        launch(Dispatchers.IO) {
            Log.d("MainActivity", "Sending command: $cmdKey")
            val success = sendCommandInternal(cmdKey)
            Log.d("MainActivity", "Command result: $success")
            launch(Dispatchers.Main) {
                setButtonFeedback(buttonId, if (success) "success" else "danger", cmdKey)
            }
        }
    }

    @JavascriptInterface
    fun handleLongPress(cmdKey: String, cmdName: String, buttonId: String) {
        Log.d("MainActivity", "handleLongPress called: $cmdKey, $cmdName, $buttonId")
        val isBtOn = isBluetoothConnected || isBluetoothConnected_VIRTUAL

        if ((buttonId == "btnEngineStart" || buttonId == "btnEngineStop" || buttonId == "btnFindMyCar") && isBtOn) {
            launch(Dispatchers.Main) {
                runJs("updateDashboardStatus('ACC ON 상태에서는 원격 시동 사용이 불가합니다', '', 'exclamation-triangle', true, $isBtOn)")

                if (buttonId == "btnFindMyCar") {
                    showJsStatus("ACC ON 상태에서는 사용이 불가합니다", "danger", 3000)
                }

                delay(2000)
                updateDashboardStatus()
            }
            return
        }

        if (!checkApiCooldown(buttonId)) {
            Log.d("MainActivity", "checkApiCooldown returned false for $buttonId")
            return
        }

        if (buttonId == "btnEngineStart") {
            if (isEngineOn) return
            handleEngineStart(buttonId)
            return
        }

        launch(Dispatchers.IO) {
            Log.d("MainActivity", "Sending command: $cmdKey")
            val success = sendCommandInternal(cmdKey)
            Log.d("MainActivity", "Command result: $success")
            launch(Dispatchers.Main) {
                setButtonFeedback(buttonId, if (success) "success" else "danger", cmdKey)
            }
        }
    }


    private fun handleEngineStart(buttonId: String) {
        launch(Dispatchers.IO) {
            val success = sendCommandInternal("VEHICLE_START")
            launch(Dispatchers.Main) {
                setButtonFeedback(buttonId, if (success) "success" else "danger")
                if (success) {
                    isEngineOn = true
                    runJs("updateEngineUI(true)")
                    startTimerService("ENGINE", 20 * 60 * 1000)
                    updateDashboardStatus()
                }
            }
        }
    }

    private fun handleEngineStop(buttonId: String) {
        launch(Dispatchers.IO) {
            val success = sendCommandInternal("VEHICLE_STOP")
            launch(Dispatchers.Main) {
                setButtonFeedback(buttonId, if (success) "success" else "danger")
                if (success) {
                    isEngineOn = false
                    runJs("updateEngineUI(false)")
                    stopTimerService("ENGINE")
                    updateDashboardStatus()
                }
            }
        }
    }

    @JavascriptInterface
    fun handleVentilationToggle() {
        Log.d("MainActivity", "handleVentilationToggle called")
        val isBtOn = isBluetoothConnected || isBluetoothConnected_VIRTUAL
        if (!isVentilating && isBtOn) {
            launch(Dispatchers.Main) {
                runJs("updateDashboardStatus('ACC ON 상태에서는 원격 시동 사용이 불가합니다', '', 'exclamation-triangle', true, $isBtOn)")
                showJsStatus("ACC ON 상태에서는 사용이 불가합니다", "danger", 3000)
                delay(2000)
                updateDashboardStatus()
            }
            return
        }

        if (!isVentilating && !checkApiCooldown("btnVentilation")) return

        if (isVentilating) {
            stopVentilation(false)
        } else {
            startVentilation()
        }
    }

    @JavascriptInterface
    fun handleHeatEjectToggle() {
        Log.d("MainActivity", "handleHeatEjectToggle called")
        val isBtOn = isBluetoothConnected || isBluetoothConnected_VIRTUAL
        if (!isHeatEjecting && isBtOn) {
            launch(Dispatchers.Main) {
                runJs("updateDashboardStatus('ACC ON 상태에서는 원격 시동 사용이 불가합니다', '', 'exclamation-triangle', true, $isBtOn)")
                showJsStatus("ACC ON 상태에서는 사용이 불가합니다", "danger", 3000)
                delay(2000)
                updateDashboardStatus()
            }
            return
        }

        if (!isHeatEjecting && !checkApiCooldown("btnHeatEject")) return

        if (isHeatEjecting) {
            stopHeatEject(false)
        } else {
            startHeatEject()
        }
    }

    @JavascriptInterface
    fun getDrivingHistory(): String {
        if (WayonCloudMode.isEnabled(this)) {
            return wayonCloudHistoryJson ?: "[]"
        }
        return try {
            val file = java.io.File(this@MainActivity.filesDir, "driving_history.json")
            if (file.exists()) org.json.JSONArray(file.readText()).toString() else "[]"
        } catch (e: Exception) {
            Log.e("MainActivity", "Failed to read driving history", e)
            "[]"
        }
    }

    @JavascriptInterface
    fun refreshCarData() {
        triggerRefresh()
    }

    @JavascriptInterface
    fun refreshWayonCloudData() {
        refreshWayonCloudFeed(showResult = false)
    }

    @JavascriptInterface
    fun refreshWayonCloudTrips() {
        refreshWayonCloudTrips(showResult = false)
    }

    @JavascriptInterface
    fun clearDrivingHistory() {
        try {
            val file = java.io.File(this@MainActivity.filesDir, "driving_history.json")
            if (file.exists()) {
                file.delete()
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    @JavascriptInterface
    fun setAutoRefresh(enabled: Boolean) {
        Log.d("MainActivity", "JS Request: setAutoRefresh($enabled)")
        launch(Dispatchers.IO) {
            carStatusReference()?.child("setting_auto_refresh")?.setValue(enabled)
        }

        launch(Dispatchers.Main) {
            val state = if(enabled) "ON" else "OFF"
            showJsStatus("자동 새로고침: $state", "info")
            // Optimistic UI update check
            runJs("updateSettingsUI($enabled)")
        }
    }

    private fun startVentilation() {
        if (isHeatEjecting) {
            showJsStatus("열 배출 모드가 실행 중입니다.", "danger")
            return
        }

        isVentilating = true
        runJs("updateVentilationUI(true)")
        setExtrasButtonsDisabled(true)
        updateDashboardStatus()

        launch(Dispatchers.IO) {
            val success = sendCommandInternal("WINDOW_OPEN")
            launch(Dispatchers.Main) {
                setButtonFeedback("btnVentilation", if (success) "success" else "danger")
                if (success) {
                    startTimerService("VENTILATION", 5 * 60 * 1000)
                } else {
                    isVentilating = false
                    runJs("updateVentilationUI(false)")
                }
                setExtrasButtonsDisabled(false)
                updateDashboardStatus()
            }
        }
    }

    private fun stopVentilation(autoClose: Boolean) {
        stopTimerService("VENTILATION")

        launch(Dispatchers.IO) {
            launch(Dispatchers.Main) { setExtrasButtonsDisabled(true) }
            val success = sendCommandInternal("WINDOW_CLOSE")
            launch(Dispatchers.Main) {
                setButtonFeedback("btnVentilation", if (success) "success" else "danger")
                isVentilating = false
                runJs("updateVentilationUI(false)")
                setExtrasButtonsDisabled(false)
                updateDashboardStatus()
            }
        }
    }

    private fun startHeatEject() {
        if (isVentilating) {
            showJsStatus("열 배출 모드가 실행 중입니다.", "danger")
            return
        }
        isHeatEjecting = true
        runJs("updateHeatEjectUI(true)")
        setExtrasButtonsDisabled(true)
        updateDashboardStatus()

        launch(Dispatchers.IO) {
            var success = sendCommandInternal("WINDOW_OPEN")
            if (!success) {
                abortHeatEjectStart(closeWindow = false, closeSunroof = false)
                return@launch
            }
            launch(Dispatchers.Main) { setButtonFeedback("btnHeatEject", "success") }
            delay(apiDelay)

            if (!isHeatEjecting) return@launch

            success = sendCommandInternal("SUNROOF_OPEN")
            if (!success) {
                abortHeatEjectStart(closeWindow = true, closeSunroof = false)
                return@launch
            }
            launch(Dispatchers.Main) { setButtonFeedback("btnHeatEject", "success") }
            delay(apiDelay)

            if (!isHeatEjecting) return@launch

            success = sendCommandInternal("VEHICLE_START")
            if (!success) {
                abortHeatEjectStart(closeWindow = true, closeSunroof = true)
                return@launch
            }
            launch(Dispatchers.Main) { setButtonFeedback("btnHeatEject", "success") }

            if (!isHeatEjecting) return@launch

            launch(Dispatchers.Main) {
                isEngineOn = true
                runJs("updateEngineUI(true)")
                startTimerService("ENGINE", 20 * 60 * 1000)
                startTimerService("HEAT_EJECT", 5 * 60 * 1000)

                setExtrasButtonsDisabled(false)
                updateDashboardStatus()
            }
        }
    }

    private suspend fun abortHeatEjectStart(closeWindow: Boolean, closeSunroof: Boolean) {
        var cleanupSuccess = true
        if (closeWindow) {
            cleanupSuccess = sendCommandInternal("WINDOW_CLOSE")
        }
        if (closeSunroof) {
            delay(apiDelay)
            cleanupSuccess = sendCommandInternal("SUNROOF_CLOSE") && cleanupSuccess
        }

        launch(Dispatchers.Main) {
            setButtonFeedback("btnHeatEject", "danger")
            isHeatEjecting = false
            runJs("updateHeatEjectUI(false)")
            setExtrasButtonsDisabled(false)
            val message = if (cleanupSuccess) "열 배출 시작 실패: 열린 창문/선루프를 닫았습니다."
            else "열 배출 시작 실패: 창문/선루프 닫기 명령을 확인해 주세요."
            showJsStatus(message, "danger", 4000)
            updateDashboardStatus()
        }
    }

    private fun stopHeatEject(autoClose: Boolean, closeWindows: Boolean = true) {
        stopTimerService("HEAT_EJECT")

        if (!closeWindows) {
            isHeatEjecting = false
            runJs("updateHeatEjectUI(false)")
            setExtrasButtonsDisabled(false)
            updateDashboardStatus()
            return
        }

        launch(Dispatchers.IO) {
            launch(Dispatchers.Main) { setExtrasButtonsDisabled(true) }
            val windowSuccess = sendCommandInternal("WINDOW_CLOSE")
            delay(apiDelay)
            val sunroofSuccess = sendCommandInternal("SUNROOF_CLOSE")
            val success = windowSuccess && sunroofSuccess

            launch(Dispatchers.Main) {
                setButtonFeedback("btnHeatEject", if (success) "success" else "danger")
                isHeatEjecting = false
                runJs("updateHeatEjectUI(false)")
                setExtrasButtonsDisabled(false)
                updateDashboardStatus()
            }
        }
    }

    private fun parseTimestamp(timeStr: String): Long {
        return try {
            val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
            sdf.parse(timeStr)?.time ?: 0L
        } catch (e: Exception) {
            0L
        }
    }
}
