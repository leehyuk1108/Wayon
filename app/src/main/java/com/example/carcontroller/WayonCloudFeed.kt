package com.example.carcontroller

import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import kotlin.math.max
import kotlin.math.roundToInt

data class WayonCloudState(
    val updatedAt: String?,
    val updatedAtDisplay: String,
    val gpsUpdatedAtDisplay: String,
    val onroad: Boolean,
    val voltageV: Double?,
    val latitude: Double?,
    val longitude: Double?,
    val speedMps: Double?,
    val doorLocked: Boolean?,
    val doorLockUpdatedAt: String?,
    val rawJson: JSONObject? = null,
) {
    val speedText: String
        get() = formatSpeed(speedMps)
}

data class WayonCloudHistoryItem(
    val id: String?,
    val date: String,
    val time: String,
    val endedAt: String?,
    val distance: String,
    val duration: String,
    val avgSpeed: String,
    val topSpeed: String,
    val startLatitude: Double?,
    val startLongitude: Double?,
    val endLatitude: Double?,
    val endLongitude: Double?,
    val startAddress: String,
    val endAddress: String,
    val route: JSONArray,
    val routePointCount: Int,
) {
    fun toJsonObject(): JSONObject = JSONObject().apply {
        put("id", id)
        put("date", date)
        put("time", time)
        put("endedAt", endedAt)
        put("distance", distance)
        put("duration", duration)
        put("avgSpeed", avgSpeed)
        put("topSpeed", topSpeed)
        put("startLatitude", startLatitude)
        put("startLongitude", startLongitude)
        put("endLatitude", endLatitude)
        put("endLongitude", endLongitude)
        put("startAddress", startAddress)
        put("endAddress", endAddress)
        put("route", route)
        put("routePointCount", routePointCount)
    }
}

data class WayonCloudSnapshotItem(
    val id: String,
    val camera: String,
    val capturedAt: String?,
    val capturedAtDisplay: String,
    val kvKey: String,
    val sizeBytes: Long?,
) {
    private val cameraLabel: String
        get() = when (camera) {
            "driver" -> "실내"
            "wide" -> "실외"
            else -> camera
        }

    fun toJsonObject(): JSONObject = JSONObject().apply {
        put("id", id)
        put("camera", camera)
        put("cameraLabel", cameraLabel)
        put("capturedAt", capturedAt)
        put("capturedAtDisplay", capturedAtDisplay)
        put("kvKey", kvKey)
        put("sizeBytes", sizeBytes)
    }
}

data class WayonCloudFeed(
    val state: WayonCloudState?,
    val history: List<WayonCloudHistoryItem>,
    val snapshots: List<WayonCloudSnapshotItem> = emptyList(),
) {
    val latestTrip: WayonCloudHistoryItem?
        get() = history.firstOrNull()

    val historyJson: String
        get() = JSONArray().apply { history.forEach { put(it.toJsonObject()) } }.toString()

    val snapshotsJson: String
        get() = JSONArray().apply { snapshots.forEach { put(it.toJsonObject()) } }.toString()

    fun withLatestTripLocationFallback(): WayonCloudFeed {
        val current = state ?: return this
        if (current.latitude != null && current.longitude != null) return this
        val latest = latestTrip ?: return this
        val latitude = latest.endLatitude ?: return this
        val longitude = latest.endLongitude ?: return this
        val fallbackTime = formatTime(latest.endedAt).takeUnless { it == "--:--" }
            ?: current.gpsUpdatedAtDisplay
        return copy(
            state = current.copy(
                gpsUpdatedAtDisplay = fallbackTime,
                latitude = latitude,
                longitude = longitude,
            ),
        )
    }
}

object WayonCloudFeedParser {
    private data class ParsedTrip(val startedAtMillis: Long, val item: WayonCloudHistoryItem)
    private data class ParsedSnapshot(val capturedAtMillis: Long, val item: WayonCloudSnapshotItem)

    fun parse(json: String): WayonCloudFeed {
        val root = JSONObject(json)
        val vehicleLock = root.optJSONObject("vehicleLock")
        val state = root.optJSONObject("state")?.let { parseState(it, vehicleLock) }
        val trips = root.optJSONArray("trips") ?: JSONArray()
        val snapshots = root.optJSONArray("snapshots") ?: JSONArray()

        val history = buildList {
            for (index in 0 until trips.length()) {
                trips.optJSONObject(index)?.let { add(parseTrip(it)) }
            }
        }.sortedByDescending { it.startedAtMillis }.map { it.item }

        val snapshotItems = buildList {
            for (index in 0 until snapshots.length()) {
                snapshots.optJSONObject(index)?.let { add(parseSnapshot(it)) }
            }
        }.sortedByDescending { it.capturedAtMillis }.map { it.item }

        return WayonCloudFeed(state, history, snapshotItems)
    }

    private fun parseState(state: JSONObject, vehicleLock: JSONObject?): WayonCloudState {
        val updatedAt = state.optNullableString("updated_at")
        val rawJson = state.optJSONObjectString("raw_json")
        val gps = rawJson?.optJSONObject("gps")
        return WayonCloudState(
            updatedAt = updatedAt,
            updatedAtDisplay = formatTime(updatedAt),
            gpsUpdatedAtDisplay = formatGpsTime(gps),
            onroad = state.optBooleanLike("onroad"),
            voltageV = state.optNullableDouble("voltage_v"),
            latitude = state.optNullableDouble("latitude"),
            longitude = state.optNullableDouble("longitude"),
            speedMps = state.optNullableDouble("speed_mps"),
            doorLocked = vehicleLock?.optNullableBoolean("locked"),
            doorLockUpdatedAt = vehicleLock?.optNullableString("occurredAt"),
            rawJson = rawJson,
        )
    }

    private fun parseTrip(trip: JSONObject): ParsedTrip {
        val startedAt = trip.optNullableString("started_at")
        val endedAt = trip.optNullableString("ended_at")
        val durationSeconds = trip.optLong("duration_s", 0L)
        val distanceMeters = trip.optDouble("distance_m", 0.0)
        val route = routeArray(trip)
        val routePointCount = trip.optNullableLong("route_point_count")?.toInt() ?: route.length()
        val topSpeed = trip.optNullableDouble("max_speed_mps") ?: maxRouteSpeedMps(route)
        val averageSpeed = trip.optNullableDouble("avg_speed_mps")
            ?: durationSeconds.takeIf { it > 0 }?.let { distanceMeters / it }
        val startLatitude = trip.optNullableDouble("start_lat")
        val startLongitude = trip.optNullableDouble("start_lon")
        val endLatitude = trip.optNullableDouble("end_lat")
        val endLongitude = trip.optNullableDouble("end_lon")

        return ParsedTrip(
            startedAtMillis = parseIsoUtcMillis(startedAt) ?: 0L,
            item = WayonCloudHistoryItem(
                id = trip.optNullableString("id"),
                date = formatDate(startedAt),
                time = formatTime(startedAt),
                endedAt = endedAt,
                distance = String.format(Locale.US, "%.2f km", distanceMeters / 1000.0),
                duration = formatDuration(durationSeconds),
                avgSpeed = formatSpeed(averageSpeed),
                topSpeed = formatSpeed(topSpeed),
                startLatitude = startLatitude,
                startLongitude = startLongitude,
                endLatitude = endLatitude,
                endLongitude = endLongitude,
                startAddress = coordinateText(startLatitude, startLongitude),
                endAddress = coordinateText(endLatitude, endLongitude),
                route = route,
                routePointCount = routePointCount,
            ),
        )
    }

    private fun parseSnapshot(snapshot: JSONObject): ParsedSnapshot {
        val capturedAt = snapshot.optNullableString("captured_at")
        return ParsedSnapshot(
            capturedAtMillis = parseIsoUtcMillis(capturedAt) ?: 0L,
            item = WayonCloudSnapshotItem(
                id = snapshot.optNullableString("id").orEmpty(),
                camera = snapshot.optNullableString("camera").orEmpty(),
                capturedAt = capturedAt,
                capturedAtDisplay = formatTime(capturedAt),
                kvKey = snapshot.optNullableString("kv_key").orEmpty(),
                sizeBytes = snapshot.optNullableLong("size_bytes"),
            ),
        )
    }

    private fun routeArray(trip: JSONObject): JSONArray = when (val route = trip.opt("route")) {
        is JSONArray -> route
        is String -> runCatching { JSONArray(route) }.getOrDefault(JSONArray())
        else -> JSONArray()
    }

    private fun maxRouteSpeedMps(route: JSONArray): Double? {
        var maximum: Double? = null
        for (index in 0 until route.length()) {
            val speed = route.optJSONObject(index)?.optNullableDouble("speedMps") ?: continue
            maximum = max(maximum ?: speed, speed)
        }
        return maximum
    }
}

private fun JSONObject.optNullableString(name: String): String? =
    if (!has(name) || isNull(name)) null else optString(name)

private fun JSONObject.optNullableDouble(name: String): Double? =
    if (!has(name) || isNull(name)) null else optDouble(name).takeIf { it.isFinite() }

private fun JSONObject.optNullableLong(name: String): Long? =
    if (!has(name) || isNull(name)) null else optLong(name)

private fun JSONObject.optJSONObjectString(name: String): JSONObject? {
    if (!has(name) || isNull(name)) return null
    return when (val value = opt(name)) {
        is JSONObject -> value
        is String -> runCatching { JSONObject(value) }.getOrNull()
        else -> null
    }
}

private fun JSONObject.optBooleanLike(name: String): Boolean = when (val value = opt(name)) {
    is Boolean -> value
    is Number -> value.toInt() != 0
    is String -> value == "1" || value.equals("true", ignoreCase = true)
    else -> false
}

private fun JSONObject.optNullableBoolean(name: String): Boolean? {
    if (!has(name) || isNull(name)) return null
    return when (val value = opt(name)) {
        is Boolean -> value
        is Number -> value.toInt() != 0
        is String -> when {
            value == "1" || value.equals("true", ignoreCase = true) -> true
            value == "0" || value.equals("false", ignoreCase = true) -> false
            else -> null
        }
        else -> null
    }
}

private fun formatDate(isoUtc: String?): String = formatIsoUtc(isoUtc, "yyyy-MM-dd", "----.--.--")
private fun formatTime(isoUtc: String?): String = formatIsoUtc(isoUtc, "HH:mm", "--:--")

private fun formatGpsTime(gps: JSONObject?): String {
    if (gps == null) return "GPS 시간 없음"
    gps.optNullableString("updatedAt")?.takeIf { it.isNotBlank() }?.let { return formatTime(it) }
    val timestamp = gps.optNullableLong("timestampMillis") ?: return "GPS 시간 없음"
    return formatEpochMillis(timestamp, "HH:mm", "GPS 시간 없음")
}

private fun formatIsoUtc(isoUtc: String?, pattern: String, fallback: String): String {
    val millis = parseIsoUtcMillis(isoUtc) ?: return fallback
    return formatEpochMillis(millis, pattern, fallback)
}

private fun parseIsoUtcMillis(isoUtc: String?): Long? {
    if (isoUtc.isNullOrBlank()) return null
    val patterns = listOf("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", "yyyy-MM-dd'T'HH:mm:ss'Z'")
    return patterns.firstNotNullOfOrNull { pattern ->
        runCatching {
            SimpleDateFormat(pattern, Locale.US).apply {
                timeZone = TimeZone.getTimeZone("UTC")
            }.parse(isoUtc)?.time
        }.getOrNull()
    }
}

private fun formatEpochMillis(timestampMillis: Long, pattern: String, fallback: String): String =
    runCatching {
        SimpleDateFormat(pattern, Locale.KOREA).apply {
            timeZone = TimeZone.getTimeZone("Asia/Seoul")
        }.format(Date(timestampMillis))
    }.getOrDefault(fallback)

private fun formatDuration(seconds: Long): String {
    val safeSeconds = seconds.coerceAtLeast(0L)
    return String.format(
        Locale.US,
        "%02d:%02d:%02d",
        safeSeconds / 3600,
        (safeSeconds % 3600) / 60,
        safeSeconds % 60,
    )
}

private fun formatSpeed(speedMps: Double?): String =
    speedMps?.let { "${(it * 3.6).roundToInt()} km/h" } ?: "-- km/h"

private fun coordinateText(latitude: Double?, longitude: Double?): String =
    if (latitude != null && longitude != null) {
        String.format(Locale.US, "%.5f, %.5f", latitude, longitude)
    } else {
        "알 수 없음"
    }
