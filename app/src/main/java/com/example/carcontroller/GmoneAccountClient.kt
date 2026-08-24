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
    private const val CAR_CONTROL_OPERATION = 19
    private const val STATUS_OPERATION = 21
    // Official Multipack protocol: REQ_CLEAR_DTC (enum index 0x2f).
    private const val CLEAR_DTC_OPERATION = 47
    private const val READ_OPTIONS_OPERATION = 59
    private const val WRITE_OPTIONS_OPERATION = 61
    private const val READ_MODULE_INFO_OPERATION = 63
    private const val RESULT_OPERATION = 66

    data class LoginResult(val vehicleCount: Int)
    data class VehicleStatus(val data: JSONObject, val updatedAt: String)
    internal data class DtcPresentation(
        val code: String,
        val description: String,
        val category: String,
    )
    internal data class ExtendedControlSpec(
        val controlType: Int,
        val requestOption: Int,
        val successMessage: String,
    )
    private data class Session(val login: JSONObject, val vehicleCount: Int)

    fun login(email: String, password: String): LoginResult {
        return LoginResult(authenticate(email, password).vehicleCount)
    }

    fun fetchMultipackSettings(email: String, password: String): JSONObject {
        val session = authenticate(email, password)
        return readMultipackSettings(session.login)
    }

    fun sendExtendedVehicleControl(email: String, password: String, command: String): String {
        val spec = extendedControlSpec(command)
        val session = authenticate(email, password)
        val resolved = resolveResult(
            session.login,
            request(
                path = "/b1_connect_m",
                operation = CAR_CONTROL_OPERATION,
                login = session.login,
                body = JSONObject()
                    .put("control_type", spec.controlType)
                    .put("request_option", spec.requestOption),
            ),
        )
        val body = requireSuccess(resolved, "차량 제어")
        val responseType = body.optInt("control_type", spec.controlType)
        val responseOption = body.optInt("request_option", spec.requestOption)
        if (responseType != spec.controlType || responseOption != spec.requestOption) {
            throw IOException("차량 제어 응답이 요청과 일치하지 않습니다.")
        }
        return spec.successMessage
    }

    internal fun extendedControlSpec(command: String): ExtendedControlSpec = when (command) {
        "VEHICLE_START" -> ExtendedControlSpec(0, 2, "원격시동을 시작했습니다.")
        "VEHICLE_STOP" -> ExtendedControlSpec(0, 0, "원격시동을 종료했습니다.")
        "DOOR_LOCK" -> ExtendedControlSpec(1, 0, "차량 도어를 잠갔습니다.")
        "DOOR_UNLOCK" -> ExtendedControlSpec(1, 1, "차량 도어 잠금을 해제했습니다.")
        "DRIVER_DOOR_UNLOCK" -> ExtendedControlSpec(1, 2, "운전석 도어 잠금을 해제했습니다.")
        "TRUNK_CLOSE" -> ExtendedControlSpec(2, 0, "트렁크를 닫았습니다.")
        "TRUNK_OPEN" -> ExtendedControlSpec(2, 1, "트렁크를 열었습니다.")
        "PANIC" -> ExtendedControlSpec(3, 1, "차량 찾기 신호를 실행했습니다.")
        "MAIN_LIGHT_OFF" -> ExtendedControlSpec(4, 0, "메인 라이트를 껐습니다.")
        "MAIN_LIGHT_ON" -> ExtendedControlSpec(4, 1, "메인 라이트를 켰습니다.")
        "WINDOW_CLOSE" -> ExtendedControlSpec(5, 0, "창문을 닫았습니다.")
        "WINDOW_OPEN" -> ExtendedControlSpec(5, 1, "창문을 열었습니다.")
        "SUNROOF_CLOSE" -> ExtendedControlSpec(6, 0, "선루프를 닫았습니다.")
        "SUNROOF_OPEN" -> ExtendedControlSpec(6, 1, "선루프를 열었습니다.")
        "SUNROOF_TILT" -> ExtendedControlSpec(6, 3, "선루프를 틸트했습니다.")
        else -> throw IllegalArgumentException("지원하지 않는 GMONE 차량 제어입니다.")
    }

    internal fun supportsVehicleControl(command: String): Boolean = runCatching {
        extendedControlSpec(command)
    }.isSuccess

    fun fetchVehicleStatus(email: String, password: String, refreshDtc: Boolean = false): VehicleStatus {
        val session = authenticate(email, password)
        val initial = request(
            path = "/b1_connect_m",
            operation = STATUS_OPERATION,
            login = session.login,
            body = JSONObject().put("refresh_dtc", refreshDtc).put("last_received_time", 0),
        )
        val resolved = resolveResult(session.login, initial)
        val body = resolved.optJSONObject("body") ?: throw IOException("차량 상태 응답이 없습니다.")
        val resultCode = body.optInt("success", -1)
        if (resultCode != 0) throw IOException(statusError(resultCode))
        val carStatus = body.optJSONObject("car_status") ?: throw IOException("차량 상태 값이 없습니다.")
        val timestamp = resolved.optLong("timestamp", System.currentTimeMillis())
        val settings = runCatching { readMultipackSettings(session.login) }.getOrNull()
        val moduleInfo = runCatching { readMultipackInfo(session.login) }.getOrNull()
        return VehicleStatus(
            normalizeStatus(
                carStatus,
                timestamp,
                body.optJSONArray("running_cycles_data"),
                settings,
                moduleInfo,
            ),
            formatKst(timestamp),
        )
    }

    fun clearDiagnosticCodes(email: String, password: String): String {
        val session = authenticate(email, password)
        val resolved = resolveResult(
            session.login,
            request(
                path = "/b1_connect_m",
                operation = CLEAR_DTC_OPERATION,
                login = session.login,
                body = JSONObject(),
            ),
        )
        requireSuccess(resolved, "고장코드 삭제")
        return "고장코드 삭제 요청이 완료되었습니다."
    }

    internal fun clearDtcOperationId(): Int = CLEAR_DTC_OPERATION

    fun saveMultipackSettings(email: String, password: String, patch: JSONObject): JSONObject {
        val session = authenticate(email, password)
        val current = readMultipackSettings(session.login)
        val safePatch = validateSettingsPatch(patch)
        val merged = mergeSettings(current, safePatch)
        val resolved = resolveResult(
            session.login,
            request(
                path = "/b1_connect_m",
                operation = WRITE_OPTIONS_OPERATION,
                login = session.login,
                body = JSONObject().put("multipack_option", merged),
            ),
        )
        requireSuccess(resolved, "멀티팩 설정 저장")

        val verified = readMultipackSettings(session.login)
        val keys = safePatch.keys()
        while (keys.hasNext()) {
            val key = keys.next()
            if (verified.optInt(key, Int.MIN_VALUE) != safePatch.getInt(key)) {
                throw IOException("$key 설정이 차량 모듈에 반영되지 않았습니다.")
            }
        }
        return verified
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
            if (responseCode !in 200..299) {
                val reason = runCatching {
                    JSONObject(response).optString("message")
                        .ifBlank { JSONObject(response).optString("error") }
                }.getOrDefault("").trim()
                throw IOException(
                    if (reason.isBlank()) "멀티팩 서버 HTTP $responseCode"
                    else "멀티팩 서버 HTTP $responseCode: $reason",
                )
            }
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

    private fun readMultipackSettings(login: JSONObject): JSONObject {
        val resolved = resolveResult(
            login,
            request("/b1_connect_m", READ_OPTIONS_OPERATION, login, JSONObject()),
        )
        val body = requireSuccess(resolved, "멀티팩 설정 조회")
        return body.optJSONObject("multipack_option")
            ?: throw IOException("멀티팩 설정값이 응답에 없습니다.")
    }

    private fun readMultipackInfo(login: JSONObject): JSONObject {
        val resolved = resolveResult(
            login,
            request("/b1_connect_m", READ_MODULE_INFO_OPERATION, login, JSONObject()),
        )
        val body = requireSuccess(resolved, "멀티팩 모듈 정보 조회")
        return body.optJSONObject("multipack_info") ?: JSONObject()
    }

    private fun requireSuccess(response: JSONObject, action: String): JSONObject {
        val body = response.optJSONObject("body") ?: throw IOException("$action 응답이 없습니다.")
        val resultCode = body.optInt("success", -1)
        if (resultCode != 0) throw IOException("${action}에 실패했습니다. (코드 $resultCode)")
        return body
    }

    private fun normalizeStatus(
        carStatus: JSONObject,
        timestamp: Long,
        runningCycles: JSONArray? = null,
        settings: JSONObject? = null,
        moduleInfo: JSONObject? = null,
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
        fuelLevelLiters(carStatus)?.let { result.put("fuel", compactNumber(it)) }
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
        result.put("gmone_details", normalizeDetails(carStatus, runningCycles, settings, moduleInfo))
        result.put("last_update", formatKst(timestamp))
        result.put("source", "gmone-direct-android")
        result.put("collector_status", "success")
        result.put("refresh_status", "success")
        return result
    }

    internal fun normalizeDetails(
        carStatus: JSONObject,
        runningCycles: JSONArray? = null,
        settings: JSONObject? = null,
        moduleInfo: JSONObject? = null,
    ): JSONObject {
        val tires = JSONObject().apply {
            putNormalizedTire("frontLeftKpa", carStatus.opt("trPrsLf"))
            putNormalizedTire("frontRightKpa", carStatus.opt("trPrsRf"))
            putNormalizedTire("rearLeftKpa", carStatus.opt("trPrsLr"))
            putNormalizedTire("rearRightKpa", carStatus.opt("trPrsRr"))
        }
        val closures = JSONObject().apply {
            putDoorLockState("doors", carStatus.opt("door"))
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
                number(carStatus.opt("fCap"))?.let { put("capacityLiters", compactJsonNumber(it)) }
                number(carStatus.opt("fLvl"))?.let { put("levelPercent", compactJsonNumber(it)) }
                fuelLevelLiters(carStatus)?.let { put("levelLiters", compactJsonNumber(it)) }
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
                putNumberFrom(carStatus, "remainingStarts", "rvsRmng")
                putNumberFrom(carStatus, "remainingTimeRaw", "rvsRmngTm")
                put("remainingTimeValid", boolean(carStatus.opt("rvsRmngTmVld")) ?: false)
            })
            put("connectivity", JSONObject().apply {
                putNumberFrom(carStatus, "moduleSignalLevel", "rsiLvl")
                put("moduleSignalMaximum", 5)
            })
            put("capabilities", JSONObject().apply {
                put("driverDoorUnlockStatusRaw", true)
                put("driverDoorUnlockCommandAvailable", true)
                put("mainLightStatusRaw", carStatus.has("light"))
                put("mainLightCommandAvailable", true)
                put("climateLevelAvailable", false)
                put("evChargerPowerLevelAvailable", ev.optBoolean("supported", false))
            })
            if (settings != null || moduleInfo != null) {
                put("module", JSONObject().apply {
                    settings?.let { put("settings", JSONObject(it.toString())) }
                    moduleInfo?.let { put("info", JSONObject().put("multipack_info", JSONObject(it.toString()))) }
                })
            }
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
            number(record.opt("code"))?.toInt()?.let { rawCode ->
                val presentation = dtcPresentation(rawCode)
                safe.put("displayCode", presentation.code)
                safe.put("description", presentation.description)
                safe.put("category", presentation.category)
            }
            if ((number(record.opt("fail")) ?: 0.0) != 0.0) failedCount += 1
            records.put(safe)
        }
        return JSONObject()
            .put("reportedCount", number(carStatus.opt("dtcCnt"))?.toInt() ?: records.length())
            .put("failedCount", failedCount)
            .put("records", records)
    }

    internal fun dtcPresentation(rawCode: Int): DtcPresentation {
        val value = rawCode and 0xFFFF
        val system = charArrayOf('P', 'C', 'B', 'U')[(value ushr 14) and 0x03]
        val standardDigit = (value ushr 12) and 0x03
        val code = String.format(Locale.US, "%c%d%03X", system, standardDigit, value and 0x0FFF)
        val category = when (system) {
            'P' -> "파워트레인"
            'C' -> "섀시"
            'B' -> "차체"
            else -> "차량 통신"
        }
        val description = when (code) {
            "P129B" -> "연료 펌프 제어 모듈 시스템 전압 낮음"
            "B2B11" -> "중앙 게이트웨이 모듈 시스템 전압 낮음"
            "U0121" -> "ABS/전자식 브레이크 제어 모듈과 통신 두절"
            "U0140" -> "차체 제어 모듈(BCM)과 통신 두절"
            else -> "$category 계통 고장코드"
        }
        return DtcPresentation(code, description, category)
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

    private fun JSONObject.putDoorLockState(key: String, value: Any?) {
        number(value)?.let {
            val raw = it.toInt()
            val label = when (raw) {
                0 -> "잠김"
                1 -> "잠금 해제"
                2 -> "운전석만 잠금 해제"
                else -> "알 수 없음"
            }
            put(
                key,
                JSONObject()
                    .put("raw", raw)
                    .put("active", raw != 0)
                    .put("label", label),
            )
        }
    }

    internal fun validateSettingsPatch(patch: JSONObject): JSONObject {
        val allowedValues = mapOf(
            "all_function_stop" to 0..1,
            "auto_door_lock" to 0..1,
            "blind_alert_chime" to 0..1,
            "blind_alert_chime_count" to 2..5,
            "blind_alert_chime_sound" to 0..3,
            "blind_alert_speed" to 0..100,
            "door_lock_speed" to 0..1,
            "door_unlock_gear" to 0..1,
            "engine_cooldown_time" to 0..2,
            "engine_start_radio_mute" to 0..1,
            "mirror_unfold" to 0..2,
            "reverse_hazard" to 0..1,
            "shock_alarm_count" to 2..5,
            "shock_sensor_delay_enable" to 0..1,
            "shock_sensor_delay_seconds" to 0..120,
            "shock_sensor_disable" to 0..4,
            "sunshade_close" to 0..1,
            "windows_close" to 0..2,
        )
        val validated = JSONObject()
        val keys = patch.keys()
        while (keys.hasNext()) {
            val key = keys.next()
            val range = allowedValues[key] ?: throw IllegalArgumentException("지원하지 않는 설정입니다: $key")
            val value = when (val raw = patch.opt(key)) {
                is Number -> raw.toInt()
                is String -> raw.toIntOrNull()
                else -> null
            } ?: throw IllegalArgumentException("$key 값은 정수여야 합니다.")
            if (value !in range) throw IllegalArgumentException("$key 값이 허용 범위를 벗어났습니다.")
            if (key == "shock_sensor_delay_seconds" && value in 1..4) {
                throw IllegalArgumentException("충격 센서 지연은 0초 또는 5~120초여야 합니다.")
            }
            validated.put(key, value)
        }
        if (validated.length() == 0) throw IllegalArgumentException("변경할 설정이 없습니다.")
        return validated
    }

    internal fun mergeSettings(current: JSONObject, patch: JSONObject): JSONObject {
        val merged = JSONObject(current.toString())
        val keys = patch.keys()
        while (keys.hasNext()) {
            val key = keys.next()
            merged.put(key, patch.getInt(key))
        }
        return merged
    }

    private fun compactJsonNumber(value: Double): Number =
        if (value % 1.0 == 0.0) value.toLong() else value

    private fun fuelLevelLiters(carStatus: JSONObject): Double? {
        val capacityLiters = number(carStatus.opt("fCap")) ?: return null
        val levelPercent = number(carStatus.opt("fLvl")) ?: return null
        if (capacityLiters <= 0.0 || levelPercent !in 0.0..100.0) return null
        return capacityLiters * levelPercent / 100.0
    }

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

    private fun boolean(value: Any?): Boolean? = when (value) {
        is Boolean -> value
        is Number -> value.toInt() != 0
        is String -> when (value.trim().lowercase(Locale.US)) {
            "true", "1", "yes", "y" -> true
            "false", "0", "no", "n" -> false
            else -> null
        }
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
