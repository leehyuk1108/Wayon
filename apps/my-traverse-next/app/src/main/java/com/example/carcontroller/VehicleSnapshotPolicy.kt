package com.example.carcontroller

import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.text.ParsePosition
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

internal object VehicleSnapshotPolicy {
    const val PREF_KEY = "VEHICLE_SNAPSHOT_V1"
    const val MAX_BYTES = 256 * 1024
    private const val MAX_AGE_MS = 7L * 24 * 60 * 60 * 1000
    private val sensitive = listOf("token", "password", "secret", "email", "uuid", "imei", "iccid", "phone_number", "api_key")
    private val vinKey = Regex("(?i)(^vin$|_vin|vin_|vehicleIdentificationNumber)")
    private val identifier = Regex("(?i)([A-HJ-NPR-Z0-9]{17}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")

    fun scope(email: String?, cloudKey: String?): String {
        val key = cloudKey?.takeIf { it.isNotBlank() } ?: "local-only-vehicle-snapshot"
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(key.toByteArray(Charsets.UTF_8), "HmacSHA256"))
        return mac.doFinal(("gmone-acct-v1:" + email.orEmpty().trim().lowercase(Locale.ROOT))
            .toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it) }
    }

    fun epoch(status: WayonVehicleStatus): Long? = parseTime(status.data.optString("last_update")) ?: parseTime(status.updatedAt)

    fun parseTime(value: String?): Long? {
        if (value.isNullOrBlank()) return null
        val formats = listOf("yyyy-MM-dd'T'HH:mm:ss.SSSXXX" to "UTC", "yyyy-MM-dd'T'HH:mm:ssXXX" to "UTC",
            "yyyy-MM-dd HH:mm:ss" to "Asia/Seoul")
        return formats.firstNotNullOfOrNull { (pattern, zone) ->
            runCatching { val position = ParsePosition(0)
                val parsed = SimpleDateFormat(pattern, Locale.US).apply {
                isLenient = false
                timeZone = TimeZone.getTimeZone(zone)
            }.parse(value, position)
                parsed?.time?.takeIf { position.index == value.length }
            }.getOrNull()
        }
    }

    fun usable(status: WayonVehicleStatus, nowMs: Long): Boolean {
        val time = epoch(status) ?: return false
        return nowMs - time in -120_000L..MAX_AGE_MS && status.data.length() > 0
    }

    fun rank(status: WayonVehicleStatus): Int {
        val module = status.data.optJSONObject("gmone_details")?.optJSONObject("module")
        return (if (module != null && module.length() > 0) 2 else 0) + (if (status.cached) 0 else 4)
    }

    fun sanitize(data: JSONObject): JSONObject {
        require(data.toString().toByteArray(Charsets.UTF_8).size <= MAX_BYTES)
        fun clean(value: Any?, depth: Int): Any? {
            require(depth <= 16)
            return when (value) {
                is JSONObject -> JSONObject().apply {
                    value.keys().forEach { key ->
                        if (sensitive.none { key.lowercase(Locale.ROOT).contains(it) } && !vinKey.containsMatchIn(key) && !identifier.matches(key)) {
                            put(key, clean(value.opt(key), depth + 1))
                        }
                    }
                }
                is JSONArray -> JSONArray().apply {
                    for (index in 0 until value.length()) put(clean(value.opt(index), depth + 1))
                }
                is String -> if (identifier.matches(value)) "<redacted>" else value
                else -> value
            }
        }
        return clean(data, 0) as JSONObject
    }

    fun encode(scope: String, status: WayonVehicleStatus, nowMs: Long): String? = runCatching {
        if (!usable(status, nowMs)) return null
        JSONObject().put("version", 1).put("scope", scope).put("source", status.source)
            .put("updatedAt", status.updatedAt).put("data", sanitize(status.data)).toString()
    }.getOrNull()

    fun decode(raw: String?, scope: String, nowMs: Long): WayonVehicleStatus? = runCatching {
        if (raw.isNullOrBlank() || raw.toByteArray(Charsets.UTF_8).size > MAX_BYTES) return null
        val value = JSONObject(raw)
        if (value.optInt("version") != 1 || value.optString("scope") != scope) return null
        val status = WayonVehicleStatus(value.optString("source"), value.optString("updatedAt"), true,
            value.getJSONObject("data"), cached = true, clientScope = scope)
        status.takeIf { usable(it, nowMs) }
    }.getOrNull()

    fun upload(status: WayonVehicleStatus, scope: String, nowMs: Long): JSONObject? = runCatching {
        if (status.cached || !usable(status, nowMs)) return null
        val iso = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US).apply {
            timeZone = TimeZone.getTimeZone("UTC")
        }
        JSONObject().put("schemaVersion", "wayon-gmone-v1").put("source", "gmone-direct-android")
            .put("clientScope", scope).put("collectedAt", iso.format(Date(nowMs)))
            .put("vehicleUpdatedAt", iso.format(Date(epoch(status)!!))).put("status", sanitize(status.data))
    }.getOrNull()
}

/** Only an observed direct reply in this process can supply the existing fast command check. */
internal class DirectVehicleObservation {
    private var status: WayonVehicleStatus? = null
    private var scope = ""
    private var receivedMs = 0L

    @Synchronized fun clear() { status = null }

    @Synchronized fun record(value: WayonVehicleStatus, accountScope: String, elapsedMs: Long) {
        if (value.cached || value.stale) return
        status = value
        scope = accountScope
        receivedMs = elapsedMs
    }

    @Synchronized fun recent(accountScope: String, elapsedMs: Long, wallMs: Long): WayonVehicleStatus? = status?.takeIf {
        accountScope == scope && elapsedMs - receivedMs in 0L..30_000L &&
            VehicleSnapshotPolicy.epoch(it)?.let { time -> wallMs - time in 0L..30_000L } == true
    }
}
