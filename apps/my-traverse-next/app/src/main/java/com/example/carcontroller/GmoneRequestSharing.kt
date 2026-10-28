package com.example.carcontroller

import java.util.concurrent.CompletableFuture
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.ExecutionException

/** Share authentication without holding a state lock during network operations. */
internal class GmoneSessionCache<T>(
    private val ttlMs: Long = 120_000,
    private val nowMs: () -> Long = { System.nanoTime() / 1_000_000 },
) {
    private var key: String? = null
    private var value: T? = null
    private var expiresAt = 0L
    private var generation = 0L
    private val pending = GmoneSingleFlight<T>()

    fun get(accountKey: String, authenticate: () -> T): T {
        val requestGeneration = synchronized(this) {
            validValue(accountKey)?.let { return it }
            generation
        }
        return pending.read("$requestGeneration:$accountKey") {
            synchronized(this) { validValue(accountKey) } ?: authenticate().also { authenticated ->
                synchronized(this) {
                    // A logout or explicit invalidation must not resurrect an old login.
                    if (generation == requestGeneration) {
                        key = accountKey
                        value = authenticated
                        expiresAt = nowMs() + ttlMs
                    }
                }
            }
        }
    }

    private fun validValue(accountKey: String): T? =
        value?.takeIf { key == accountKey && nowMs() < expiresAt }

    @Synchronized fun invalidateIf(matches: (T) -> Boolean) {
        if (value?.let(matches) == true) clear()
    }

    @Synchronized fun clear() {
        generation += 1
        key = null
        value = null
        expiresAt = 0L
    }
}

/** Deduplicate concurrent read-only requests, without caching old vehicle data. */
internal class GmoneSingleFlight<T> {
    private val pending = ConcurrentHashMap<String, CompletableFuture<T>>()

    fun read(key: String, request: () -> T): T {
        val own = CompletableFuture<T>()
        val existing = pending.putIfAbsent(key, own)
        if (existing != null) {
            try {
                return existing.get()
            } catch (error: ExecutionException) {
                throw error.cause ?: error
            }
        }
        try {
            return request().also { own.complete(it) }
        } catch (error: Throwable) {
            own.completeExceptionally(error)
            throw error
        } finally {
            pending.remove(key, own)
        }
    }
}
