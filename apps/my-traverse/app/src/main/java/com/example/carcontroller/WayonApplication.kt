package com.example.carcontroller

import android.app.Application

class WayonApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        WayonImpactNotifications.ensureChannel(this)
        if (BuildConfig.FIREBASE_CONFIGURED) {
            WayonPushRegistrar.registerCurrentToken(this)
        }
    }
}
