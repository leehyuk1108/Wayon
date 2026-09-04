(function (root, factory) {
    const policy = factory();
    if (typeof module === "object" && module.exports) module.exports = policy;
    if (root) root.VehicleStatusPolicy = policy;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
    "use strict";

    const TIRE_WARNING_KPA = 200;
    const OIL_WARNING_PERCENT = 10;
    const FUEL_WARNING_PERCENT = 10;
    const BATTERY_TEMPERATURE_WARNING_C = 55;
    const BATTERY_TEMPERATURE_CRITICAL_C = 65;
    const VEHICLE_DETAILS_STALE_AFTER_SECONDS = 10 * 60;

    function number(value) {
        if (value === null || value === undefined || value === "") return null;
        const parsed = Number(value);
        return Number.isFinite(parsed) ? parsed : null;
    }

    function format(value, digits = 0) {
        const parsed = number(value);
        if (parsed === null) return "--";
        return parsed.toLocaleString("en-US", {
            minimumFractionDigits: digits,
            maximumFractionDigits: digits,
        });
    }

    function report(tone, title, detail, icon, healthDetail = detail) {
        return { tone, title, detail: detail || "", icon, healthDetail: healthDetail || "" };
    }

    function thermalSeverity(status) {
        const normalized = String(status || "").trim().toLowerCase();
        if (["danger", "red", "overheated"].includes(normalized)) return "critical";
        if (["yellow", "warning"].includes(normalized)) return "warning";
        return "normal";
    }

    function liveAgeSeconds(live, nowMs) {
        const parsed = Date.parse(live?.updatedAt || "");
        return Number.isFinite(parsed) ? Math.max(0, (nowMs - parsed) / 1000) : null;
    }

    function detailsAgeSeconds(details, nowMs) {
        const value = details?.meta?.updatedAt;
        if (typeof value !== "string" || !value.trim()) return null;
        const text = value.trim();
        const normalized = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(text)
            ? `${text.replace(" ", "T")}+09:00`
            : text;
        const parsed = Date.parse(normalized);
        return Number.isFinite(parsed) ? Math.max(0, (nowMs - parsed) / 1000) : null;
    }

    function speedDetail(live, suffix) {
        const speedKph = number(live?.speedKph);
        return `${speedKph === null ? "--" : Math.round(speedKph)} km/h · ${suffix}`;
    }

    function remainingTimeLabel(remoteStart) {
        const raw = number(remoteStart?.remainingTimeRaw);
        if (raw === null) return "--:--";
        const totalSeconds = Math.max(0, Math.round(raw));
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        if (hours > 0) return `${hours}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
        return `${minutes}:${String(seconds).padStart(2, "0")}`;
    }

    function tireWarning(details) {
        const tires = details?.tires || {};
        const entries = [
            ["Front left", number(tires.frontLeftKpa)],
            ["Front right", number(tires.frontRightKpa)],
            ["Rear left", number(tires.rearLeftKpa)],
            ["Rear right", number(tires.rearRightKpa)],
        ].filter((entry) => entry[1] !== null && entry[1] >= 100 && entry[1] <= 400);
        if (!entries.length) return null;
        const lowest = entries.reduce((result, entry) => entry[1] < result[1] ? entry : result);
        return lowest[1] < TIRE_WARNING_KPA ? `${lowest[0]} tire ${Math.round(lowest[1])} kPa` : null;
    }

    function fuelWarning(details) {
        const level = number(details?.fuel?.levelLiters);
        const capacity = number(details?.fuel?.capacityLiters);
        const range = number(details?.fuel?.rangeKm);
        const percent = level !== null && capacity !== null && capacity > 0 ? level / capacity * 100 : null;
        if ((percent !== null && percent <= FUEL_WARNING_PERCENT) || (range !== null && range <= 50)) {
            const parts = [];
            if (percent !== null) parts.push(`${Math.round(percent)}% fuel`);
            if (range !== null) parts.push(`${Math.round(range)} km range`);
            return parts.join(" · ") || "Low fuel";
        }
        return null;
    }

    function evaluate(details, live, nowMs = Date.now(), impact = null) {
        if (impact && typeof impact === "object") {
            const receivedAt = number(impact.receivedAtMs);
            const detectedAt = Date.parse(impact.detectedAt || "");
            const eventTime = receivedAt ?? (Number.isFinite(detectedAt) ? detectedAt : null);
            if (eventTime !== null && nowMs - eventTime <= 30 * 60 * 1000) {
                return report(
                    "critical",
                    "IMPACT\nDETECTED",
                    "Parking security event · Check 360° Live",
                    "shield-alert",
                );
            }
        }

        const hasDetails = details && typeof details === "object";
        const hasLive = live && typeof live === "object";
        if (!hasDetails && !hasLive) {
            return report("offline", "CHECKING", "Waiting for vehicle data", "loader-circle");
        }

        const closures = hasDetails ? details.closures || {} : {};
        const detailsAge = hasDetails ? detailsAgeSeconds(details, nowMs) : null;
        const detailsStale = details?.meta?.stale === true
            || (detailsAge !== null && detailsAge > VEHICLE_DETAILS_STALE_AFTER_SECONDS);
        const voltage = number(details?.battery12v?.voltageV) ?? number(live?.voltageV);
        const batteryTemperature = number(details?.battery12v?.temperatureC);
        const failedDtc = number(details?.diagnostics?.alertCount)
            ?? number(details?.diagnostics?.failedCount);
        const oilLife = number(details?.maintenance?.oilLifePercent);
        const criticalIssues = [];
        const warningIssues = [];

        if (voltage !== null && voltage <= 11.5) criticalIssues.push(`12V battery ${format(voltage, 1)}V`);
        else if (voltage !== null && voltage < 11.9) warningIssues.push(`12V battery ${format(voltage, 1)}V`);

        if (batteryTemperature !== null && batteryTemperature >= BATTERY_TEMPERATURE_CRITICAL_C) {
            return report(
                "critical",
                "HIGH\nTEMPERATURE",
                `12V battery ${format(batteryTemperature)}°C`,
                "thermometer-sun",
            );
        } else if (batteryTemperature !== null && batteryTemperature >= BATTERY_TEMPERATURE_WARNING_C) {
            warningIssues.push(`12V battery ${format(batteryTemperature)}°C`);
        }

        const thermal = thermalSeverity(live?.thermalStatus);
        if (thermal === "critical") criticalIssues.push("Comma device overheated");
        else if (thermal === "warning") warningIssues.push("Comma device temperature high");

        if (failedDtc !== null && failedDtc > 0) {
            warningIssues.push(`${format(failedDtc)} diagnostic alert${failedDtc === 1 ? "" : "s"}`);
        }
        if (!detailsStale && closures.doors?.active === true) warningIssues.push("Doors unlocked");
        if (!detailsStale && closures.hood?.active === true) warningIssues.push("Hood open");
        if (!detailsStale && closures.trunk?.active === true) warningIssues.push("Trunk open");

        const openWindows = ["windowFrontLeft", "windowFrontRight", "windowRearLeft", "windowRearRight"]
            .filter((key) => closures[key]?.active === true).length;
        if (!detailsStale && openWindows > 0) warningIssues.push(`${openWindows} window${openWindows === 1 ? "" : "s"} open`);
        if (!detailsStale && closures.sunroof?.active === true) warningIssues.push("Sunroof open");

        if (criticalIssues.length) {
            const detail = [...criticalIssues, ...warningIssues].join(" · ");
            return report("critical", "ATTENTION", detail, "triangle-alert");
        }

        const tire = tireWarning(details);
        if (tire) {
            const tireKpa = number(String(tire).match(/(\d+) kPa/)?.[1]);
            const tirePsi = tireKpa === null ? null : Math.round(tireKpa * 0.1450377377);
            const tirePosition = String(tire).replace(/ tire .*$/, "");
            const tireDetail = tirePsi === null
                ? `${tirePosition} · Check tire`
                : `${tirePosition} ${tirePsi} psi · Check tire`;
            return report("warning", "TIRE\nPRESSURE", tireDetail, "circle-gauge");
        }
        if (oilLife !== null && oilLife >= 0 && oilLife <= OIL_WARNING_PERCENT) {
            return report("warning", "SERVICE\nDUE", "Engine oil service required", "wrench");
        }
        const fuel = fuelWarning(details);
        if (fuel) warningIssues.push(fuel);

        if (warningIssues.length) {
            const detail = warningIssues.join(" · ");
            return report("warning", "CHECK\nVEHICLE", detail, "triangle-alert");
        }

        if (live?.unavailable === true) {
            return report("offline", "VEHICLE\nOFFLINE", live.message || "Last connection unavailable", "cloud-off");
        }

        if (detailsStale) {
            return report("warning", "UPDATE\nDELAYED", "Lock status is not confirmed", "clock-alert");
        }

        if (hasLive) {
            const ageSeconds = liveAgeSeconds(live, nowMs);
            const staleAfterSeconds = live.onroad === true ? 45 : 600;
            if (ageSeconds !== null && ageSeconds > staleAfterSeconds) {
                return report("warning", "UPDATE\nDELAYED", "Vehicle data may be outdated", "clock-alert");
            }
            if (live.onroad === true && (live.latitude == null || live.longitude == null || live.gpsFresh === false)) {
                return report("warning", "LOCATION\nUNKNOWN", "Vehicle status received · GPS unavailable", "map-pin-off");
            }
        }

        const remainingStarts = number(details?.remoteStart?.remainingStarts);
        if (remainingStarts !== null && remainingStarts <= 0) {
            return report("warning", "START\nUNAVAILABLE", "No remote starts remaining", "power-off");
        }
        if (Number(details?.module?.settings?.all_function_stop) === 0) {
            return report("warning", "REMOTE\nUNAVAILABLE", "Multipack functions are disabled", "power-off");
        }

        const engineRunning = details?.vehicleState?.engineRunning === true;
        const remoteRunning = engineRunning && details?.remoteStart?.remainingTimeValid === true;
        if (remoteRunning) {
            return report(
                "running",
                "REMOTE\nSTART",
                `${remainingTimeLabel(details.remoteStart)} remaining`,
                "power",
                "Remote start is running",
            );
        }

        if (live?.onroad === true) {
            if (live.openpilotActive === true) {
                return report("driving", "DRIVING", speedDetail(live, "Openpilot engaged"), "navigation");
            }
            const opDetail = live.openpilotEnabled === true ? "Openpilot enabled" : "Openpilot disengaged";
            return report("driving", "DRIVING", speedDetail(live, opDetail), "navigation");
        }

        if (live?.ignition === true || engineRunning) {
            return report("driving", "ENGINE\nON", "Vehicle is awake", "power");
        }

        return report("secure", "ALL\nGOOD", "", "check", "No issues detected");
    }

    return {
        evaluate,
        thresholds: {
            tireWarningKpa: TIRE_WARNING_KPA,
            oilWarningPercent: OIL_WARNING_PERCENT,
            fuelWarningPercent: FUEL_WARNING_PERCENT,
            batteryTemperatureWarningC: BATTERY_TEMPERATURE_WARNING_C,
            batteryTemperatureCriticalC: BATTERY_TEMPERATURE_CRITICAL_C,
            vehicleDetailsStaleAfterSeconds: VEHICLE_DETAILS_STALE_AFTER_SECONDS,
        },
    };
});
