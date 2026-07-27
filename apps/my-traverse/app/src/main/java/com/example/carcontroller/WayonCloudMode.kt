package com.example.carcontroller

import android.content.Context

object WayonCloudMode {
    fun isEnabled(context: Context): Boolean = context
        .getSharedPreferences(MainActivity.PREFS_NAME, Context.MODE_PRIVATE)
        .getString(MainActivity.PREF_KEY_WAYON_CLOUD_KEY, null)
        ?.isNotBlank() == true

    fun clearLocalTrackingState(context: Context) {
        context.getSharedPreferences(MainActivity.PREFS_NAME, Context.MODE_PRIVATE)
            .edit()
            .putBoolean(DrivingService.PREF_KEY_IS_DRIVING_ACTIVE, false)
            .remove(DrivingService.PREF_KEY_TEMP_START_TIME)
            .remove(DrivingService.PREF_KEY_TEMP_DIST)
            .remove(DrivingService.PREF_KEY_TEMP_TOP_SPEED)
            .remove(DrivingService.PREF_KEY_LAST_UPDATE_TIME)
            .remove(DrivingService.PREF_KEY_TEMP_START_ADDRESS)
            .apply()
    }
}
