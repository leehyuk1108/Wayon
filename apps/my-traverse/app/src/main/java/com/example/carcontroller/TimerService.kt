package com.example.carcontroller

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.CountDownTimer
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.localbroadcastmanager.content.LocalBroadcastManager
import java.io.IOException
import java.net.URL
import javax.net.ssl.HttpsURLConnection
import kotlin.coroutines.CoroutineContext
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class TimerService : Service(), CoroutineScope {
    override val coroutineContext: CoroutineContext = Dispatchers.Main

    // === 1. 타이머 변수 2개로 분리 ===
    private var timerEngine: CountDownTimer? = null
    private var timerExtras: CountDownTimer? = null

    // === 2. 타이머별 남은 시간/제목 저장 ===
    private var engineTimeLeft: String = ""
    private var extrasTimeLeft: String = ""
    private var extrasTaskTitle: String = ""

    private var baseApiUrl: String? = null

    // === 3. 서비스가 포그라운드 상태인지 추적 ===
    private var isServiceInForeground = false

    companion object {
        const val NOTIFICATION_ID = 1 // ‼️ 이제 알림 ID는 1개만 사용
        const val COMPLETION_NOTIFICATION_ID = 2 // 완료 알림 ID

        const val CHANNEL_ID = "CarTimerChannel"
        const val ACTION_START_TIMER = "ACTION_START_TIMER"
        const val ACTION_STOP_TIMER = "ACTION_STOP_TIMER"

        // UI 업데이트용 브로드캐스트
        const val BROADCAST_TIMER_UPDATE = "BROADCAST_TIMER_UPDATE"
        const val EXTRA_TIME_STRING = "EXTRA_TIME_STRING"
        const val EXTRA_TASK_TYPE = "EXTRA_TASK_TYPE"
        const val EXTRA_IS_RUNNING = "EXTRA_IS_RUNNING"
    }

    override fun onCreate() {
        super.onCreate()
        baseApiUrl = getSavedBaseApiUrl()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        intent?.getStringExtra("BASE_API_URL")
            ?.takeIf { it.isNotBlank() }
            ?.let { apiUrl ->
                baseApiUrl = apiUrl
                getSharedPreferences(MainActivity.PREFS_NAME, Context.MODE_PRIVATE)
                    .edit()
                    .putString(MainActivity.PREF_KEY_API_URL, apiUrl)
                    .apply()
            }
        val action = intent?.action
        val taskType = intent?.getStringExtra("TASK_TYPE")

        if (action == ACTION_START_TIMER) {
            val duration = intent.getLongExtra("TIMER_DURATION", 0)
            if (taskType == "ENGINE") {
                startEngineTimer(duration)
            } else if (taskType == "VENTILATION" || taskType == "HEAT_EJECT") {
                startExtrasTimer(duration, taskType)
            }
        } else if (action == ACTION_STOP_TIMER) {
            if (taskType == "ENGINE") {
                stopEngineTimer()
            } else if (taskType == "VENTILATION" || taskType == "HEAT_EJECT") {
                stopExtrasTimer(taskType)
            }
        }
        return START_STICKY
    }

    // --- 4. 타이머 함수 수정 ---

    // A. 시동 타이머 (ENGINE)
    private fun startEngineTimer(duration: Long) {
        timerEngine?.cancel()
        engineTimeLeft = formatTime(duration)
        timerEngine = object : CountDownTimer(duration, 1000) {
            override fun onTick(millisUntilFinished: Long) {
                engineTimeLeft = formatTime(millisUntilFinished)
                updateCombinedNotification()
                broadcastTimerUpdate("ENGINE", true, engineTimeLeft)
            }
            override fun onFinish() {
                launch {
                    val success = handleTimerFinish("ENGINE")
                    stopEngineTimer()
                    if (!MainActivity.isActivityVisible) {
                        val message = if (success) "20분 타이머가 만료되어 시동을 껐습니다."
                        else "20분 타이머가 만료되었지만 시동 끄기 명령 전송에 실패했습니다."
                        showCompletionNotification("시동 타이머 종료", message)
                    }
                }
            }
        }.start()
        updateCombinedNotification()
    }

    private fun stopEngineTimer() {
        timerEngine?.cancel()
        timerEngine = null
        engineTimeLeft = ""
        broadcastTimerUpdate("ENGINE", false)
        updateCombinedNotification() // ‼️ 알림 갱신 (또는 제거)
    }

    // B. 부가기능 타이머 (VENTILATION, HEAT_EJECT)
    private fun startExtrasTimer(duration: Long, taskType: String) {
        timerExtras?.cancel()

        extrasTaskTitle = if (taskType == "VENTILATION") "환기 모드" else "열 배출 모드"
        extrasTimeLeft = formatTime(duration)

        timerExtras = object : CountDownTimer(duration, 1000) {
            override fun onTick(millisUntilFinished: Long) {
                extrasTimeLeft = formatTime(millisUntilFinished)
                updateCombinedNotification()
                broadcastTimerUpdate(taskType, true, extrasTimeLeft)
            }
            override fun onFinish() {
                launch {
                    val success = handleTimerFinish(taskType)
                    stopExtrasTimer(taskType)
                    if (!MainActivity.isActivityVisible) {
                        val message = when {
                            taskType == "VENTILATION" && success -> "5분 타이머가 만료되어 창문을 닫았습니다."
                            taskType == "VENTILATION" -> "5분 타이머가 만료되었지만 창문 닫기 명령 전송에 실패했습니다."
                            success -> "5분 타이머가 만료되어 창문과 선루프를 닫았습니다."
                            else -> "5분 타이머가 만료되었지만 창문/선루프 닫기 명령 전송에 실패했습니다."
                        }
                        showCompletionNotification("$extrasTaskTitle 종료", message)
                    }
                }
            }
        }.start()
        updateCombinedNotification()
    }

    private fun stopExtrasTimer(taskType: String) {
        timerExtras?.cancel()
        timerExtras = null
        extrasTimeLeft = ""
        broadcastTimerUpdate(taskType, false)
        updateCombinedNotification() // ‼️ 알림 갱신 (또는 제거)
    }


    // --- 5. 타이머 종료 로직 (동일) ---
    private suspend fun handleTimerFinish(taskType: String): Boolean = withContext(Dispatchers.IO) {
        when (taskType) {
            "ENGINE" -> sendCommandInternal("VEHICLE_STOP")
            "VENTILATION" -> sendCommandInternal("WINDOW_CLOSE")
            "HEAT_EJECT" -> {
                val windowSuccess = sendCommandInternal("WINDOW_CLOSE")
                delay(5000)
                val sunroofSuccess = sendCommandInternal("SUNROOF_CLOSE")
                windowSuccess && sunroofSuccess
            }
            else -> false
        }
    }

    private fun getSavedBaseApiUrl(): String? {
        return getSharedPreferences(MainActivity.PREFS_NAME, Context.MODE_PRIVATE)
            .getString(MainActivity.PREF_KEY_API_URL, null)
    }

    // 실제 API를 호출하는 내부 함수 (동일)
    private fun sendCommandInternal(cmd: String): Boolean {
        val apiUrl = baseApiUrl ?: getSavedBaseApiUrl()?.also { baseApiUrl = it } ?: return false
        val fullUrl = "$apiUrl&cmd=$cmd"
        var connection: HttpsURLConnection? = null

        return try {
            val url = URL(fullUrl)
            connection = (url.openConnection() as HttpsURLConnection).apply {
                requestMethod = "GET"
                connectTimeout = 5000
                readTimeout = 5000
            }
            connection.responseCode in 200..299
        } catch (e: IOException) {
            e.printStackTrace()
            Log.e("TimerService", "API Call Failed: ${e.message}")
            false
        } finally {
            connection?.disconnect()
        }
    }

    // JS(WebView)로 현재 상태를 알림 (동일)
    private fun broadcastTimerUpdate(taskType: String, isRunning: Boolean, timeString: String = "") {
        val intent = Intent(BROADCAST_TIMER_UPDATE)
        intent.putExtra(EXTRA_IS_RUNNING, isRunning)
        intent.putExtra(EXTRA_TIME_STRING, timeString)
        intent.putExtra(EXTRA_TASK_TYPE, taskType)
        LocalBroadcastManager.getInstance(this).sendBroadcast(intent)
    }

    private fun formatTime(millis: Long): String {
        val minutes = (millis / 1000) / 60
        val seconds = (millis / 1000) % 60
        return String.format("%02d:%02d", minutes, seconds)
    }

    // --- 6. 알림 로직 수정 ---

    // (진행 중) 알림 생성
    private fun createNotification(title: String, text: String, inboxStyleLines: List<String> = emptyList()): Notification {
        val notificationIntent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this,
            0, notificationIntent, PendingIntent.FLAG_IMMUTABLE
        )

        val builder = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(text)
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setOnlyAlertOnce(true) // 진동/소리는 1회만

        if (inboxStyleLines.isNotEmpty()) {
            val inboxStyle = NotificationCompat.InboxStyle()
            inboxStyleLines.forEach { line ->
                inboxStyle.addLine(line)
            }
            builder.setStyle(inboxStyle)
        }

        return builder.build()
    }

    // (신규) 통합 알림 업데이트 함수
    private fun updateCombinedNotification() {
        val lines = mutableListOf<String>()
        if (timerEngine != null) {
            lines.add("시동: $engineTimeLeft 남음")
        }
        if (timerExtras != null) {
            lines.add("$extrasTaskTitle: $extrasTimeLeft 남음")
        }

        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        if (lines.isEmpty()) {
            // 모든 타이머가 꺼졌으면 알림 중지
            stopForeground(true)
            isServiceInForeground = false
            stopSelf() // 서비스 종료
            return
        }

        val title = "차량 모드 동작중"
        val contentText = lines.first() // 첫 번째 줄을 기본 텍스트로

        val notification = createNotification(title, contentText, lines)

        // (ID 1번으로 알림을 통합하여 시작/업데이트)
        if (!isServiceInForeground) {
            startForeground(NOTIFICATION_ID, notification)
            isServiceInForeground = true
        } else {
            manager.notify(NOTIFICATION_ID, notification)
        }
    }

    // (완료) 알림 띄우기 함수
    private fun showCompletionNotification(title: String, text: String) {
        val notificationIntent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this,
            0, notificationIntent, PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(text)
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .build()

        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(COMPLETION_NOTIFICATION_ID, notification) // ID (2번)
    }

    // (채널 생성 함수 - 중요도 DEFAULT 유지)
    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val serviceChannel = NotificationChannel(
                CHANNEL_ID,
                "차량 타이머",
                NotificationManager.IMPORTANCE_DEFAULT // 상단에 뜨도록
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(serviceChannel)
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
