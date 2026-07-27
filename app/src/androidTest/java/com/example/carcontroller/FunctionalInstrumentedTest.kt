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
class FunctionalInstrumentedTest {
    @Test
    fun testVentilationLogic() {
        val scenario = ActivityScenario.launch(MainActivity::class.java)
        val latch = CountDownLatch(1)

        scenario.onActivity { activity ->
            try {
                // 1. Set Virtual Bluetooth
                val btField = MainActivity::class.java.getDeclaredField("isBluetoothConnected_VIRTUAL")
                btField.isAccessible = true
                btField.setBoolean(activity, true)
                Log.d("FunctionalTest", "Virtual bluetooth set to true")

                // 2. Instantiate WebAppInterface (inner class)
                // Class name is usually MainActivity$WebAppInterface
                val outerClass = MainActivity::class.java
                val innerClasses = outerClass.declaredClasses
                var webInterfaceClass: Class<*>? = null

                for (cls in innerClasses) {
                    if (cls.simpleName == "WebAppInterface") {
                        webInterfaceClass = cls
                        break
                    }
                }

                if (webInterfaceClass == null) {
                    fail("Could not find WebAppInterface inner class")
                    return@onActivity // Check compiler logic
                }

                // Construct it: Inner classes need the outer definition
                val constructor = webInterfaceClass!!.getDeclaredConstructor(outerClass)
                constructor.isAccessible = true
                val webInterfaceInstance = constructor.newInstance(activity)

                // 3. Invoke method on the INTERFACE instance
                val method = webInterfaceClass.getDeclaredMethod("handleVentilationToggle")
                method.isAccessible = true
                method.invoke(webInterfaceInstance)
                Log.d("FunctionalTest", "Invoked handleVentilationToggle on WebAppInterface")

                // 4. Check result on the ACTIVITY instance
                val field = MainActivity::class.java.getDeclaredField("isVentilating")
                field.isAccessible = true
                val isVentilating = field.getBoolean(activity)
                Log.d("FunctionalTest", "isVentilating: " + isVentilating)

                // Assert it turned TRUE (since default was false and we toggled)
                // Note: Logic allows it if !isVentilating && isBtOn.
                if (!isVentilating) {
                   fail("Ventilation did not start even though BT was virtual-connected")
                }

            } catch (e: Exception) {
                Log.e("FunctionalTest", "Error in test", e)
                fail("Exception: " + e.toString() + " Cause: " + e.cause)
            }
            latch.countDown()
        }
        latch.await(3, TimeUnit.SECONDS)
        scenario.close()
    }
}
