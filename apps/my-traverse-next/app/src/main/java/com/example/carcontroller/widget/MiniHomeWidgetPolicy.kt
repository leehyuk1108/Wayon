package com.example.carcontroller.widget

import com.example.carcontroller.WayonCloudFeed
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import kotlin.math.roundToInt

internal data class MiniHomeStatus(
    val kicker: String,
    val title: String,
    val detail: String,
    val tone: String,
)

internal data class MiniHomeSnapshot(
    val status: MiniHomeStatus,
    val rangeKm: Int?,
    val fuelPercent: Int?,
    val latitude: Double?,
    val longitude: Double?,
    val updatedAt: String,
    val tracking: Boolean,
)

internal object MiniHomeWidgetPolicy {
    private const val TIRE_WARNING_KPA = 200.0
    private const val OIL_WARNING_PERCENT = 10.0
    private const val FUEL_WARNING_PERCENT = 10
    private const val BATTERY_TEMPERATURE_WARNING_C = 55.0
    private const val BATTERY_TEMPERATURE_CRITICAL_C = 65.0
    private const val VEHICLE_DETAILS_STALE_AFTER_MS = 24L * 60L * 60L * 1000L

    fun snapshot(feed: WayonCloudFeed, nowMs: Long = System.currentTimeMillis()): MiniHomeSnapshot {
        val resolved = feed.withLatestTripLocationFallback()
        val state = resolved.state
        val data = resolved.vehicleStatus?.data
        val details = data?.optJSONObject("gmone_details")
        val fuel = fuelPercent(details, data)
        return MiniHomeSnapshot(
            status = status(resolved, nowMs),
            rangeKm = rangeKm(details, data),
            fuelPercent = fuel,
            latitude = state?.latitude ?: resolved.latestTrip?.endLatitude,
            longitude = state?.longitude ?: resolved.latestTrip?.endLongitude,
            updatedAt = formatUpdatedAt(
                data?.stringOrNull("last_update")
                    ?: resolved.vehicleStatus?.updatedAt
                    ?: state?.updatedAt,
            ),
            tracking = state?.onroad == true && state.ignition != false && state.gpsFresh != false,
        )
    }

    fun status(
        feed: WayonCloudFeed,
        nowMs: Long = System.currentTimeMillis(),
        impactActive: Boolean = false,
    ): MiniHomeStatus {
        if (impactActive) {
            return report("ATTENTION", "IMPACT\nDETECTED", "Check 360 Live", "critical")
        }

        val state = feed.state
        val vehicleStatus = feed.vehicleStatus
        val details = vehicleStatus?.data?.optJSONObject("gmone_details")
        if (state == null && details == null) {
            return report("CHECK STATUS", "CHECKING", "Waiting for vehicle data", "offline")
        }

        val detailsMeta = details?.optJSONObject("meta")
        val detailsSource = detailsMeta?.stringOrNull("source").orEmpty().lowercase(Locale.US)
        val detailsUpdatedAt = if (detailsSource.contains("gmone")) {
            detailsMeta?.stringOrNull("collectedAt")
                ?: detailsMeta?.stringOrNull("updatedAt")
                ?: vehicleStatus?.updatedAt
        } else {
            detailsMeta?.stringOrNull("updatedAt") ?: vehicleStatus?.updatedAt
        }
        val detailsStale = vehicleStatus?.stale == true ||
            parseTimestamp(detailsUpdatedAt)?.let { nowMs - it > VEHICLE_DETAILS_STALE_AFTER_MS } == true
        val voltage = details?.optJSONObject("battery12v")?.numberOrNull("voltageV") ?: state?.voltageV
        val batteryTemperature = details?.optJSONObject("battery12v")?.numberOrNull("temperatureC")
        val failedDtc = details?.optJSONObject("diagnostics")?.numberOrNull("alertCount")
            ?: details?.optJSONObject("diagnostics")?.numberOrNull("failedCount")
        val oilLife = details?.optJSONObject("maintenance")?.numberOrNull("oilLifePercent")
        val criticalIssues = mutableListOf<String>()
        val warningIssues = mutableListOf<String>()

        if (voltage != null && voltage <= 11.5) criticalIssues += String.format(Locale.US, "12V %.1fV", voltage)
        else if (voltage != null && voltage < 11.9) warningIssues += String.format(Locale.US, "12V %.1fV", voltage)

        if (batteryTemperature != null && batteryTemperature >= BATTERY_TEMPERATURE_CRITICAL_C) {
            return report("ATTENTION", "HIGH\nTEMPERATURE", "12V battery ${batteryTemperature.roundToInt()} C", "critical")
        } else if (batteryTemperature != null && batteryTemperature >= BATTERY_TEMPERATURE_WARNING_C) {
            warningIssues += "Battery ${batteryTemperature.roundToInt()} C"
        }

        when (state?.thermalStatus?.trim()?.lowercase(Locale.US)) {
            "danger", "red", "overheated" -> criticalIssues += "Comma overheated"
            "yellow", "warning" -> warningIssues += "Comma temperature high"
        }
        if (failedDtc != null && failedDtc > 0) warningIssues += "${failedDtc.roundToInt()} diagnostic alert"

        if (!detailsStale) {
            val closures = details?.optJSONObject("closures")
            if (closures?.isActive("doors") == true) warningIssues += "Doors unlocked"
            if (closures?.isActive("hood") == true) warningIssues += "Hood open"
            if (closures?.isActive("trunk") == true) warningIssues += "Trunk open"
            val openWindows = listOf("windowFrontLeft", "windowFrontRight", "windowRearLeft", "windowRearRight")
                .count { closures?.isActive(it) == true }
            if (openWindows > 0) warningIssues += "$openWindows windows open"
            if (closures?.isActive("sunroof") == true) warningIssues += "Sunroof open"
        }

        if (criticalIssues.isNotEmpty()) {
            return report("ATTENTION", "ATTENTION", (criticalIssues + warningIssues).joinToString(" · "), "critical")
        }

        val tireLow = details?.optJSONObject("tires")?.let { tires ->
            listOf("frontLeftKpa", "frontRightKpa", "rearLeftKpa", "rearRightKpa")
                .mapNotNull { tires.numberOrNull(it) }
                .filter { it in 100.0..400.0 }
                .minOrNull()
                ?.takeIf { it < TIRE_WARNING_KPA }
        }
        if (tireLow != null) {
            return report("CHECK STATUS", "TIRE\nPRESSURE", "${tireLow.roundToInt()} kPa", "warning")
        }
        if (oilLife != null && oilLife in 0.0..OIL_WARNING_PERCENT) {
            return report("CHECK STATUS", "SERVICE\nDUE", "Engine oil service required", "warning")
        }
        val fuelPercent = fuelPercent(details, vehicleStatus?.data)
        val rangeKm = rangeKm(details, vehicleStatus?.data)
        if ((fuelPercent != null && fuelPercent <= FUEL_WARNING_PERCENT) || (rangeKm != null && rangeKm <= 50)) {
            warningIssues += "Low fuel"
        }
        if (warningIssues.isNotEmpty()) {
            return report("CHECK STATUS", "CHECK\nVEHICLE", warningIssues.joinToString(" · "), "warning")
        }

        if (detailsStale) {
            return report("CHECK STATUS", "UPDATE\nDELAYED", "Vehicle data may be outdated", "warning")
        }
        if (state?.onroad == true) {
            state.updatedAt?.let(::parseTimestamp)?.let { updatedAt ->
                if (nowMs - updatedAt > 45_000L) {
                    return report("CHECK STATUS", "UPDATE\nDELAYED", "Vehicle data may be outdated", "warning")
                }
            }
        }
        if (state?.onroad == true && (state.latitude == null || state.longitude == null || state.gpsFresh == false)) {
            return report("CHECK STATUS", "LOCATION\nUNKNOWN", "GPS unavailable", "warning")
        }

        val remoteStart = details?.optJSONObject("remoteStart")
        val engineRunning = details?.optJSONObject("vehicleState")?.optBoolean("engineRunning", false) == true
        if (engineRunning && remoteStart?.optBoolean("remainingTimeValid", false) == true) {
            return report("CHECK STATUS", "REMOTE\nSTART", "Remote start is running", "running")
        }
        if (state?.onroad == true) {
            val detail = state.speedMps?.let { "${(it * 3.6).roundToInt()} km/h" }.orEmpty()
            return report("LIVE STATUS", "DRIVING", detail, "driving")
        }
        if (state?.ignition == true || engineRunning) {
            return report("LIVE STATUS", "ENGINE\nON", "Vehicle is awake", "driving")
        }
        return report("CHECK STATUS", "ALL\nGOOD", "", "secure")
    }

    private fun report(kicker: String, title: String, detail: String, tone: String) =
        MiniHomeStatus(kicker, title, detail, tone)

    private fun rangeKm(details: JSONObject?, data: JSONObject?): Int? =
        details?.optJSONObject("fuel")?.numberOrNull("rangeKm")?.roundToInt()
            ?: firstNumber(data?.stringOrNull("range"))?.roundToInt()

    private fun fuelPercent(details: JSONObject?, data: JSONObject?): Int? {
        val fuel = details?.optJSONObject("fuel")
        fuel?.numberOrNull("levelPercent")?.let { return it.roundToInt().coerceIn(0, 100) }
        val liters = fuel?.numberOrNull("levelLiters")
        val capacity = fuel?.numberOrNull("capacityLiters")
        if (liters != null && capacity != null && capacity > 0) {
            return (liters / capacity * 100).roundToInt().coerceIn(0, 100)
        }
        val raw = data?.stringOrNull("fuel") ?: return null
        val number = firstNumber(raw) ?: return null
        return if (raw.contains('%')) number.roundToInt().coerceIn(0, 100)
        else (number / 82.0 * 100).roundToInt().coerceIn(0, 100)
    }

    private fun firstNumber(value: String?): Double? = value
        ?.let { NUMBER_REGEX.find(it)?.value }
        ?.toDoubleOrNull()

    private fun formatUpdatedAt(value: String?): String {
        val timestamp = parseTimestamp(value) ?: return "--"
        return SimpleDateFormat("yyyy/MM/dd, HH:mm", Locale.KOREA).apply {
            timeZone = TimeZone.getTimeZone("Asia/Seoul")
        }.format(Date(timestamp))
    }

    private fun parseTimestamp(value: String?): Long? {
        if (value.isNullOrBlank()) return null
        val formats = listOf(
            Triple("yyyy-MM-dd'T'HH:mm:ss.SSSXXX", Locale.US, "UTC"),
            Triple("yyyy-MM-dd'T'HH:mm:ssXXX", Locale.US, "UTC"),
            Triple("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US, "UTC"),
            Triple("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US, "UTC"),
            Triple("yyyy-MM-dd HH:mm:ss", Locale.KOREA, "Asia/Seoul"),
        )
        return formats.firstNotNullOfOrNull { (pattern, locale, zone) ->
            runCatching {
                SimpleDateFormat(pattern, locale).apply {
                    isLenient = false
                    timeZone = TimeZone.getTimeZone(zone)
                }.parse(value)?.time
            }.getOrNull()
        }
    }

    private fun JSONObject.stringOrNull(name: String): String? =
        if (!has(name) || isNull(name)) null else optString(name).takeIf { it.isNotBlank() && it != "--" }

    private fun JSONObject.numberOrNull(name: String): Double? =
        if (!has(name) || isNull(name)) null else optDouble(name).takeIf { it.isFinite() }

    private fun JSONObject.isActive(name: String): Boolean =
        optJSONObject(name)?.optBoolean("active", false) == true

    private val NUMBER_REGEX = Regex("-?\\d+(?:\\.\\d+)?")
}
