package com.example.carcontroller

import java.io.IOException

/** Poll an existing result ticket only; never resend the original operation. */
internal class GmoneResultPoller(
    private val nowMs: () -> Long = { System.nanoTime() / 1_000_000 },
    private val sleepMs: (Long) -> Unit = { Thread.sleep(it) },
) {
    fun <T : Any> await(fetchResult: () -> T?): T {
        val startedAt = nowMs()
        repeat(20) { attempt ->
            val elapsed = nowMs() - startedAt
            val remaining = 30_000L - elapsed
            if (remaining <= 0) throw timeout()
            val interval = when {
                attempt == 0 -> 250L
                elapsed < 12_000L -> 1_000L
                elapsed < 20_000L -> 2_000L
                else -> 5_000L
            }
            sleepMs(minOf(interval, remaining))
            fetchResult()?.let { return it }
        }
        throw timeout()
    }

    private fun timeout() = IOException("멀티팩 처리 결과 확인 시간이 초과되었습니다. 상태를 확인한 후 다시 요청해 주세요.")
}
