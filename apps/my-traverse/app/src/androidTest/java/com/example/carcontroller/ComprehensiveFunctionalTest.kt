package com.example.carcontroller

import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.core.app.ActivityScenario
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.Assert.*
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import android.util.Log

@RunWith(AndroidJUnit4::class)
class ComprehensiveFunctionalTest {

    @Test
    fun testAllFeatures() {
        Log.d("CompTest", "Starting Revised Test")
        // Use example.com which is lighter and stable
        val mockUrl = "https://www.example.com"

        val scenario = ActivityScenario.launch(MainActivity::class.java)
        Thread.sleep(1000)

        // Setup
        scenario.onActivity { activity ->
            val urlField = MainActivity::class.java.getDeclaredField("baseApiUrl")
            urlField.isAccessible = true
            urlField.set(activity, mockUrl)

            val btField = MainActivity::class.java.getDeclaredField("isBluetoothConnected_VIRTUAL")
            btField.isAccessible = true
            btField.setBoolean(activity, false)
        }

        // --- TEST 1: VENTILATION (Simpler flow) ---
        Log.d("CompTest", "TEST STEP: Ventilation")
        scenario.onActivity { activity ->
             val outerClass = MainActivity::class.java
             val innerClasses = outerClass.declaredClasses
             val webInterfaceClass = innerClasses.find { it.simpleName == "WebAppInterface" }!!
             val constructor = webInterfaceClass.getDeclaredConstructor(outerClass)
             constructor.isAccessible = true
             val webInterfaceInstance = constructor.newInstance(activity)

            // Invoke public method
            val ventMethod = webInterfaceClass.getDeclaredMethod("handleVentilationToggle")
            ventMethod.isAccessible = true
            ventMethod.invoke(webInterfaceInstance)
            Log.d("CompTest", "Invoked handleVentilationToggle")
        }

        var isVentilating = false
        for (i in 1..20) {
            Thread.sleep(1000)
             scenario.onActivity { activity ->
                val ventField = MainActivity::class.java.getDeclaredField("isVentilating")
                ventField.isAccessible = true
                isVentilating = ventField.getBoolean(activity)
             }
             if (isVentilating) break
        }
        if (isVentilating) Log.d("CompTest", "✅ Ventilation Verified")
        else Log.e("CompTest", "❌ Ventilation Failed")

        // Assert later to allow other tests to try? No, fail fast is better to read logs.
        assertTrue("Ventilation Start Failed", isVentilating)


        // --- TEST 2: ENGINE START (Private Inner Method) ---
        Log.d("CompTest", "TEST STEP: Engine Start")
        scenario.onActivity { activity ->
            val outerClass = MainActivity::class.java
            val innerClasses = outerClass.declaredClasses
            val webInterfaceClass = innerClasses.find { it.simpleName == "WebAppInterface" }!!
            val constructor = webInterfaceClass.getDeclaredConstructor(outerClass)
            constructor.isAccessible = true
            val webInterfaceInstance = constructor.newInstance(activity)

            // Try to find handleEngineStart in WebAppInterface
            // It might be 'private' so getDeclaredMethod is needed.
            // parameter is buttonId (String)
            try {
                val engineMethod = webInterfaceClass.getDeclaredMethod("handleEngineStart", String::class.java)
                engineMethod.isAccessible = true
                engineMethod.invoke(webInterfaceInstance, "btnEngineStart")
                Log.d("CompTest", "Invoked handleEngineStart directly on Inner Class")
            } catch (e: NoSuchMethodException) {
                Log.e("CompTest", "handleEngineStart not found in WebAppInterface. Trying checks...", e)
                // Fallback to searching methods
                val methods = webInterfaceClass.declaredMethods
                for (m in methods) Log.d("CompTest", "InnerMethod: " + m.name)
                fail("Could not find handleEngineStart")
            }
        }

        var isEngineOn = false
        for (i in 1..20) {
            Thread.sleep(1000)
            scenario.onActivity { activity ->
                val engineField = MainActivity::class.java.getDeclaredField("isEngineOn")
                engineField.isAccessible = true
                isEngineOn = engineField.getBoolean(activity)
            }
            if (isEngineOn) break
        }
         if (isEngineOn) Log.d("CompTest", "✅ Engine Verified")
        else Log.e("CompTest", "❌ Engine Failed")

        assertTrue("Engine Start Failed", isEngineOn)

        scenario.close()
    }
}
