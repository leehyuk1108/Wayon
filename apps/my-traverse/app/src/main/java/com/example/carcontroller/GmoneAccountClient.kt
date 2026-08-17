package com.example.carcontroller

import java.io.IOException
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import javax.net.ssl.HttpsURLConnection
import org.json.JSONArray
import org.json.JSONObject

object GmoneAccountClient {
    private const val SERVER_URL = "https://mp.gmone.co.kr:28354"
    private const val LOGIN_OPERATION = 8
    private const val STATUS_OPERATION = 21
    private const val RESULT_OPERATION = 66

    data class LoginResult(val vehicleCount: Int)
    data class VehicleStatus(val data: JSONObject, val updatedAt: String)
    private data class Session(val login: JSONObject, val vehicleCount: Int)

    fun login(email: String, password: String): LoginResult {
        return LoginResult(authenticate(email, password).vehicleCount)
    }

    fun fetchVehicleStatus(email: String, password: String): VehicleStatus {
        val session = authenticate(email, password)
        val initial = request(
            path = "/b1_connect_m",
            operation = STATUS_OPERATION,
            login = session.login,
            body = JSONObject().put("refresh_dtc", false).put("last_received_time", 0),
        )
        val resolved = resolveResult(session.login, initial)
        val body = resolved.optJSONObject("body") ?: throw IOException("차량 상태 응답이 없습니다.")
        val resultCode = body.optInt("success", -1)
        if (resultCode != 0) throw IOException(statusError(resultCode))
        val carStatus = body.optJSONObject("car_status") ?: throw IOException("차량 상태 값이 없습니다.")
        val timestamp = resolved.optLong("timestamp", System.currentTimeMillis())
        return VehicleStatus(
            normalizeStatus(carStatus, timestamp, body.optJSONArray("running_cycles_data")),
            formatKst(timestamp),
        )
    }

    private fun authenticate(email: String, password: String): Session {
        val payload = JSONObject()
            .put("header", JSONObject().put("id", LOGIN_OPERATION).put("ticket_id", 0).put("revision", 0))
            .put("login", JSONObject().put("email", email.trim()).put("password", password))
            .put("body", JSONObject())
        val root = post("$SERVER_URL/b1_init", payload)
        val login = root.optJSONObject("login") ?: throw IOException("로그인 응답이 없습니다.")
        val body = root.optJSONObject("body") ?: JSONObject()
        if (login.optInt("success", -1) != 0 || body.optInt("success", -1) != 0) {
            throw IOException("아이디 또는 비밀번호를 확인하세요.")
        }
        val uuid = login.optString("user_info_uuid").takeIf { it.isNotBlank() }
            ?: login.optJSONObject("user_info")?.optString("user_uuid")?.takeIf { it.isNotBlank() }
            ?: throw IOException("멀티팩 계정 식별자가 없습니다.")
        val token = login.optString("token_key").takeIf { it.isNotBlank() }
            ?: throw IOException("멀티팩 로그인 토큰이 없습니다.")
        val carInfo = login.optJSONObject("car_info")
        return Session(
            login = JSONObject().put("uuid", uuid).put("token_key", token),
            vehicleCount = carInfo?.length() ?: 0,
        )
    }

    private fun request(path: String, operation: Int, login: JSONObject, body: JSONObject): JSONObject {
        val payload = JSONObject()
            .put("header", JSONObject().put("id", operation).put("ticket_id", 0).put("revision", 0))
            .put("login", login)
            .put("body", body)
        return post("$SERVER_URL$path", payload)
    }

    private fun post(url: String, payload: JSONObject): JSONObject {
        val connection = URL(url).openConnection() as HttpsURLConnection
        connection.requestMethod = "POST"
        connection.doOutput = true
        connection.useCaches = false
        connection.connectTimeout = 20_000
        connection.readTimeout = 20_000
        connection.setRequestProperty("Content-Type", "application/json")
        connection.setRequestProperty("Accept", "application/json")

        return try {
            connection.outputStream.bufferedWriter(Charsets.UTF_8).use { it.write(payload.toString()) }
            val responseCode = connection.responseCode
            val stream = if (responseCode in 200..299) connection.inputStream else connection.errorStream
            val response = stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }.orEmpty()
            if (responseCode !in 200..299) throw IOException("멀티팩 서버 HTTP $responseCode")
            runCatching { JSONObject(response) }
                .getOrElse { throw IOException("멀티팩 서버 응답을 해석할 수 없습니다.") }
        } finally {
            connection.disconnect()
        }
    }

    private fun resolveResult(login: JSONObject, initial: JSONObject): JSONObject {
        val body = initial.optJSONObject("body") ?: JSONObject()
        val ticket = body.optString("ticket_uuid")
        if (!body.optBoolean("wait_response", false) || ticket.isBlank()) return initial

        repeat(10) {
            Thread.sleep(3_000)
            val fetched = request(
                path = "/b1_connect_m",
                operation = RESULT_OPERATION,
                login = login,
                body = JSONObject().put("ticket_uuid", ticket),
            )
            fetched.optJSONObject("body")?.optJSONObject("fetched_data")?.let { return it }
        }
        throw IOException("차량 상태 조회 시간이 초과되었습니다.")
    }

    private fun normalizeStatus(
        carStatus: JSONObject,
        timestamp: Long,
        runningCycles: JSONArray? = null,
    ): JSONObject {
        val result = JSONObject()
        putNumberText(result, "battery", carStatus, "volt") { value ->
            when {
                value >= 1000 -> value / 1000
                value >= 100 -> value / 10
                else -> value
            }
        }
        putNumberText(result, "battery_level", carStatus, "btChrg")
        putNumberText(result, "battery_life", carStatus, "btHlth")
        putNumberText(result, "fuel", carStatus, "fLvl")
        number(carStatus.opt("odo"))?.let { value ->
            result.put("mileage", String.format(Locale.US, "%,.0f", value))
        }
        putNumberText(result, "oil", carStatus, "olLfe")
        putNumberText(result, "range", carStatus, "fRng")

        val tireKeys = listOf("trPrsLf", "trPrsLr", "trPrsRf", "trPrsRr")
        val tireValues = tireKeys.map { key ->
            number(carStatus.opt(key))?.let(::normalizeTirePressureKpa)?.let(::compactNumber) ?: "--"
        }
        if (tireValues.any { it != "--" }) {
            val tireText = buildString {
                append("타이어 정보")
                tireValues.forEach { value ->
                    append('\n').append(value).also { if (value != "--") append(" kpa") }
                }
            }
            result.put("tire_pressure", tireText)
            result.put("tire_pressure_all", tireText)
        }
        result.put("gmone_details", normalizeDetails(carStatus, runningCycles))
        result.put("last_update", formatKst(timestamp))
        result.put("source", "gmone-direct-android")
        result.put("collector_status", "success")
        result.put("refresh_status", "success")
        return result
    }

    internal fun normalizeDetails(carStatus: JSONObject, runningCycles: JSONArray? = null): JSONObject {
        val tires = JSONObject().apply {
            putNormalizedTire("frontLeftKpa", carStatus.opt("trPrsLf"))
            putNormalizedTire("frontRightKpa", carStatus.opt("trPrsRf"))
            putNormalizedTire("rearLeftKpa", carStatus.opt("trPrsLr"))
            putNormalizedTire("rearRightKpa", carStatus.opt("trPrsRr"))
        }
        val closures = JSONObject().apply {
            putBinaryState("doors", carStatus.opt("door"))
            putBinaryState("hood", carStatus.opt("hood"))
            putBinaryState("trunk", carStatus.opt("trunk"))
            putBinaryState("sunroof", carStatus.opt("srf"))
            putBinaryState("windowFrontLeft", carStatus.opt("winLf"))
            putBinaryState("windowFrontRight", carStatus.opt("winRf"))
            putBinaryState("windowRearLeft", carStatus.opt("winLr"))
            putBinaryState("windowRearRight", carStatus.opt("winRr"))
        }
        val diagnostics = normalizeDiagnostics(carStatus)
        val ev = JSONObject().apply {
            val values = linkedMapOf(
                "chargerCouplerStatusRaw" to "evChgrCplrStats",
                "chargerPowerLevelRaw" to "evChgrPwrLvl",
                "chargerSystemStatusRaw" to "evChgrSysStats",
                "chargeCompleteTimeRaw" to "evChrgCpltTm",
                "chargeCompleteTimeSetRaw" to "evChrgCpltTmSet",
                "chargeStartTimeRaw" to "evChrgStTm",
                "chargeStartTimeSetRaw" to "evChrgStTmSet",
                "chargeStatusRaw" to "evChrgStat",
                "rangeAverageKm" to "evRngAvg",
                "rangeMaximumKm" to "evRngMax",
                "rangeMinimumKm" to "evRngMin",
            )
            var supported = false
            values.forEach { (destination, source) ->
                number(carStatus.opt(source))?.let { value ->
                    put(destination, compactJsonNumber(value))
                    if (value != 0.0 && value != 4_294_934_896.0) supported = true
                }
            }
            put("supported", supported)
        }
        val rawStatus = JSONObject().apply {
            val keys = carStatus.keys()
            while (keys.hasNext()) {
                val key = keys.next()
                if (key == "dtc") continue
                val value = carStatus.opt(key)
                if (value is String || value is Number || value is Boolean) put(key, value)
            }
        }

        return JSONObject().apply {
            put("schemaVersion", "gmone-details-v1")
            put("fuel", JSONObject().apply {
                putNumberFrom(carStatus, "capacityLiters", "fCap")
                putNumberFrom(carStatus, "levelLiters", "fLvl")
                putNumberFrom(carStatus, "rangeKm", "fRng")
            })
            put("battery12v", JSONObject().apply {
                putNumberFrom(carStatus, "voltageV", "volt")
                putNumberFrom(carStatus, "chargePercent", "btChrg")
                putNumberFrom(carStatus, "healthPercent", "btHlth")
                putNumberFrom(carStatus, "temperatureC", "btTmp")
            })
            put("tires", tires)
            put("closures", closures)
            put("vehicleState", JSONObject().apply {
                putNumberFrom(carStatus, "engineRaw", "eng")
                putNumberFrom(carStatus, "lightRaw", "light")
                putNumberFrom(carStatus, "hornRaw", "hrnStats")
                putNumberFrom(carStatus, "statusCounterRaw", "bCnt")
                put("engineRunning", (number(carStatus.opt("eng")) ?: 0.0) != 0.0)
            })
            put("maintenance", JSONObject().apply {
                putNumberFrom(carStatus, "oilLifePercent", "olLfe")
                putNumberFrom(carStatus, "defLevelPercent", "defLvl")
                putNumberFrom(carStatus, "defRemainingDistanceKm", "defRmngDis")
            })
            put("diagnostics", diagnostics)
            put("remoteStart", JSONObject().apply {
                putNumberFrom(carStatus, "levelRaw", "rsiLvl")
                putNumberFrom(carStatus, "remainingStarts", "rvsRmng")
                putNumberFrom(carStatus, "remainingTimeRaw", "rvsRmngTm")
                put("remainingTimeValid", carStatus.optBoolean("rvsRmngTmVld", false))
            })
            put("ev", ev)
            put("rawStatus", rawStatus)
            normalizeRunningCycles(runningCycles)?.let { put("runningCycles", it) }
        }
    }

    private fun normalizeDiagnostics(carStatus: JSONObject): JSONObject {
        val records = JSONArray()
        var failedCount = 0
        val source = carStatus.optJSONArray("dtc") ?: JSONArray()
        for (index in 0 until source.length()) {
            val record = source.optJSONObject(index) ?: continue
            val safe = JSONObject()
            val keys = record.keys()
            while (keys.hasNext()) {
                val key = keys.next()
                val value = record.opt(key)
                if (value is String || value is Number || value is Boolean) safe.put(key, value)
            }
            if ((number(record.opt("fail")) ?: 0.0) != 0.0) failedCount += 1
            records.put(safe)
        }
        return JSONObject()
            .put("reportedCount", number(carStatus.opt("dtcCnt"))?.toInt() ?: records.length())
            .put("failedCount", failedCount)
            .put("records", records)
    }

    private fun normalizeRunningCycles(source: JSONArray?): JSONObject? {
        if (source == null || source.length() == 0) return null
        var distanceKm = 0.0
        var driveSeconds = 0.0
        var fuelUsedLiters = 0.0
        var firstTime: Long? = null
        var lastTime: Long? = null
        val records = mutableListOf<JSONObject>()
        for (index in 0 until source.length()) {
            val cycle = source.optJSONObject(index) ?: continue
            distanceKm += number(cycle.opt("dis")) ?: 0.0
            driveSeconds += number(cycle.opt("drvTm")) ?: 0.0
            fuelUsedLiters += number(cycle.opt("fuse")) ?: 0.0
            val time = number(cycle.opt("time"))?.toLong()
            if (time != null) {
                firstTime = firstTime?.let { minOf(it, time) } ?: time
                lastTime = lastTime?.let { maxOf(it, time) } ?: time
            }
            records += JSONObject(cycle.toString())
        }
        val recent = JSONArray()
        records.sortedByDescending { number(it.opt("time")) ?: 0.0 }
            .take(20)
            .forEach(recent::put)
        return JSONObject()
            .put("count", records.size)
            .put("totalDistanceKm", compactJsonNumber(distanceKm))
            .put("totalDriveSeconds", compactJsonNumber(driveSeconds))
            .put("totalFuelUsedLiters", compactJsonNumber(fuelUsedLiters))
            .put("firstCycleAt", firstTime)
            .put("lastCycleAt", lastTime)
            .put("recent", recent)
    }

    private fun JSONObject.putNumberFrom(source: JSONObject, destinationKey: String, sourceKey: String) {
        number(source.opt(sourceKey))?.let { put(destinationKey, compactJsonNumber(it)) }
    }

    private fun JSONObject.putNormalizedTire(key: String, raw: Any?) {
        number(raw)?.let(::normalizeTirePressureKpa)?.let { put(key, compactJsonNumber(it)) }
    }

    private fun JSONObject.putBinaryState(key: String, value: Any?) {
        number(value)?.let {
            put(key, JSONObject().put("raw", compactJsonNumber(it)).put("active", it != 0.0))
        }
    }

    private fun compactJsonNumber(value: Double): Number =
        if (value % 1.0 == 0.0) value.toLong() else value

    internal fun normalizeTirePressureKpa(value: Double): Double =
        if (value > 0.0 && value < 100.0) value * 4.0 else value

    private fun putNumberText(
        destination: JSONObject,
        destinationKey: String,
        source: JSONObject,
        sourceKey: String,
        transform: (Double) -> Double = { it },
    ) {
        val value = number(source.opt(sourceKey)) ?: return
        destination.put(destinationKey, compactNumber(transform(value)))
    }

    private fun number(value: Any?): Double? = when (value) {
        is Number -> value.toDouble()
        is String -> Regex("-?\\d+(?:\\.\\d+)?").find(value.replace(",", ""))?.value?.toDoubleOrNull()
        else -> null
    }

    private fun compactNumber(value: Double): String = if (value % 1.0 == 0.0) {
        value.toLong().toString()
    } else {
        String.format(Locale.US, "%.2f", value).trimEnd('0').trimEnd('.')
    }

    private fun formatKst(timestamp: Long): String {
        val millis = if (timestamp < 10_000_000_000L) timestamp * 1000 else timestamp
        return SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.KOREA).apply {
            timeZone = TimeZone.getTimeZone("Asia/Seoul")
        }.format(Date(millis))
    }

    private fun statusError(code: Int): String = when (code) {
        2 -> "멀티팩 모듈이 연결되지 않았습니다."
        3 -> "차량 내부 모듈이 연결되지 않았습니다."
        4 -> "차량 내부 모듈을 찾을 수 없습니다."
        5 -> "차량이 주차 상태가 아닙니다."
        8 -> "차량 통신에 실패했습니다."
        12 -> "차량이 다른 요청을 처리 중입니다."
        13 -> "차량 조회 요청이 아직 처리 중입니다."
        else -> "차량 상태 조회에 실패했습니다. (코드 $code)"
    }
}
