package com.example.carcontroller

import java.io.IOException
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import javax.net.ssl.HttpsURLConnection
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
        return VehicleStatus(normalizeStatus(carStatus, timestamp), formatKst(timestamp))
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

    private fun normalizeStatus(carStatus: JSONObject, timestamp: Long): JSONObject {
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
        putNumberText(result, "mileage", carStatus, "odo")
        putNumberText(result, "oil", carStatus, "olLfe")
        putNumberText(result, "range", carStatus, "fRng")

        val tireKeys = listOf("trPrsLf", "trPrsRf", "trPrsLr", "trPrsRr")
        val tireValues = tireKeys.map { key -> number(carStatus.opt(key))?.let(::compactNumber) ?: "--" }
        if (tireValues.any { it != "--" }) {
            val tireText = buildString {
                append("타이어 정보")
                tireValues.forEach { append('\n').append(it) }
            }
            result.put("tire_pressure", tireText)
            result.put("tire_pressure_all", tireText)
        }
        result.put("last_update", formatKst(timestamp))
        result.put("source", "gmone-direct-android")
        result.put("collector_status", "success")
        result.put("refresh_status", "success")
        return result
    }

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
