package com.example.carcontroller

import org.junit.Test

import org.junit.Assert.*

/**
 * Example local unit test, which will execute on the development machine (host).
 *
 * See [testing documentation](http://d.android.com/tools/testing).
 */
class ExampleUnitTest {
    @Test
    fun addition_isCorrect() {
        assertEquals(4, 2 + 2)
    }

    @Test
    fun directTirePressure_isConvertedToKpa() {
        assertEquals(268.0, GmoneAccountClient.normalizeTirePressureKpa(67.0), 0.0)
        assertEquals(252.0, GmoneAccountClient.normalizeTirePressureKpa(252.0), 0.0)
    }

    @Test
    fun cloudTirePressureText_isNormalizedWithoutDoubleConversion() {
        assertEquals(
            "타이어 정보\n268 kpa\n272 kpa\n272 kpa\n280 kpa",
            MainActivity.normalizeTirePressureText("타이어 정보\n67 kpa\n68 kpa\n68 kpa\n70 kpa"),
        )
        assertEquals(
            "타이어 정보\n268 kpa\n272 kpa",
            MainActivity.normalizeTirePressureText("타이어 정보\n268 kpa\n272 kpa"),
        )
    }
}
