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
    const VEHICLE_DETAILS_STALE_AFTER_SECONDS = 24 * 60 * 60;
    const LIVE_STALE_AFTER_SECONDS = 45;
    const OFFROAD_LIVE_STALE_AFTER_SECONDS = 660;

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
        return Number.isFinite(parsed) && parsed <= nowMs + 60000 ? Math.max(0, (nowMs - parsed) / 1000) : null;
    }

    function detailsAgeSeconds(details, nowMs) {
        const meta = details?.meta || {};
        const source = String(meta.source || "").toLowerCase();
        const value = source.includes("gmone")
            ? (meta.collectedAt || meta.updatedAt)
            : meta.updatedAt;
        if (typeof value !== "string" || !value.trim()) return null;
        const text = value.trim();
        const normalized = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(text)
            ? `${text.replace(" ", "T")}+09:00`
            : text;
        const parsed = Date.parse(normalized);
        return Number.isFinite(parsed) && parsed <= nowMs + 60000 ? Math.max(0, (nowMs - parsed) / 1000) : null;
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
        const gmoneSource = String(details?.meta?.source || "").toLowerCase().includes("gmone");
        // Offroad uploads normally arrive every 300 seconds; unknown mode keeps the tighter bound.
        const liveMaxAge = live?.onroad === false ? OFFROAD_LIVE_STALE_AFTER_SECONDS : LIVE_STALE_AFTER_SECONDS;
        const detailsMaxAge = gmoneSource ? VEHICLE_DETAILS_STALE_AFTER_SECONDS : liveMaxAge;
        const detailsStale = details?.meta?.stale === true
            || (detailsAge !== null && detailsAge > detailsMaxAge);
        const detailsFresh = hasDetails && !detailsStale && detailsAge !== null;
        const liveAge = hasLive ? liveAgeSeconds(live, nowMs) : null;
        const liveStale = live?.stale === true || (liveAge !== null && liveAge > liveMaxAge);
        const liveFresh = hasLive && live.unavailable !== true && !liveStale && liveAge !== null;
        // Legacy voltageV/deviceInput may describe a USB bench supply, not the vehicle battery.
        const batteryVoltage = detailsFresh && gmoneSource ? number(details?.battery12v?.voltageV) : null;
        const vehicleInput = live?.vehicleInput;
        const inputVoltage = liveFresh && vehicleInput?.qualified === true && vehicleInput?.fresh === true
            && vehicleInput?.kind === "vehicleInputEstimate" ? number(vehicleInput.voltageV) : null;
        const voltage = batteryVoltage ?? inputVoltage;
        const voltageLabel = batteryVoltage !== null ? "12V battery" : "Vehicle input estimate";
        const batteryTemperature = detailsFresh && gmoneSource ? number(details?.battery12v?.temperatureC) : null;
        const failedDtc = detailsFresh
            ? number(details?.diagnostics?.alertCount) ?? number(details?.diagnostics?.failedCount) : null;
        const oilLife = detailsFresh ? number(details?.maintenance?.oilLifePercent) : null;
        const criticalIssues = [];
        const warningIssues = [];

        if (voltage !== null && voltage <= 11.5) criticalIssues.push(`${voltageLabel} ${format(voltage, 1)}V`);
        else if (voltage !== null && voltage < 11.9) warningIssues.push(`${voltageLabel} ${format(voltage, 1)}V`);

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

        const thermal = thermalSeverity(liveFresh ? live.thermalStatus : null);
        if (thermal === "critical") criticalIssues.push("Comma device overheated");
        else if (thermal === "warning") warningIssues.push("Comma device temperature high");

        if (failedDtc !== null && failedDtc > 0) {
            warningIssues.push(`${format(failedDtc)} diagnostic alert${failedDtc === 1 ? "" : "s"}`);
        }
        if (detailsFresh && closures.doors?.active === true) warningIssues.push("Doors unlocked");
        if (detailsFresh && closures.hood?.active === true) warningIssues.push("Hood open");
        if (detailsFresh && closures.trunk?.active === true) warningIssues.push("Trunk open");

        const openWindows = ["windowFrontLeft", "windowFrontRight", "windowRearLeft", "windowRearRight"]
            .filter((key) => closures[key]?.active === true).length;
        if (detailsFresh && openWindows > 0) warningIssues.push(`${openWindows} window${openWindows === 1 ? "" : "s"} open`);
        if (detailsFresh && closures.sunroof?.active === true) warningIssues.push("Sunroof open");

        if (criticalIssues.length) {
            const detail = [...criticalIssues, ...warningIssues].join(" · ");
            return report("critical", "ATTENTION", detail, "triangle-alert");
        }

        const tire = detailsFresh ? tireWarning(details) : null;
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
        const fuel = detailsFresh ? fuelWarning(details) : null;
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

        if (liveStale) {
            return report("warning", "UPDATE\nDELAYED", "Vehicle data may be outdated", "clock-alert");
        }
        if ((hasDetails && !detailsFresh) || (hasLive && !liveFresh)) {
            return report("offline", "STATUS\nUNKNOWN", "Vehicle data freshness is not confirmed", "circle-help");
        }

        if (liveFresh) {
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

        const closureChecks = ["doors", "hood", "trunk", "sunroof", "windowFrontLeft", "windowFrontRight", "windowRearLeft", "windowRearRight"]
            .map((key) => typeof closures[key]?.active === "boolean");
        const tireChecks = ["frontLeftKpa", "frontRightKpa", "rearLeftKpa", "rearRightKpa"]
            .map((key) => {
                const pressure = number(details?.tires?.[key]);
                return pressure !== null && pressure >= 100 && pressure <= 400;
            });
        const healthChecks = [...closureChecks, ...tireChecks, batteryVoltage !== null,
            batteryTemperature !== null, failedDtc !== null, oilLife !== null,
            number(details?.fuel?.levelLiters) !== null && number(details?.fuel?.capacityLiters) > 0,
            number(details?.fuel?.rangeKm) !== null];
        const healthKnown = detailsFresh && healthChecks.every(Boolean) && details?.vehicleState?.engineRunning === false;
        if (!healthKnown) {
            if (detailsFresh && healthChecks.some(Boolean)) {
                return report("", "LIMITED\nDATA", "No issues in reported checks · Some vehicle data is unavailable", "circle-help");
            }
            const detail = inputVoltage === null ? "Vehicle health is not confirmed"
                : `Vehicle input estimate ${format(inputVoltage, 1)}V · Vehicle health is not confirmed`;
            return report("offline", "STATUS\nUNKNOWN", detail, "circle-help");
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
            liveStaleAfterSeconds: LIVE_STALE_AFTER_SECONDS,
            offroadLiveStaleAfterSeconds: OFFROAD_LIVE_STALE_AFTER_SECONDS,
        },
    };
});
