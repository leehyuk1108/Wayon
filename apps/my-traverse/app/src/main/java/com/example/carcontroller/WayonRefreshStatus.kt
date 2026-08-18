package com.example.carcontroller

internal data class WayonRefreshStatus(
    val pending: Boolean,
    val requestedAt: String?,
    val completedAt: String?,
)

internal object WayonRefreshCompletionPolicy {
    fun isComplete(expectedRequestAt: String, status: WayonRefreshStatus): Boolean =
        !status.pending &&
            status.requestedAt == expectedRequestAt &&
            !status.completedAt.isNullOrBlank()
}
