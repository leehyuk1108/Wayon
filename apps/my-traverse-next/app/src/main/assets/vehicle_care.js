(function (root, factory) {
    const api = factory();
    if (typeof module === "object" && module.exports) module.exports = api;
    if (root) root.VehicleCareReport = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
    "use strict";

    // Comma CAN fuel and maintenance figures (Traverse): trip fuel lives in analysis.fuel
    // (wayon-trip-fuel-v1), the latest readings in the live state's vehicleCare block.
    const TRIP_FUEL_SCHEMA = "wayon-trip-fuel-v1";
    const TANK_LITERS = 82;
    const REFUEL_MIN_PERCENT = 8;
    const RECENT_DAYS = 30;
    const OIL_WARNING_PERCENT = 15;
    const DAY_MS = 24 * 60 * 60 * 1000;

    function num(value) {
        if (value === null || value === undefined || value === "" || typeof value === "boolean") return null;
        const number = Number(value);
        return Number.isFinite(number) ? number : null;
    }

    function fixed(value, digits, suffix = "") {
        const number = num(value);
        return number === null ? "--" : `${number.toLocaleString("ko-KR", {
            minimumFractionDigits: digits, maximumFractionDigits: digits })}${suffix}`;
    }

    function duration(seconds) {
        const value = num(seconds);
        if (value === null || value < 0) return "--";
        const minutes = Math.round(value / 60);
        if (minutes < 60) return `${minutes}분`;
        return `${Math.floor(minutes / 60)}시간 ${minutes % 60}분`;
    }

    function shortDate(ms) {
        const date = new Date(ms);
        return `${date.getMonth() + 1}/${date.getDate()}`;
    }

    function shortDateTime(ms) {
        const date = new Date(ms);
        return `${shortDate(ms)} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
    }

    function tripFuel(analysis) {
        const fuel = analysis && typeof analysis === "object" ? analysis.fuel : null;
        if (!fuel || typeof fuel !== "object" || Array.isArray(fuel) || fuel.schemaVersion !== TRIP_FUEL_SCHEMA) return null;
        const usedL = num(fuel.usedL);
        if (usedL === null || usedL < 0 || usedL > 200) return null;
        const percent = (value) => {
            const number = num(value);
            return number !== null && number >= 0 && number <= 100 ? number : null;
        };
        const positive = (value) => {
            const number = num(value);
            return number !== null && number >= 0 ? number : null;
        };
        return {
            usedL,
            idleL: positive(fuel.idleL),
            idlePercent: percent(fuel.idlePercent),
            distanceKm: positive(fuel.distanceKm),
            kmPerL: positive(fuel.kmPerL),
            lPer100Km: positive(fuel.lPer100Km),
            levelStartPercent: percent(fuel.levelStartPercent),
            levelEndPercent: percent(fuel.levelEndPercent),
            levelStartL: positive(fuel.levelStartL),
            levelEndL: positive(fuel.levelEndL),
            odometerEndKm: positive(fuel.odometerEndKm),
            oilLifePercent: percent(fuel.oilLifePercent),
            observedS: positive(fuel.observedS),
            partial: fuel.partial === true,
        };
    }

    function tripFuelView(analysis) {
        const fuel = tripFuel(analysis);
        if (!fuel) return null;
        const levels = fuel.levelStartPercent !== null && fuel.levelEndPercent !== null;
        const notes = [];
        if (fuel.partial) notes.push("일부 구간만 읽은 주행이라 실제보다 적게 나올 수 있어요.");
        notes.push("차량 CAN의 연료 사용량 눈금으로 계산한 값이라 몇 % 오차가 있을 수 있어요.");
        return {
            overview: [
                ["사용 연료", fixed(fuel.usedL, 1, " L")],
                ["연비", fixed(fuel.kmPerL, 1, " km/L")],
                ["공회전 연료", fuel.idleL === null ? "--"
                    : `${fixed(fuel.idleL, 1, " L")}${fuel.idlePercent === null ? "" : ` · ${fixed(fuel.idlePercent, 0, "%")}`}`],
                ["연료량", levels ? `${Math.round(fuel.levelStartPercent)}% → ${Math.round(fuel.levelEndPercent)}%` : "--"],
            ],
            rows: [
                ["100 km당", fixed(fuel.lPer100Km, 1, " L")],
                ["계기판 기준 거리", fixed(fuel.distanceKm, 1, " km")],
                ["남은 연료", fuel.levelStartL === null || fuel.levelEndL === null ? "--"
                    : `${fixed(fuel.levelStartL, 1)} → ${fixed(fuel.levelEndL, 1, " L")}`],
                ["엔진오일 수명", fixed(fuel.oilLifePercent, 0, "%")],
                ["기록된 엔진 시간", duration(fuel.observedS)],
            ],
            listText: fuel.kmPerL !== null ? `${fixed(fuel.kmPerL, 1, " km/L")} · ${fixed(fuel.usedL, 1, " L")}`
                : `${fixed(fuel.usedL, 1, " L")} 사용`,
            notes,
        };
    }

    function fuelTrips(items, timeOf, normalize) {
        const trips = [];
        for (const item of Array.isArray(items) ? items : []) {
            const analysis = normalize ? normalize(item?.analysis) : item?.analysis;
            const fuel = tripFuel(analysis);
            const time = num(timeOf ? timeOf(item) : null);
            if (fuel && time !== null && time > 0) trips.push({ time, fuel });
        }
        return trips.sort((a, b) => a.time - b.time);
    }

    function detectRefuels(trips) {
        const refuels = [];
        for (let index = 1; index < trips.length; index += 1) {
            const before = trips[index - 1].fuel.levelEndPercent;
            const after = trips[index].fuel.levelStartPercent;
            if (before === null || after === null || after - before < REFUEL_MIN_PERCENT) continue;
            refuels.push({ time: trips[index].time, index, fromPercent: before, toPercent: after,
                addedL: (after - before) / 100 * TANK_LITERS });
        }
        return refuels;
    }

    function sumEconomy(trips) {
        let usedL = 0;
        let distanceKm = 0;
        let idleL = 0;
        let economyUsedL = 0;
        for (const { fuel } of trips) {
            usedL += fuel.usedL;
            idleL += fuel.idleL ?? 0;
            if (fuel.distanceKm !== null) {
                distanceKm += fuel.distanceKm;
                economyUsedL += fuel.usedL;
            }
        }
        return { count: trips.length, usedL, distanceKm, idleL,
            kmPerL: distanceKm >= 1 && economyUsedL >= 0.05 ? distanceKm / economyUsedL : null,
            idlePercent: usedL > 0 ? idleL / usedL * 100 : null };
    }

    function liveCare(live) {
        const care = live && typeof live === "object" ? live.vehicleCare : null;
        if (!care || typeof care !== "object" || Array.isArray(care)) return null;
        const observedAt = Date.parse(care.observedAt);
        if (!Number.isFinite(observedAt)) return null;
        const value = (key, low, high) => {
            const number = num(care[key]);
            return number !== null && number >= low && number <= high ? number : null;
        };
        return {
            fresh: care.fresh === true,
            observedAt,
            fuelLevelPercent: value("fuelLevelPercent", 0, 100),
            fuelLiters: value("fuelLiters", 0, 200),
            oilLifePercent: value("oilLifePercent", 0, 100),
            odometerKm: value("odometerKm", 0, 2000000),
            batteryVoltage: value("batteryVoltage", 6, 18),
            batteryCurrentA: value("batteryCurrentA", -1000, 1000),
            batterySocPercent: value("batterySocPercent", 0, 100),
        };
    }

    function careSummary(items, live, nowMs = Date.now(), options = {}) {
        const trips = fuelTrips(items, options.timeOf, options.normalize);
        const care = liveCare(live);
        const rows = [];
        const recent = sumEconomy(trips.filter(trip => nowMs - trip.time <= RECENT_DAYS * DAY_MS));
        if (recent.count) {
            rows.push({ label: `최근 ${RECENT_DAYS}일 연비`, value: recent.kmPerL === null ? "--"
                : `${fixed(recent.kmPerL, 1, " km/L")} · ${fixed(100 / recent.kmPerL, 1, " L/100km")}` });
            rows.push({ label: `최근 ${RECENT_DAYS}일 주행`, value:
                `${recent.count}회 · ${fixed(recent.distanceKm, 0, " km")} · ${fixed(recent.usedL, 1, " L")}` });
            if (recent.idlePercent !== null) rows.push({ label: "공회전 연료 비율", value: fixed(recent.idlePercent, 0, "%") });
        }
        const refuels = detectRefuels(trips);
        const last = refuels[refuels.length - 1];
        if (last) {
            rows.push({ label: "마지막 주유", value:
                `${shortDate(last.time)} · 약 +${fixed(last.addedL, 0, " L")} (${Math.round(last.fromPercent)}% → ${Math.round(last.toPercent)}%)` });
            const since = sumEconomy(trips.slice(last.index));
            rows.push({ label: "주유 후", value: `${fixed(since.distanceKm, 0, " km")} · ${fixed(since.usedL, 1, " L")}`
                + (since.kmPerL === null ? "" : ` · ${fixed(since.kmPerL, 1, " km/L")}`) });
        }
        let oilWarning = false;
        if (care) {
            if (care.fuelLevelPercent !== null) {
                rows.push({ label: "연료량", value: `${fixed(care.fuelLevelPercent, 0, "%")}`
                    + (care.fuelLiters === null ? "" : ` · 약 ${fixed(care.fuelLiters, 0, " L")}`) });
            }
            if (care.oilLifePercent !== null) {
                oilWarning = care.oilLifePercent <= OIL_WARNING_PERCENT;
                rows.push({ label: "엔진오일 수명", value: `${fixed(care.oilLifePercent, 0, "%")}${oilWarning ? " · 교환 시기" : ""}` });
            }
            if (care.batterySocPercent !== null) rows.push({ label: "12V 배터리 충전", value: fixed(care.batterySocPercent, 0, "%") });
            // Voltage and current mean something only while the engine runs (the alternator charges);
            // a parked last-known 14 V would mislead.
            if (care.fresh && care.batteryVoltage !== null) {
                const current = care.batteryCurrentA;
                rows.push({ label: "배터리 전압", value: `${fixed(care.batteryVoltage, 1, " V")}`
                    + (current === null ? "" : ` · ${current >= 0 ? "충전" : "방전"} ${fixed(Math.abs(current), 0, " A")}`) });
            }
            if (care.odometerKm !== null) rows.push({ label: "주행거리계", value: fixed(care.odometerKm, 0, " km") });
        }
        const meta = care ? (care.fresh ? "주행 중 실시간" : `마지막 수신 ${shortDateTime(care.observedAt)}`)
            : (trips.length ? `주행 기록 ${trips.length}회 기준` : "콤마 CAN");
        return { rows, meta, oilWarning, empty: rows.length === 0,
            emptyText: "다음 주행부터 콤마가 차량 CAN으로 연비와 차량 기록을 보내요." };
    }

    return { TRIP_FUEL_SCHEMA, TANK_LITERS, REFUEL_MIN_PERCENT, RECENT_DAYS, OIL_WARNING_PERCENT,
        tripFuel, tripFuelView, fuelTrips, detectRefuels, sumEconomy, liveCare, careSummary };
});
