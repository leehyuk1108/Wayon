package com.example.carcontroller

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.os.Build

class TimerReceiver : BroadcastReceiver() {

    // 핸드폰이 재부팅되면 이 함수가 호출됩니다.
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == "android.intent.action.BOOT_COMPLETED") {
            // (구현 참고)
            // 실제 앱에서는 SharedPreferences 같은 곳에 타이머가 실행 중이었는지
            // 상태를 저장하고, 재부팅 시 그 상태를 읽어와서
            // TimerService를 다시 실행해야 합니다.

            // 지금은 간단히, 재부팅 시 알림만 띄우는 정도로 둘 수 있습니다.
            // (또는 일단 비워두어도 앱 실행에는 문제가 없습니다.)

            // Log.d("TimerReceiver", "Boot completed, checking for active timers...")
        }
    }
}