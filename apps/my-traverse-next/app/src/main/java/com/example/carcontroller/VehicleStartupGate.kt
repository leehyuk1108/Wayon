package com.example.carcontroller

/** Keep the older cloud snapshot hidden while the foreground account read is pending. */
internal class VehicleStartupGate<T> {
    var generation = 0
        private set
    var value: T? = null
        private set
    private var timestamp = Long.MIN_VALUE
    private var directPending = false
    private var cloudPending = false
    val loading: Boolean get() = directPending || (value == null && cloudPending)

    fun begin(direct: Boolean, cloud: Boolean): Int {
        generation += 1
        value = null
        timestamp = Long.MIN_VALUE
        directPending = direct
        cloudPending = cloud
        return generation
    }

    fun complete(requestGeneration: Int, direct: Boolean, candidate: T?, epochMs: Long?) : Boolean {
        if (requestGeneration != generation) return false
        if (direct) directPending = false else cloudPending = false
        if (candidate != null && (value == null || (epochMs ?: Long.MIN_VALUE) >= timestamp)) {
            value = candidate
            timestamp = epochMs ?: Long.MIN_VALUE
        }
        return true
    }
}
