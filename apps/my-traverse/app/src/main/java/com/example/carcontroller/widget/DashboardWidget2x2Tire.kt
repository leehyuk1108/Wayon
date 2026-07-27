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

class DashboardWidget2x2Tire : AppWidgetProvider() {

    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {
        for (appWidgetId in appWidgetIds) {
            updateAppWidget(context, appWidgetManager, appWidgetId)
        }
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        if (intent.action == "com.example.carcontroller.UPDATE_WIDGET") {
            val appWidgetManager = AppWidgetManager.getInstance(context)
            val ids = appWidgetManager.getAppWidgetIds(android.content.ComponentName(context, DashboardWidget2x2Tire::class.java))
            for (id in ids) {
                updateAppWidget(context, appWidgetManager, id)
            }
        }
    }

    companion object {
        fun updateAppWidget(context: Context, appWidgetManager: AppWidgetManager, appWidgetId: Int) {
            val prefs: SharedPreferences = context.getSharedPreferences("widget_data", Context.MODE_PRIVATE)
            val views = RemoteViews(context.packageName, R.layout.widget_dashboard_2x2_tire)

            // Data Points: Tire Pressure (All)
            val tireAll = prefs.getString("tire_pressure", "--") ?: "--"
            val lastUpdate = prefs.getString("lastUpdate", "--:--") ?: "--:--"

            // Parse Tire Pressure
            // Use robust regex handling for "252 240 248 248" (spaces) or "252,240..." (commas)
            var fl = "--"
            var fr = "--"
            var rl = "--"
            var rr = "--"

            // 1. Clean string: remove brackets, quotes, units
            var cleanTire = tireAll.replace("[", "").replace("]", "").replace("\"", "")
            cleanTire = cleanTire.replace(Regex("(?i)(psi|kpa)"), "")

            // 2. Split by comma or whitespace
            val rawParts = cleanTire.split(Regex("[,\\s]+"))

            // 3. Extract digits from each part
            val digitParts = rawParts.map { it.filter { c -> c.isDigit() } }.filter { it.isNotEmpty() }

            val finalParts = mutableListOf<String>()

            if (digitParts.size >= 4) {
                 finalParts.addAll(digitParts)
            } else if (digitParts.size == 1 && digitParts[0].length >= 8) {
                 // Fallback: If 1 giant string (e.g. "252240248248"), chunk into 3s
                 // Assuming 3-digit pressures (kPa > 100)
                 digitParts[0].chunked(3).forEach { finalParts.add(it) }
            } else {
                 finalParts.addAll(digitParts)
            }

            if (finalParts.isNotEmpty()) {
                if (finalParts.size >= 4) {
                    fl = finalParts[0]
                    fr = finalParts[2] // Swapped with RL based on user report (Input likely FL, RL, FR, RR)
                    rl = finalParts[1]
                    rr = finalParts[3]
                } else if (finalParts.size == 1) {
                     // Still just one value? Duplicate it.
                    fl = finalParts[0]
                    fr = finalParts[0]
                    rl = finalParts[0]
                    rr = finalParts[0]
                }
            }

            // Set Texts
            views.setTextViewText(R.id.widget_tire_fl, fl)
            views.setTextViewText(R.id.widget_tire_fr, fr)
            views.setTextViewText(R.id.widget_tire_rl, rl)
            views.setTextViewText(R.id.widget_tire_rr, rr)

            // Footer: Last Update
            views.setTextViewText(R.id.widget_tire_footer, "Updated $lastUpdate")

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
            views.setOnClickPendingIntent(R.id.widget_title, openPendingIntent)

            appWidgetManager.updateAppWidget(appWidgetId, views)
        }
    }
}
