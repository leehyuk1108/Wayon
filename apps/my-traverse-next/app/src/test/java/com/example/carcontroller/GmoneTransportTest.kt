package com.example.carcontroller

import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.net.URL
import java.net.URLConnection
import java.net.URLStreamHandler
import java.security.cert.Certificate
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import javax.net.ssl.HttpsURLConnection
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.BeforeClass
import org.junit.Test

/** Exercise the production JSON transport without reaching a vehicle or real server. */
class GmoneTransportTest {
    companion object {
        @Volatile private var responder: ((JSONObject) -> JSONObject)? = null

        @JvmStatic @BeforeClass fun interceptHttps() {
            URL.setURLStreamHandlerFactory { protocol ->
                if (protocol != "https") null else object : URLStreamHandler() {
                    override fun openConnection(url: URL): URLConnection {
                        check(url.host == "mp.gmone.co.kr") { "Unexpected test network destination" }
                        return object : HttpsURLConnection(url) {
                            val sent = ByteArrayOutputStream()
                            val response: ByteArray by lazy {
                                val handler = responder ?: error("No test responder installed")
                                handler(JSONObject(sent.toString("UTF-8"))).toString().toByteArray()
                            }
                            override fun getOutputStream() = sent
                            override fun getResponseCode(): Int { response; return 200 }
                            override fun getInputStream() = ByteArrayInputStream(response)
                            override fun connect() = Unit
                            override fun disconnect() = Unit
                            override fun usingProxy() = false
                            override fun getCipherSuite() = "TEST"
                            override fun getLocalCertificates(): Array<Certificate>? = null
                            override fun getServerCertificates(): Array<Certificate> = emptyArray()
                        }
                    }
                }
            }
        }
    }

    private val operations = CopyOnWriteArrayList<Int>()
    private val executor = Executors.newFixedThreadPool(3)

    @Before fun reset() {
        GmoneAccountClient.clearSession()
    }

    @After fun finish() {
        executor.shutdownNow()
        assertTrue(executor.awaitTermination(5, TimeUnit.SECONDS))
        responder = null
        GmoneAccountClient.clearSession()
    }

    private fun serve(body: (Int, JSONObject) -> JSONObject) {
        responder = { request ->
            val operation = request.getJSONObject("header").getInt("id")
            operations.add(operation)
            if (operation == 8) JSONObject(
                """{"login":{"success":0,"user_info_uuid":"test-user","token_key":"test-token"},"body":{"success":0}}""",
            ) else body(operation, request)
        }
    }

    private fun status() = JSONObject(
        """{"timestamp":1791770000000,"body":{"success":0,"car_status":{"volt":12500,"fRng":250}}}""",
    )

    @Test fun commandIsTransmittedWhileStartupStatusIsWaiting() {
        val statusEntered = CountDownLatch(1)
        val releaseStatus = CountDownLatch(1)
        serve { op, request ->
            when (op) {
                21 -> {
                    statusEntered.countDown()
                    check(releaseStatus.await(5, TimeUnit.SECONDS))
                    status()
                }
                19 -> {
                    assertEquals(1, request.getJSONObject("body").getInt("control_type"))
                    assertEquals(0, request.getJSONObject("body").getInt("request_option"))
                    JSONObject("""{"body":{"success":0,"control_type":1,"request_option":0}}""")
                }
                else -> error("Unexpected operation $op")
            }
        }
        val read = executor.submit<GmoneAccountClient.VehicleStatus> {
            GmoneAccountClient.fetchVehicleStatus("test", "password", includeModuleDetails = false)
        }
        try {
            assertTrue(statusEntered.await(3, TimeUnit.SECONDS))
            val command = executor.submit<String> {
                GmoneAccountClient.sendExtendedVehicleControl("test", "password", "DOOR_LOCK")
            }
            assertTrue(command.get(2, TimeUnit.SECONDS).isNotBlank())
            assertFalse(read.isDone)
            assertEquals(listOf(8, 21, 19), operations.toList())
        } finally {
            releaseStatus.countDown()
        }
        assertEquals("250", read.get(3, TimeUnit.SECONDS).data.getString("range"))
    }

    @Test fun ambiguousCommandFailureIsNotAutomaticallyRepeated() {
        serve { op, _ ->
            assertEquals(19, op)
            throw IOException("Simulated connection loss after dispatch")
        }
        assertThrows(IOException::class.java) {
            GmoneAccountClient.sendExtendedVehicleControl("test", "password", "DOOR_LOCK")
        }
        assertEquals(listOf(8, 19), operations.toList())
    }

    @Test fun pendingCommandPollsItsTicketWithoutResendingCommand() {
        var resultChecks = 0
        serve { op, request ->
            when (op) {
                19 -> JSONObject("""{"body":{"wait_response":true,"ticket_uuid":"command-ticket"}}""")
                66 -> {
                    assertEquals("command-ticket", request.getJSONObject("body").getString("ticket_uuid"))
                    resultChecks++
                    if (resultChecks == 1) JSONObject("""{"body":{}}""") else
                        JSONObject("""{"body":{"fetched_data":{"body":{"success":0,"control_type":1,"request_option":0}}}}""")
                }
                else -> error("Unexpected operation $op")
            }
        }
        assertTrue(GmoneAccountClient.sendExtendedVehicleControl("test", "password", "DOOR_LOCK").isNotBlank())
        assertEquals(listOf(8, 19, 66, 66), operations.toList())
    }

    @Test fun busyCommandIsNotResent() {
        serve { op, _ ->
            assertEquals(19, op)
            JSONObject("""{"body":{"success":12}}""")
        }
        assertThrows(IOException::class.java) {
            GmoneAccountClient.sendExtendedVehicleControl("test", "password", "DOOR_LOCK")
        }
        assertEquals(listOf(8, 19), operations.toList())
    }

    @Test fun settingsWriteVerificationDoesNotJoinAnOlderPendingRead() {
        val staleReadStarted = CountDownLatch(1)
        val releaseStaleRead = CountDownLatch(1)
        val settingsReads = AtomicInteger()
        var staleRead: java.util.concurrent.Future<JSONObject>? = null
        serve { op, _ ->
            when (op) {
                59 -> {
                    val index = settingsReads.incrementAndGet()
                    if (index == 2) {
                        staleReadStarted.countDown()
                        check(releaseStaleRead.await(5, TimeUnit.SECONDS))
                    }
                    JSONObject().put("body", JSONObject().put("success", 0)
                        .put("multipack_option", JSONObject().put("all_function_stop", if (index >= 3) 1 else 0)))
                }
                61 -> {
                    staleRead = executor.submit<JSONObject> {
                        GmoneAccountClient.fetchMultipackSettings("test", "password")
                    }
                    check(staleReadStarted.await(3, TimeUnit.SECONDS))
                    JSONObject("""{"body":{"success":0}}""")
                }
                else -> error("Unexpected operation $op")
            }
        }
        val save = executor.submit<JSONObject> {
            GmoneAccountClient.saveMultipackSettings("test", "password", JSONObject().put("all_function_stop", 1))
        }
        try {
            assertEquals(1, save.get(3, TimeUnit.SECONDS).getInt("all_function_stop"))
            assertFalse(staleRead!!.isDone)
            assertEquals(3, settingsReads.get())
        } finally {
            releaseStaleRead.countDown()
        }
        assertEquals(0, staleRead!!.get(3, TimeUnit.SECONDS).getInt("all_function_stop"))
    }

    @Test fun expiredAuthenticationIsInvalidatedButCommandIsNotRetried() {
        var expired = true
        serve { op, _ ->
            assertEquals(19, op)
            if (expired) JSONObject("""{"login":{"success":1},"body":{"success":1}}""")
            else JSONObject("""{"body":{"success":0}}""")
        }
        assertThrows(IOException::class.java) {
            GmoneAccountClient.sendExtendedVehicleControl("test", "password", "DOOR_LOCK")
        }
        assertEquals(listOf(8, 19), operations.toList())
        expired = false
        GmoneAccountClient.sendExtendedVehicleControl("test", "password", "DOOR_LOCK")
        assertEquals(listOf(8, 19, 8, 19), operations.toList())
    }

    @Test fun basicInformationArrivesBeforeModuleReadsAndIsNotMutated() {
        var basic: GmoneAccountClient.VehicleStatus? = null
        serve { op, _ ->
            when (op) {
                21 -> status()
                59 -> {
                    assertNotNull(basic)
                    JSONObject("""{"body":{"success":0,"multipack_option":{"all_function_stop":1}}}""")
                }
                63 -> JSONObject("""{"body":{"success":0,"multipack_info":{"version":1}}}""")
                else -> error("Unexpected operation $op")
            }
        }
        val full = GmoneAccountClient.fetchVehicleStatus("test", "password", onBasicStatus = { basic = it })
        assertEquals(listOf(8, 21, 59, 63), operations.toList())
        assertFalse(basic!!.data.getJSONObject("gmone_details").has("module"))
        val module = full.data.getJSONObject("gmone_details").getJSONObject("module")
        assertEquals(1, module.getJSONObject("settings").getInt("all_function_stop"))
        assertEquals(1, module.getJSONObject("info").getJSONObject("multipack_info").getInt("version"))
    }

    @Test fun failedModuleReadStillReturnsCurrentBasicStatus() {
        serve { op, _ ->
            if (op == 21) status() else throw IOException("Module unavailable")
        }
        val full = GmoneAccountClient.fetchVehicleStatus("test", "password")
        assertEquals("250", full.data.getString("range"))
        assertFalse(full.data.getJSONObject("gmone_details").has("module"))
    }

    @Test fun controlInProgressSkipsSupplementalVehicleQueries() {
        serve { op, _ -> assertEquals(21, op); status() }
        val result = GmoneAccountClient.fetchVehicleStatus(
            "test", "password", canReadModuleDetails = { false },
        )
        assertEquals("250", result.data.getString("range"))
        assertEquals(listOf(8, 21), operations.toList())
    }

    @Test fun commandArrivingDuringSettingsReadPreventsFollowingModuleQuery() {
        var readDetails = true
        serve { op, _ ->
            when (op) {
                21 -> status()
                59 -> {
                    readDetails = false
                    JSONObject("""{"body":{"success":0,"multipack_option":{"all_function_stop":1}}}""")
                }
                else -> error("Unexpected operation $op")
            }
        }
        val result = GmoneAccountClient.fetchVehicleStatus(
            "test", "password", canReadModuleDetails = { readDetails },
        )
        assertEquals(listOf(8, 21, 59), operations.toList())
        assertEquals(1, result.data.getJSONObject("gmone_details").getJSONObject("module")
            .getJSONObject("settings").getInt("all_function_stop"))
    }

    @Test fun cancelledScreenDoesNotSendSupplementalQueries() {
        serve { op, _ -> assertEquals(21, op); status() }
        assertThrows(java.util.concurrent.CancellationException::class.java) {
            GmoneAccountClient.fetchVehicleStatus("test", "password", onBasicStatus = {
                throw java.util.concurrent.CancellationException("Screen closed")
            })
        }
        assertEquals(listOf(8, 21), operations.toList())
    }
}
