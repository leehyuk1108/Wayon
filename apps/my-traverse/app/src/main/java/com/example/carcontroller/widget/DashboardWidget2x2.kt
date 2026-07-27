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

class DashboardWidget2x2 : AppWidgetProvider() {

    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {
        for (appWidgetId in appWidgetIds) {
            updateAppWidget(context, appWidgetManager, appWidgetId)
        }
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        if (intent.action == "com.example.carcontroller.UPDATE_WIDGET") {
            val appWidgetManager = AppWidgetManager.getInstance(context)
            val ids = appWidgetManager.getAppWidgetIds(android.content.ComponentName(context, DashboardWidget2x2::class.java))
            for (id in ids) {
                updateAppWidget(context, appWidgetManager, id)
            }
        }
    }

    companion object {
        fun updateAppWidget(context: Context, appWidgetManager: AppWidgetManager, appWidgetId: Int) {
            val prefs: SharedPreferences = context.getSharedPreferences("widget_data", Context.MODE_PRIVATE)
            val views = RemoteViews(context.packageName, R.layout.widget_dashboard_2x2)

            val fuel = prefs.getString("fuel", "--") ?: "--"
            val range = prefs.getString("range", "--") ?: "--"
            val battery = prefs.getString("battery", "--") ?: "--"
            val batteryLevel = prefs.getString("batteryLevel", "--") ?: "--"
            val lastUpdate = prefs.getString("lastUpdate", "--:--") ?: "--:--"

            views.setTextViewText(R.id.widget_fuel_range, range)
            views.setTextViewText(R.id.widget_fuel_val, "$fuel%")
            views.setTextViewText(R.id.widget_bat_val, "$batteryLevel% • ${battery}V") // Restored Voltage

            // Parse Fuel for ProgressBar
            val fuelInt = fuel.toIntOrNull() ?: 0
            views.setProgressBar(R.id.widget_fuel_bar, 100, fuelInt, false)
            views.setTextViewText(R.id.widget_last_updated, lastUpdate)

            // Refresh Click
            val refreshIntent = Intent(context, com.example.carcontroller.WidgetCommandReceiver::class.java).apply {
                putExtra("WIDGET_ACTION", "REFRESH_FROM_WIDGET")
            }
             val pendingIntent = PendingIntent.getBroadcast(
                context, 0, refreshIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            views.setOnClickPendingIntent(R.id.widget_btn_refresh, pendingIntent)

            // Open App
            val openIntent = Intent(context, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            }
            val openPendingIntent = PendingIntent.getActivity(
                context, 1, openIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            views.setOnClickPendingIntent(R.id.widget_car_name, openPendingIntent)

            appWidgetManager.updateAppWidget(appWidgetId, views)
        }
    }
}
