package com.example.carcontroller

import java.lang.ref.WeakReference

object GlobalHelper {
    private var mainActivityRef: WeakReference<MainActivity>? = null

    fun registerActivity(activity: MainActivity) {
        mainActivityRef = WeakReference(activity)
    }

    fun unregisterActivity() {
        mainActivityRef?.clear()
        mainActivityRef = null
    }

    fun getMainActivity(): MainActivity? {
        return mainActivityRef?.get()
    }
}
