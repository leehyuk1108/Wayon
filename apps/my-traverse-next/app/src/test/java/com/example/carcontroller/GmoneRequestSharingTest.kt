package com.example.carcontroller

import java.io.IOException
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import org.junit.Assert.*
import org.junit.Test

class GmoneRequestSharingTest {
    @Test fun authenticationIsSharedButExpiresAndClearsOnAccountChange() {
        var now = 0L
        val cache = GmoneSessionCache<Any>(100) { now }
        val original = cache.get("account-a") { Any() }
        assertSame(original, cache.get("account-a") { error("duplicate login") })
        now = 100
        val renewed = cache.get("account-a") { Any() }
        assertNotSame(original, renewed)
        cache.invalidateIf { it === original }
        assertSame(renewed, cache.get("account-a") { error("old failure cleared new session") })
        assertNotSame(renewed, cache.get("account-b") { Any() })
        cache.clear()
        assertNotSame(renewed, cache.get("account-a") { Any() })
    }

    @Test fun failedAuthenticationIsNotCached() {
        val cache = GmoneSessionCache<String>()
        assertThrows(IOException::class.java) { cache.get("a") { throw IOException("rejected") } }
        assertEquals("success", cache.get("a") { "success" })
    }

    @Test fun concurrentLoginUsesOneRequest() {
        val cache = GmoneSessionCache<Any>()
        val pool = Executors.newFixedThreadPool(4)
        val count = AtomicInteger()
        try {
            val calls = (1..4).map { pool.submit<Any> { cache.get("a") { count.incrementAndGet(); Any() } } }
            val values = calls.map { it.get(2, TimeUnit.SECONDS) }
            assertEquals(1, count.get())
            values.forEach { assertSame(values.first(), it) }
        } finally { pool.shutdownNow() }
    }

    @Test fun logoutDoesNotWaitForNetworkOrRestorePendingSession() {
        val cache = GmoneSessionCache<String>()
        val pool = Executors.newFixedThreadPool(2)
        val started = CountDownLatch(1)
        val release = CountDownLatch(1)
        try {
            val login = pool.submit<String> {
                cache.get("a") { started.countDown(); release.await(); "old" }
            }
            assertTrue(started.await(2, TimeUnit.SECONDS))
            pool.submit { cache.clear() }.get(1, TimeUnit.SECONDS)
            assertEquals("new", cache.get("a") { "new" })
            release.countDown()
            assertEquals("old", login.get(2, TimeUnit.SECONDS))
            assertEquals("new", cache.get("a") { error("pending login replaced the current session") })
        } finally { release.countDown(); pool.shutdownNow() }
    }

    @Test fun pendingStatusDoesNotBlockCommandOrAnotherAccount() {
        val cache = GmoneSessionCache<String>()
        val reads = GmoneSingleFlight<String>()
        val pool = Executors.newFixedThreadPool(3)
        val started = CountDownLatch(1)
        val release = CountDownLatch(1)
        try {
            val status = pool.submit<String> {
                cache.get("a") { "session" }
                reads.read("a") { started.countDown(); release.await(); "fresh" }
            }
            assertTrue(started.await(2, TimeUnit.SECONDS))
            val command = pool.submit<String> {
                cache.get("a") { error("command logged in again") }
                "sent-once"
            }
            assertEquals("sent-once", command.get(1, TimeUnit.SECONDS))
            assertEquals("other", reads.read("b") { "other" })
            assertFalse(status.isDone)
            release.countDown()
            assertEquals("fresh", status.get(2, TimeUnit.SECONDS))
            assertEquals("new-read", reads.read("a") { "new-read" })
        } finally { release.countDown(); pool.shutdownNow() }
    }

    @Test fun failedStatusDoesNotPoisonNextRead() {
        val reads = GmoneSingleFlight<String>()
        assertThrows(IOException::class.java) { reads.read("a") { throw IOException("offline") } }
        assertEquals("fresh", reads.read("a") { "fresh" })
    }

    @Test fun simultaneousStatusAndEngineCheckShareOnlyThePendingRead() {
        val reads = GmoneSingleFlight<String>()
        val pool = Executors.newFixedThreadPool(2)
        val started = CountDownLatch(1)
        val release = CountDownLatch(1)
        val secondEntered = CountDownLatch(1)
        val count = AtomicInteger()
        try {
            val first = pool.submit<String> {
                reads.read("a") { count.incrementAndGet(); started.countDown(); release.await(); "fresh" }
            }
            assertTrue(started.await(2, TimeUnit.SECONDS))
            val second = pool.submit<String> {
                secondEntered.countDown()
                reads.read("a") { count.incrementAndGet(); "unexpected" }
            }
            assertTrue(secondEntered.await(2, TimeUnit.SECONDS))
            // The second reader must be waiting on the first, not executing a second request.
            assertThrows(java.util.concurrent.TimeoutException::class.java) { second.get(100, TimeUnit.MILLISECONDS) }
            release.countDown()
            assertEquals("fresh", first.get(2, TimeUnit.SECONDS))
            assertEquals("fresh", second.get(2, TimeUnit.SECONDS))
            assertEquals(1, count.get())
        } finally { release.countDown(); pool.shutdownNow() }
    }
}
