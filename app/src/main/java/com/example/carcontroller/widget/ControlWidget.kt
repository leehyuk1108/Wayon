package com.example.carcontroller.widget

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.content.Intent
import android.widget.RemoteViews
import com.example.carcontroller.MainActivity
import com.example.carcontroller.R
import com.example.carcontroller.WidgetCommandReceiver

class ControlWidget : AppWidgetProvider() {

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        val action = intent.action

        if (action != null && action.startsWith("CMD_")) {
            // Send Broadcast to Static Receiver
            val broadcastIntent = Intent(context, WidgetCommandReceiver::class.java).apply {
                putExtra("WIDGET_ACTION", action)
            }
            context.sendBroadcast(broadcastIntent)
        }
    }

    companion object {
        fun updateAppWidget(context: Context, appWidgetManager: AppWidgetManager, appWidgetId: Int) {
            val views = RemoteViews(context.packageName, R.layout.widget_control)

            // Define Actions
            views.setOnClickPendingIntent(R.id.widget_btn_start, getPendingIntent(context, "CMD_START_ENGINE"))
            views.setOnClickPendingIntent(R.id.widget_btn_stop, getPendingIntent(context, "CMD_STOP_ENGINE"))
            views.setOnClickPendingIntent(R.id.widget_btn_lock, getPendingIntent(context, "CMD_LOCK_DOOR"))
            views.setOnClickPendingIntent(R.id.widget_btn_unlock, getPendingIntent(context, "CMD_UNLOCK_DOOR"))

            appWidgetManager.updateAppWidget(appWidgetId, views)
        }

        private fun getPendingIntent(context: Context, action: String): PendingIntent {
            val intent = Intent(context, ControlWidget::class.java).apply {
                this.action = action
            }
            return PendingIntent.getBroadcast(
                context,
                action.hashCode(),
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
        }
    }
}
