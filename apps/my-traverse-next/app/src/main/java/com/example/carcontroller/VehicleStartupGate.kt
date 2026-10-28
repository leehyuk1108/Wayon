package com.example.carcontroller

/** Display the newest known snapshot without waiting for a slower direct read. */
internal class VehicleStartupGate<T> {
    var generation = 0
        private set
    var value: T? = null
        private set
    private var timestamp = Long.MIN_VALUE
    private var quality = Int.MIN_VALUE
    private var directPending = false
    private var cloudPending = false
    val loading: Boolean get() = value == null && (directPending || cloudPending)
    val refreshing: Boolean get() = directPending || cloudPending

    fun begin(direct: Boolean, cloud: Boolean): Int {
        generation += 1
        value = null
        timestamp = Long.MIN_VALUE
        quality = Int.MIN_VALUE
        directPending = direct
        cloudPending = cloud
        return generation
    }

    fun offerCached(requestGeneration: Int, candidate: T, epochMs: Long?, rank: Int = 0): Boolean {
        if (requestGeneration != generation) return false
        select(candidate, epochMs, rank)
        return true
    }

    fun complete(requestGeneration: Int, direct: Boolean, candidate: T?, epochMs: Long?, rank: Int = 0) : Boolean {
        if (requestGeneration != generation) return false
        if (direct) directPending = false else cloudPending = false
        if (candidate != null) select(candidate, epochMs, rank)
        return true
    }

    private fun select(candidate: T, epochMs: Long?, rank: Int) {
        val next = epochMs ?: Long.MIN_VALUE
        if (value == null || next > timestamp || (next == timestamp && rank >= quality)) {
            value = candidate
            timestamp = next
            quality = rank
        }
    }
}
