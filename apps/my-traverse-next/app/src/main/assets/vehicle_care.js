(function (root, factory) {
    const api = factory();
    if (typeof module === "object" && module.exports) module.exports = api;
    if (root) root.VehicleCareReport = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
    "use strict";

    // Comma CAN trip fuel (Traverse) from analysis.fuel (wayon-trip-fuel-v1), shown in the drive report.
    const TRIP_FUEL_SCHEMA = "wayon-trip-fuel-v1";

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
            oilLifePercent: percent(fuel.oilLifePercent),
            observedS: positive(fuel.observedS),
            partial: fuel.partial === true,
            longGaps: positive(fuel.longGaps) ?? 0,
        };
    }

    function tripFuelView(analysis) {
        const fuel = tripFuel(analysis);
        if (!fuel) return null;
        const levels = fuel.levelStartPercent !== null && fuel.levelEndPercent !== null;
        const notes = [];
        if (fuel.partial) notes.push("일부 구간만 읽은 주행이라 사용 연료가 실제보다 적게 나올 수 있어요.");
        if (fuel.longGaps > 0) notes.push("연료 신호가 끊긴 구간은 연료와 거리 모두 빼고 연비를 계산했어요.");
        notes.push("차량 CAN의 연료 사용량 눈금으로 계산한 값이라 몇 % 오차가 있을 수 있어요.");
        return {
            // Short trips (under 1 km or 0.05 L) carry no km/L.
            economyText: fixed(fuel.kmPerL, 1, " km/L"),
            rows: [
                ["사용 연료", fixed(fuel.usedL, 1, " L")],
                ["공회전 연료", fuel.idleL === null ? "--"
                    : `${fixed(fuel.idleL, 1, " L")}${fuel.idlePercent === null ? "" : ` · ${fixed(fuel.idlePercent, 0, "%")}`}`],
                ["100 km당", fixed(fuel.lPer100Km, 1, " L")],
                ["연료량", levels ? `${Math.round(fuel.levelStartPercent)}% → ${Math.round(fuel.levelEndPercent)}%` : "--"],
                ["남은 연료", fuel.levelStartL === null || fuel.levelEndL === null ? "--"
                    : `${fixed(fuel.levelStartL, 1)} → ${fixed(fuel.levelEndL, 1, " L")}`],
                ["연비 계산 거리", fixed(fuel.distanceKm, 1, " km")],
                ["엔진오일 수명", fixed(fuel.oilLifePercent, 0, "%")],
                ["기록된 엔진 시간", duration(fuel.observedS)],
            ],
            notes,
        };
    }

    return { TRIP_FUEL_SCHEMA, tripFuel, tripFuelView };
});
