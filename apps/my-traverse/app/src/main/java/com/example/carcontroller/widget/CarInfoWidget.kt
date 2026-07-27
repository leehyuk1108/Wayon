package com.example.carcontroller.widget

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.widget.RemoteViews
import com.example.carcontroller.MainActivity
import com.example.carcontroller.R

class CarInfoWidget : AppWidgetProvider() {

    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {
        // Update all widgets
        for (appWidgetId in appWidgetIds) {
            updateAppWidget(context, appWidgetManager, appWidgetId)
        }
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        if (intent.action == "com.example.carcontroller.UPDATE_WIDGET") {
            val appWidgetManager = AppWidgetManager.getInstance(context)
            val ids = appWidgetManager.getAppWidgetIds(android.content.ComponentName(context, CarInfoWidget::class.java))
            for (id in ids) {
                updateAppWidget(context, appWidgetManager, id)
            }
        }
    }

    companion object {
        fun updateAppWidget(context: Context, appWidgetManager: AppWidgetManager, appWidgetId: Int) {
            val prefs: SharedPreferences = context.getSharedPreferences("widget_data", Context.MODE_PRIVATE)

            // Construct the RemoteViews object
            val views = RemoteViews(context.packageName, R.layout.widget_car_info)

            // Read data
            // Note: DashboardWidget uses 'oil' pref for 'Oil Life' but user wants 'Fuel Level' style display (72%).
            // Usually 'oil' stores "72". 'range' stores "459".
            // 'battery' stores "12.2" and 'batteryLevel' stores "49".
            val range = prefs.getString("range", "--") ?: "--"
            val oil = prefs.getString("oil", "--") ?: "--"
            val battery = prefs.getString("battery", "--") ?: "--"
            val batteryLevel = prefs.getString("batteryLevel", "--") ?: "--"

            // Set Text
            views.setTextViewText(R.id.widget_car_range, range)

            // Bottom Info
            // Fuel Icon + Percentage (mapped from 'oil' for now as per DashboardWidget pattern)
            views.setTextViewText(R.id.widget_car_fuel, "$oil%")

            // Battery Icon + "12.2V (49%)"
            views.setTextViewText(R.id.widget_car_battery, "${battery}V ($batteryLevel%)")

            // Refresh Click (Use Static Receiver for reliability)
            val refreshIntent = Intent(context, com.example.carcontroller.WidgetCommandReceiver::class.java).apply {
                putExtra("WIDGET_ACTION", "REFRESH_FROM_WIDGET")
            }
             val pendingIntent = PendingIntent.getBroadcast(
                context, 0, refreshIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            views.setOnClickPendingIntent(R.id.widget_btn_refresh, pendingIntent)

            // Open App on Click Title or Car Image
            val openIntent = Intent(context, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            }
            val openPendingIntent = PendingIntent.getActivity(
                context, 1, openIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            views.setOnClickPendingIntent(R.id.widget_title, openPendingIntent)
            views.setOnClickPendingIntent(R.id.widget_car_image, openPendingIntent)


            // Instruct the widget manager to update the widget
            appWidgetManager.updateAppWidget(appWidgetId, views)
        }
    }
}
