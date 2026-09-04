package com.example.carcontroller

import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.core.app.ActivityScenario
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.Assert.*

/**
 * Instrumented test, which will execute on an Android device.
 *
 * See [testing documentation](http://d.android.com/tools/testing).
 */
@RunWith(AndroidJUnit4::class)
class ExampleInstrumentedTest {
    @Test
    fun selfDiagnostics() {
        // 1. Context & Package Verification
        val appContext = InstrumentationRegistry.getInstrumentation().targetContext
        assertEquals("com.example.carcontroller", appContext.packageName)

        // 2. Activity & UI Verification
        // Launch the activity to ensure it starts without crashing
        val scenario = ActivityScenario.launch(MainActivity::class.java)
        scenario.onActivity { activity ->
            // Verify the Activity is not null
            assertNotNull(activity)

            // Verify the core WebView component exists
            val webView = activity.findViewById<android.view.View>(R.id.webview)
            assertNotNull("WebView component is missing from layout", webView)
        }
        scenario.close()
    }
}
