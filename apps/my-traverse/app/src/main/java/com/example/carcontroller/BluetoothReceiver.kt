package com.example.carcontroller

import android.Manifest
import android.annotation.SuppressLint
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.bluetooth.BluetoothDevice
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.location.Address
import android.location.Geocoder
import android.location.Location
import android.os.Build
import android.util.Log
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import java.io.IOException
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class BluetoothReceiver : BroadcastReceiver() {

    companion object {
        const val LOCATION_NOTIFICATION_ID = 4
        const val LOCATION_CHANNEL_ID = "LocationNotificationChannel"
    }

    @SuppressLint("MissingPermission")
    override fun onReceive(context: Context, intent: Intent) {
        // (신규) 블루투스 연결 감지 (Auto-Start)
        if (intent.action == BluetoothDevice.ACTION_ACL_CONNECTED) {
             // 1. 권한 확인 (Android 12+)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                if (ActivityCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
                    Log.w("BluetoothReceiver", "BT CONNECT permission missing.")
                    return
                }
            }

            val device: BluetoothDevice? = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE, BluetoothDevice::class.java)
            } else {
                @Suppress("DEPRECATION")
                intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE)
            }

            if (device != null && device.name?.equals("myChevrolet", ignoreCase = true) == true) {
                Log.d("BluetoothReceiver", "myChevrolet CONNECTED (Background). Starting DrivingService.")

                // 서비스 시작 Intent
                val startServiceIntent = Intent(context, DrivingService::class.java).apply {
                    action = DrivingService.ACTION_START_DRIVING
                }

                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    context.startForegroundService(startServiceIntent)
                } else {
                    context.startService(startServiceIntent)
                }
            }
        }
        else if (intent.action == BluetoothDevice.ACTION_ACL_DISCONNECTED) {

            // 1. 권한 확인 (Android 12+)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                if (ActivityCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED) {
                    Log.w("BluetoothReceiver", "BT CONNECT permission missing.")
                    return
                }
            }

            // 2. 기기 정보 가져오기
            val device: BluetoothDevice? = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE, BluetoothDevice::class.java)
            } else {
                @Suppress("DEPRECATION")
                intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE)
            }

            // 3. "myChevrolet" 기기가 맞는지 확인
            if (device != null && device.name?.equals("myChevrolet", ignoreCase = true) == true) {
                Log.d("BluetoothReceiver", "myChevrolet disconnected (Background). Stopping DrivingService...")

                // ‼️‼️‼️ 4. (수정) DrivingService 중지 명령 ‼️‼️‼️
                // (DrivingService가 종료되면서 위치와 주행 기록을 저장할 것임)
                val stopServiceIntent = Intent(context, DrivingService::class.java).apply {
                    action = DrivingService.ACTION_STOP_DRIVING
                }
                context.startService(stopServiceIntent)

                // ‼️ (신규) MAC 주소는 여기서도 저장 (최초 등록을 위해)
                val prefs = context.getSharedPreferences(MainActivity.PREFS_NAME, Context.MODE_PRIVATE)
                if (device.address != null) {
                    prefs.edit().putString(MainActivity.PREF_KEY_MAC_ADDRESS, device.address).apply()
                    Log.d("BluetoothReceiver", "Saved/Updated MAC Address: ${device.address}")
                }

                // ‼️ (삭제) goAsync() 및 자체 위치 저장 로직 모두 제거
            }
        }
    }

    // (getAddressFromLocation, showLocationSavedNotification, createNotificationChannel 함수는
    //  DrivingService가 아니라 여기서만 사용하므로 그대로 둡니다.)

    private fun getAddressFromLocation(context: Context, lat: Double, lon: Double): String {
        // (참고: 이 함수는 DrivingService에서도 중복으로 사용 중입니다.
        //  별도의 Util 파일로 분리하는 것을 권장합니다.)
        return try {
            val geocoder = Geocoder(context, Locale.KOREAN)
            @Suppress("DEPRECATION")
            val addresses: MutableList<Address>? = geocoder.getFromLocation(lat, lon, 1)
            if (addresses != null && addresses.isNotEmpty()) {
                addresses[0].getAddressLine(0)
            } else {
                "주소를 찾을 수 없음"
            }
        } catch (e: IOException) {
            "주소 변환 실패"
        }
    }

    @SuppressLint("MissingPermission")
    private fun showLocationSavedNotification(context: Context, title: String, text: String) {
        createNotificationChannel(context)

        val notificationIntent = Intent(context, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            context,
            0, notificationIntent, PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, LOCATION_CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(text)
            .setSmallIcon(R.mipmap.ic_launcher) // (아이콘 확인 필요)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .build()

        if (ActivityCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            Log.w("BluetoothReceiver", "POST_NOTIFICATIONS permission missing")
            return
        }

        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(LOCATION_NOTIFICATION_ID, notification)
    }

    private fun createNotificationChannel(context: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val serviceChannel = NotificationChannel(
                LOCATION_CHANNEL_ID,
                "주차 위치 알림",
                NotificationManager.IMPORTANCE_DEFAULT
            )
            val manager = context.getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(serviceChannel)
        }
    }
}