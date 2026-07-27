package com.example.carcontroller

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class WidgetCommandReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.getStringExtra("WIDGET_ACTION") ?: return
        Log.d("WidgetReceiver", "Received action: $action")

        val activity = GlobalHelper.getMainActivity()
        if (activity != null && !activity.isFinishing && !activity.isDestroyed) {
            Log.d("WidgetReceiver", "Activity found. Routing to MainActivity.")
            activity.handleWidgetCommand(Intent(action))
        } else {
            Log.d("WidgetReceiver", "Activity NOT found. Launching App.")
            val activityIntent = Intent(context, MainActivity::class.java).apply {
                this.action = action
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            }
            context.startActivity(activityIntent)
        }
    }
}
