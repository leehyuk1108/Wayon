const el = (id) => document.getElementById(id);

const connectionPill = el("connectionPill");
const connectionStatus = el("connectionStatus");
const refreshButton = el("refreshButton");
const tokenButton = el("tokenButton");
const tokenDialog = el("tokenDialog");
const tokenForm = el("tokenForm");
const tokenInput = el("tokenInput");
const tokenError = el("tokenError");
const closeTokenDialog = el("closeTokenDialog");
const disconnectButton = el("disconnectButton");
const recenterButton = el("recenterButton");
const clearRouteButton = el("clearRouteButton");

const viewButtons = [...document.querySelectorAll("[data-view-target]")];
const views = [...document.querySelectorAll("[data-view]")];
const cameraFilterButtons = [...document.querySelectorAll("[data-camera-filter]")];

const DEFAULT_CENTER = [36.35, 127.9];
const DEFAULT_ZOOM = 7;
const TRAVERSE_FUEL_CAPACITY_L = 82;
const REFRESH_INTERVAL_MS = 30_000;
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const animatedNumberIds = new Set(["rangeValue", "speedValue", "fuelValue", "odometerValue"]);
const numberAnimationFrames = new Map();

let currentView = "overview";
let currentCameraFilter = "all";
let currentPosition = null;
let currentOnroad = false;
let currentTrips = [];
let currentSnapshots = [];
let activeTripId = null;
let refreshInFlight = false;
let overviewMarker = null;
let tripCurrentMarker = null;
let activeTripBounds = null;
let snapshotObjectUrls = [];

function tokenFromHash() {
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  return params.get("token") || "";
}

let token = tokenFromHash() || localStorage.getItem("wayonViewToken") || "";
if (token) {
  localStorage.setItem("wayonViewToken", token);
  window.history.replaceState(null, "", `${window.location.pathname}${window.location.search}`);
}
tokenInput.value = token;

window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } });

function makeMap(containerId) {
  const map = L.map(containerId, {
    zoomControl: false,
    attributionControl: true,
  }).setView(DEFAULT_CENTER, DEFAULT_ZOOM);

  L.control.zoom({ position: "topright" }).addTo(map);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    attribution: "&copy; OpenStreetMap contributors &copy; CARTO",
    subdomains: "abcd",
    maxZoom: 20,
  }).addTo(map);
  return map;
}

const overviewMap = makeMap("overviewMap");
const tripMap = makeMap("tripMap");
const tripRouteLayer = L.layerGroup().addTo(tripMap);

function authHeaders() {
  return token ? { authorization: `Bearer ${token}` } : {};
}

function setConnection(kind, text) {
  connectionPill.classList.toggle("online", kind === "online");
  connectionPill.classList.toggle("error", kind === "error");
  connectionStatus.textContent = text;
}

function finiteNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function firstNumber(...values) {
  for (const value of values) {
    const candidate = typeof value === "string"
      ? value.replace(/,/g, "").replace(/[^\d.-]/g, "")
      : value;
    if (candidate === "" || candidate == null) continue;
    const number = finiteNumber(candidate);
    if (number != null) return number;
  }
  return null;
}

function cleanValue(value) {
  const text = String(value ?? "").trim();
  return text && text !== "--" ? text : "";
}

function fmtNumber(value, digits = 1) {
  const number = finiteNumber(value);
  return number == null ? "--" : number.toFixed(digits);
}

function fmtDate(value, options = {}) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  return date.toLocaleString("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    ...options,
  });
}

function firebaseDate(value) {
  const text = cleanValue(value);
  if (!text) return null;
  const date = new Date(`${text.replace(" ", "T")}+09:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}

function relativeTime(value) {
  if (!value) return "--";
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  const seconds = Math.round((date.getTime() - Date.now()) / 1000);
  const formatter = new Intl.RelativeTimeFormat("ko", { numeric: "auto" });
  if (Math.abs(seconds) < 60) return formatter.format(seconds, "second");
  const minutes = Math.round(seconds / 60);
  if (Math.abs(minutes) < 60) return formatter.format(minutes, "minute");
  const hours = Math.round(minutes / 60);
  if (Math.abs(hours) < 24) return formatter.format(hours, "hour");
  return formatter.format(Math.round(hours / 24), "day");
}

function fmtDuration(seconds) {
  const total = Math.max(0, Number(seconds) || 0);
  const hours = Math.floor(total / 3600);
  const minutes = Math.round((total % 3600) / 60);
  if (hours > 0) return `${hours}시간 ${minutes}분`;
  return `${minutes}분`;
}

function fmtDistance(meters) {
  const km = (Number(meters) || 0) / 1000;
  if (km >= 100) return `${Math.round(km)} km`;
  if (km >= 10) return `${km.toFixed(1)} km`;
  return `${km.toFixed(2)} km`;
}

function fmtKph(mps) {
  const number = finiteNumber(mps);
  return number == null ? "--" : String(Math.round(Math.max(0, number * 3.6)));
}

function fmtCoords(lat, lon, accuracy) {
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return "--";
  const suffix = Number.isFinite(accuracy) ? ` · 정확도 ${accuracy.toFixed(0)}m` : "";
  return `${lat.toFixed(5)}, ${lon.toFixed(5)}${suffix}`;
}

function parseRawState(state) {
  if (!state?.raw_json) return {};
  try {
    return JSON.parse(state.raw_json);
  } catch {
    return {};
  }
}

function vehicleData(vehicleStatus) {
  return vehicleStatus?.ok && vehicleStatus.data ? vehicleStatus.data : {};
}

function fuelLiters(status) {
  const fuel = cleanValue(status.fuel);
  if (!fuel || fuel.includes("%")) return null;
  return firstNumber(fuel);
}

function fuelPercent(status) {
  const fuel = cleanValue(status.fuel);
  if (!fuel) return null;
  if (fuel.includes("%")) return firstNumber(fuel);
  const liters = fuelLiters(status);
  return liters == null ? null : Math.min(100, (liters / TRAVERSE_FUEL_CAPACITY_L) * 100);
}

function rangeFields(raw, status) {
  return {
    rangeKm: firstNumber(
      status.range,
      raw.rangeKm,
      raw.range_km,
      raw.vehicleRangeKm,
      raw.fuelRangeKm,
      raw.batteryRangeKm,
    ),
    percent: firstNumber(
      fuelPercent(status),
      raw.rangePercent,
      raw.range_percent,
      raw.fuelPercent,
      raw.fuel_level_percent,
    ),
  };
}

function tirePressureData(status) {
  const source = cleanValue(status.tire_pressure);
  const matches = [...source.matchAll(/(\d+)\s*(kpa|psi)/gi)].slice(0, 4);
  if (!matches.length) return { text: "--", unit: "" };
  return {
    text: matches.map((match) => match[1]).join(" · "),
    unit: matches[0][2].toUpperCase(),
  };
}

function normalizedDtc(value) {
  const text = cleanValue(value);
  if (!text) return "--";
  return /no\s*error|no\s*dtc|normal|정상/i.test(text) ? "정상" : text;
}

function thermalLabel(value) {
  const text = cleanValue(value).toLowerCase();
  if (!text) return "--";
  if (text === "ok" || text === "green") return "정상";
  if (text === "yellow") return "주의";
  if (text === "red" || text === "danger") return "높음";
  return text;
}

function commaFresh(state) {
  if (!state?.updated_at) return false;
  const age = Date.now() - new Date(state.updated_at).getTime();
  const threshold = Number(state.onroad) ? 3 * 60_000 : 45 * 60_000;
  return age >= 0 && age <= threshold;
}

function markerIcon(onroad) {
  queueMicrotask(() => window.lucide?.createIcons({ attrs: { "stroke-width": 1.8 } }));
  return L.divIcon({
    className: "",
    html: `<div class="vehicle-marker${onroad ? " onroad" : ""}"><i data-lucide="car-front"></i></div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
  });
}

function speedColor(mps) {
  const kph = Math.max(0, Number(mps) * 3.6 || 0);
  if (kph < 45) return "#248a3d";
  if (kph < 85) return "#ff9f0a";
  return "#d70015";
}

function routePointSpeed(point) {
  return firstNumber(point?.speedMps, point?.speed_mps, point?.speed);
}

async function api(path) {
  const response = await fetch(path, {
    headers: authHeaders(),
    cache: "no-store",
  });
  if (!response.ok) {
    const error = new Error(`${response.status} ${response.statusText}`);
    error.status = response.status;
    throw error;
  }
  return response.json();
}

function setText(id, value) {
  const node = el(id);
  const text = String(value);
  const target = Number(text.replace(/,/g, ""));
  const shouldAnimate = animatedNumberIds.has(id)
    && Number.isFinite(target)
    && !node.dataset.numberAnimated
    && !reduceMotion;

  if (!shouldAnimate) {
    node.textContent = text;
    return;
  }

  node.dataset.numberAnimated = "true";
  const existingFrame = numberAnimationFrames.get(id);
  if (existingFrame) cancelAnimationFrame(existingFrame);

  const startedAt = performance.now();
  const duration = 900;
  const format = (number) => (
    node.dataset.numberFormat === "comma"
      ? Math.round(number).toLocaleString("ko-KR")
      : String(Math.round(number))
  );
  const tick = (now) => {
    const progress = Math.min(1, (now - startedAt) / duration);
    const eased = 1 - ((1 - progress) ** 3);
    node.textContent = format(target * eased);
    if (progress < 1) {
      numberAnimationFrames.set(id, requestAnimationFrame(tick));
    } else {
      numberAnimationFrames.delete(id);
    }
  };
  numberAnimationFrames.set(id, requestAnimationFrame(tick));
}

function setStatusItem(id, value, active = false) {
  const item = el(id);
  item.classList.toggle("active", active);
  item.querySelector("[data-status-value]").textContent = value;
}

function renderEmptyState() {
  setText("driveState", "연결 대기");
  setText("driveBadge", "--");
  el("driveBadge").classList.remove("onroad");
  setText("stateDescription", "Wayon Cloud에 연결하면 차량과 콤마 상태가 표시됩니다.");
  setText("lastUpdated", "업데이트 대기 중");
  setText("rangeValue", "--");
  setText("speedValue", "--");
  setText("fuelValue", "--");
  setText("odometerValue", "--");
  setText("currentAddress", "위치 데이터 대기 중");
  setText("currentCoords", "--");
  setText("gpsBadge", "GPS --");
  setText("healthStatus", "확인 중");
  el("healthStatus").className = "health-label";
  el("rangeFill").style.width = "0%";

  for (const id of [
    "vehicleBattery", "vehicleBatteryLife", "oilLife", "tirePressure",
    "commaPower", "commaVoltage", "thermalStatus", "fanStatus",
    "screenBrightness", "deviceId", "dtcStatus", "firebaseUpdatedAt",
    "batteryLevel", "refreshStatus", "commaUpdatedAt", "gpsSource",
    "currentDraw", "vehicleSpeedSource",
  ]) {
    setText(id, "--");
  }

  setStatusItem("ignitionChip", "--");
  setStatusItem("openpilotChip", "--");
  setStatusItem("commaChip", "--");
}

function renderState(state, status = {}) {
  if (!state) {
    renderEmptyState();
    return;
  }

  const raw = parseRawState(state);
  const onroad = Boolean(Number(state.onroad));
  const ignition = Boolean(Number(state.ignition));
  const enabled = Boolean(Number(state.enabled));
  const commaIsFresh = commaFresh(state);
  const { rangeKm, percent } = rangeFields(raw, status);
  const fuel = cleanValue(status.fuel);
  const liters = fuelLiters(status);
  const oil = firstNumber(status.oil);
  const vehicleBatteryVoltage = firstNumber(status.battery);
  const batteryLevelValue = firstNumber(status.battery_level);
  const batteryLifeValue = firstNumber(status.battery_life);
  const odometer = cleanValue(status.mileage).replace(/[^\d,.]/g, "");
  const firebaseUpdated = firebaseDate(status.last_update);
  const tire = tirePressureData(status);
  const lat = finiteNumber(state.latitude);
  const lon = finiteNumber(state.longitude);
  const accuracy = finiteNumber(state.gps_accuracy_m);
  const gps = raw.gps || {};

  currentOnroad = onroad;
  setText("driveState", onroad ? "주행 중" : "주차됨");
  setText("driveBadge", onroad ? "실시간" : "최근 상태");
  el("driveBadge").classList.toggle("onroad", onroad);
  setText(
    "stateDescription",
    onroad
      ? (enabled ? "OpenPilot이 활성화된 상태로 주행 중입니다." : "차량 시동이 켜져 있고 OpenPilot은 대기 중입니다.")
      : "시동이 꺼져 있습니다. 마지막 위치와 차량 상태를 표시합니다.",
  );
  setText(
    "lastUpdated",
    `Comma ${relativeTime(state.updated_at)}${firebaseUpdated ? ` · 차량 ${relativeTime(firebaseUpdated)}` : ""}`,
  );

  setStatusItem("ignitionChip", ignition ? "켜짐" : "꺼짐", ignition);
  setStatusItem("openpilotChip", enabled ? "활성" : "대기", enabled);
  setStatusItem("commaChip", commaIsFresh ? "온라인" : "대기", commaIsFresh);

  setText("rangeValue", rangeKm == null ? "--" : String(Math.round(rangeKm)));
  setText("rangeHint", percent == null ? "연료 잔량 정보 없음" : `연료 기준 ${Math.round(percent)}%`);
  el("rangeFill").style.width = `${Math.max(0, Math.min(100, percent || 0))}%`;
  setText("speedValue", fmtKph(state.speed_mps));
  setText("speedSource", raw.vehicleSpeedSource ? `Comma · ${raw.vehicleSpeedSource}` : "Comma 차량 속도");
  setText("fuelValue", liters == null ? (fuel || "--") : String(Math.round(liters)));
  setText("fuelUnit", fuel.includes("%") ? "%" : "L");
  setText("fuelHint", percent == null ? "통합 차량 정보" : `탱크 잔량 ${Math.round(percent)}%`);
  setText("odometerValue", odometer || "--");
  setText("vehicleDataAge", firebaseUpdated ? `차량 ${relativeTime(firebaseUpdated)}` : "차량 정보 대기");

  setText("vehicleBattery", vehicleBatteryVoltage == null ? "--" : `${vehicleBatteryVoltage.toFixed(1)} V`);
  setText("vehicleBatteryLife", batteryLifeValue == null ? "수명 정보 없음" : `수명 ${Math.round(batteryLifeValue)}%`);
  setText("oilLife", oil == null ? "--" : `${Math.round(oil)}%`);
  setText("tirePressure", tire.text === "--" ? "--" : `${tire.text} ${tire.unit}`);
  setText("commaPower", state.power_w == null ? "--" : `${fmtNumber(state.power_w, 1)} W`);
  setText("commaVoltage", state.voltage_v == null ? "전압 --" : `전압 ${fmtNumber(state.voltage_v, 2)} V`);
  setText("thermalStatus", thermalLabel(state.thermal_status));
  setText("fanStatus", state.fan_percent == null ? "팬 --" : `팬 ${Math.round(state.fan_percent)}%`);
  setText("screenBrightness", state.screen_brightness_percent == null ? "--" : `${Math.round(state.screen_brightness_percent)}%`);
  setText("deviceId", raw.dongleId ? `기기 ${String(raw.dongleId).slice(-6)}` : "기기 --");

  const healthy = normalizedDtc(status.dtc) === "정상" && thermalLabel(state.thermal_status) === "정상";
  setText("healthStatus", healthy ? "모두 정상" : "확인 필요");
  el("healthStatus").className = `health-label ${healthy ? "healthy" : "warning"}`;
  setText("dtcStatus", normalizedDtc(status.dtc));
  setText("firebaseUpdatedAt", firebaseUpdated ? `${fmtDate(firebaseUpdated)} · ${relativeTime(firebaseUpdated)}` : "--");
  setText("batteryLevel", batteryLevelValue == null ? "--" : `${Math.round(batteryLevelValue)}%`);
  setText("refreshStatus", /success/i.test(cleanValue(status.refresh_status)) ? "정상 완료" : (cleanValue(status.refresh_status) || "--"));
  setText("commaUpdatedAt", `${fmtDate(state.updated_at)} · ${relativeTime(state.updated_at)}`);
  setText("gpsSource", cleanValue(gps.source) || "--");
  setText("currentDraw", state.current_ma == null ? "--" : `${Math.round(state.current_ma)} mA`);
  setText("vehicleSpeedSource", cleanValue(raw.vehicleSpeedSource) || "--");

  updateOverviewPosition({ lat, lon, accuracy, onroad, updatedAt: state.updated_at, gps });
}

function updateOverviewPosition({ lat, lon, accuracy, onroad, updatedAt, gps }) {
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
    currentPosition = null;
    setText("currentAddress", "위치 데이터 없음");
    setText("currentCoords", "--");
    setText("gpsBadge", "GPS 없음");
    if (overviewMarker) {
      overviewMarker.remove();
      overviewMarker = null;
    }
    return;
  }

  currentPosition = [lat, lon];
  setText("currentAddress", onroad ? "주행 중인 차량 위치" : "최근 주차 위치");
  setText("currentCoords", fmtCoords(lat, lon, accuracy));
  setText("gpsBadge", gps.fresh === true ? "실시간 GPS" : "최근 GPS");

  if (!overviewMarker) {
    overviewMarker = L.marker(currentPosition, {
      icon: markerIcon(onroad),
      zIndexOffset: 1000,
    }).addTo(overviewMap);
    if (reduceMotion) {
      overviewMap.setView(currentPosition, 15, { animate: false });
    } else {
      overviewMap.setView(DEFAULT_CENTER, DEFAULT_ZOOM, { animate: false });
      setTimeout(() => {
        if (currentPosition) overviewMap.flyTo(currentPosition, 15, { duration: 1.35 });
      }, 420);
    }
  } else {
    overviewMarker.setLatLng(currentPosition);
    overviewMarker.setIcon(markerIcon(onroad));
  }
  overviewMarker.bindPopup(`${onroad ? "주행 중" : "주차됨"}<br>${fmtDate(updatedAt)}`);
}

function routePoints(route) {
  return (route || [])
    .map((point) => ({
      lat: finiteNumber(point.latitude),
      lon: finiteNumber(point.longitude),
      speed: routePointSpeed(point),
    }))
    .filter((point) => point.lat != null && point.lon != null);
}

function drawTripRoute(route) {
  tripRouteLayer.clearLayers();
  const points = routePoints(route);
  if (points.length < 2) return;

  for (let index = 1; index < points.length; index += 1) {
    const previous = points[index - 1];
    const next = points[index];
    L.polyline([[previous.lat, previous.lon], [next.lat, next.lon]], {
      color: speedColor(next.speed),
      weight: 5,
      opacity: 0.88,
      lineCap: "round",
    }).addTo(tripRouteLayer);
  }

  L.circleMarker([points[0].lat, points[0].lon], {
    radius: 6,
    color: "#ffffff",
    weight: 2,
    fillColor: "#248a3d",
    fillOpacity: 1,
  }).bindTooltip("출발").addTo(tripRouteLayer);
  L.circleMarker([points.at(-1).lat, points.at(-1).lon], {
    radius: 6,
    color: "#ffffff",
    weight: 2,
    fillColor: "#d70015",
    fillOpacity: 1,
  }).bindTooltip("도착").addTo(tripRouteLayer);

  const bounds = L.latLngBounds(points.map((point) => [point.lat, point.lon]));
  activeTripBounds = bounds;
  if (currentView === "trips") {
    tripMap.fitBounds(bounds, { padding: [38, 38], animate: false });
  }
}

function showCurrentPositionOnTripMap() {
  activeTripId = null;
  activeTripBounds = null;
  tripRouteLayer.clearLayers();
  for (const card of el("trips").querySelectorAll(".trip-card")) {
    card.classList.remove("active");
  }
  if (!currentPosition) {
    if (tripCurrentMarker) {
      tripCurrentMarker.remove();
      tripCurrentMarker = null;
    }
    tripMap.setView(DEFAULT_CENTER, DEFAULT_ZOOM);
    return;
  }
  if (!tripCurrentMarker) {
    tripCurrentMarker = L.marker(currentPosition, { icon: markerIcon(currentOnroad) }).addTo(tripMap);
  } else {
    tripCurrentMarker.setLatLng(currentPosition);
    tripCurrentMarker.setIcon(markerIcon(currentOnroad));
  }
  tripMap.setView(currentPosition, 15, { animate: false });
}

async function selectTrip(id) {
  activeTripId = id;
  if (tripCurrentMarker) {
    tripCurrentMarker.remove();
    tripCurrentMarker = null;
  }
  for (const card of el("trips").querySelectorAll(".trip-card")) {
    card.classList.toggle("active", card.dataset.id === id);
  }
  const trip = await api(`/api/trips/${encodeURIComponent(id)}`);
  drawTripRoute(trip.route || []);
}

function renderOverviewTrips(trips) {
  const container = el("overviewTrips");
  container.replaceChildren();

  if (!trips.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "저장된 주행 기록이 없습니다.";
    container.append(empty);
    return;
  }

  for (const [index, trip] of trips.slice(0, 2).entries()) {
    const button = document.createElement("button");
    button.className = "overview-trip";
    button.type = "button";
    button.style.animationDelay = `${index * 80}ms`;

    const date = document.createElement("span");
    date.textContent = fmtDate(trip.started_at, { year: undefined });
    const distance = document.createElement("b");
    distance.textContent = fmtDistance(trip.distance_m);
    const title = document.createElement("strong");
    title.textContent = index === 0 ? "최근 주행" : "이전 주행";
    const summary = document.createElement("small");
    summary.textContent = `${fmtDuration(trip.duration_s)} · 평균 ${fmtKph(trip.avg_speed_mps)} km/h`;

    button.append(date, distance, title, summary);
    button.addEventListener("click", () => {
      switchView("trips");
      selectTrip(trip.id).catch((error) => handleError(error, "경로를 불러오지 못했습니다."));
    });
    container.append(button);
  }
}

function renderTrips(trips) {
  currentTrips = trips;
  const container = el("trips");
  container.replaceChildren();
  setText("tripCount", `${trips.length}개 경로`);
  renderOverviewTrips(trips);

  if (!trips.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "저장된 주행 기록이 없습니다.";
    container.append(empty);
    return;
  }

  for (const [index, trip] of trips.slice(0, 40).entries()) {
    const button = document.createElement("button");
    button.className = "trip-card";
    button.type = "button";
    button.dataset.id = trip.id;
    button.classList.toggle("active", trip.id === activeTripId);
    button.style.animationDelay = `${Math.min(index * 30, 300)}ms`;

    const date = document.createElement("strong");
    date.textContent = fmtDate(trip.started_at, { year: undefined });
    const distance = document.createElement("span");
    distance.className = "distance";
    distance.textContent = fmtDistance(trip.distance_m);
    const period = document.createElement("p");
    period.textContent = `${fmtDate(trip.started_at, { year: undefined, month: undefined, day: undefined })} - ${fmtDate(trip.ended_at, { year: undefined, month: undefined, day: undefined })} · ${trip.route_point_count || 0}개 포인트`;
    const summary = document.createElement("small");
    summary.textContent = `${fmtDuration(trip.duration_s)} · 평균 ${fmtKph(trip.avg_speed_mps)} km/h · 최고 ${fmtKph(trip.max_speed_mps)} km/h`;
    button.append(date, distance, period, summary);
    button.addEventListener("click", () => {
      selectTrip(trip.id).catch((error) => handleError(error, "경로를 불러오지 못했습니다."));
    });
    container.append(button);
  }
}

function renderChart(trips) {
  const now = new Date();
  const dayMs = 24 * 60 * 60 * 1000;
  const days = [];
  for (let index = 30; index >= 0; index -= 1) {
    const date = new Date(now.getTime() - index * dayMs);
    days.push({ key: date.toISOString().slice(0, 10), km: 0 });
  }

  const byKey = new Map(days.map((day) => [day.key, day]));
  let totalKm = 0;
  let totalDuration = 0;
  let maxSpeed = null;

  for (const trip of trips) {
    const ended = new Date(trip.ended_at || trip.started_at || 0);
    if (Number.isNaN(ended.getTime()) || now - ended > 31 * dayMs) continue;
    const km = (Number(trip.distance_m) || 0) / 1000;
    totalKm += km;
    totalDuration += Number(trip.duration_s) || 0;
    const tripMax = finiteNumber(trip.max_speed_mps);
    if (tripMax != null) maxSpeed = Math.max(maxSpeed ?? tripMax, tripMax);
    const day = byKey.get(ended.toISOString().slice(0, 10));
    if (day) day.km += km;
  }

  const maxKm = Math.max(1, ...days.map((day) => day.km));
  const chart = el("monthChart");
  chart.replaceChildren();
  for (const [index, day] of days.entries()) {
    const bar = document.createElement("i");
    bar.style.height = `${Math.max(2, (day.km / maxKm) * 100)}%`;
    bar.style.animationDelay = `${Math.min(index * 12, 240)}ms`;
    bar.title = `${day.key} · ${day.km.toFixed(1)} km`;
    chart.append(bar);
  }

  const drivenDays = days.filter((day) => day.km > 0).length || 1;
  setText("monthTotal", `${totalKm.toFixed(totalKm >= 100 ? 0 : 1)} km`);
  setText("monthAvg", `${(totalKm / drivenDays).toFixed(1)} km`);
  setText("monthMaxSpeed", `${fmtKph(maxSpeed)} km/h`);
  setText("monthTime", fmtDuration(totalDuration));
  setText("chartMonth", now.toLocaleString("ko-KR", { year: "numeric", month: "long" }));
  setText("chartScale", `최대 ${Math.ceil(maxKm)} km`);
}

function clearSnapshotUrls() {
  for (const url of snapshotObjectUrls) URL.revokeObjectURL(url);
  snapshotObjectUrls = [];
}

async function loadSnapshotImage(image, key) {
  const response = await fetch(`/api/snapshot?key=${encodeURIComponent(key)}`, {
    headers: authHeaders(),
    cache: "no-store",
  });
  if (!response.ok) return;
  const url = URL.createObjectURL(await response.blob());
  snapshotObjectUrls.push(url);
  image.src = url;
}

function renderSnapshots() {
  clearSnapshotUrls();
  const container = el("snapshots");
  container.replaceChildren();
  const filtered = currentSnapshots.filter((snapshot) => (
    currentCameraFilter === "all" || snapshot.camera === currentCameraFilter
  ));
  setText("snapshotCount", `${filtered.length}장`);

  if (!filtered.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "선택한 카메라의 스냅샷이 없습니다.";
    container.append(empty);
    return;
  }

  for (const [index, snapshot] of filtered.slice(0, 12).entries()) {
    const figure = document.createElement("figure");
    figure.className = "snapshot-card";
    figure.style.animationDelay = `${Math.min(index * 55, 330)}ms`;
    const imageWrap = document.createElement("div");
    imageWrap.className = "snapshot-image";
    const image = document.createElement("img");
    image.alt = snapshot.camera === "driver" ? "실내 카메라 스냅샷" : "실외 카메라 스냅샷";
    image.loading = "lazy";
    imageWrap.append(image);

    const caption = document.createElement("figcaption");
    const labels = document.createElement("span");
    const title = document.createElement("strong");
    title.textContent = snapshot.camera === "driver" ? "실내 카메라" : "실외 카메라";
    const time = document.createElement("small");
    time.textContent = fmtDate(snapshot.captured_at);
    labels.append(title, time);
    const size = document.createElement("i");
    size.textContent = snapshot.size_bytes ? `${Math.round(snapshot.size_bytes / 1024)} KB` : "JPEG";
    caption.append(labels, size);
    figure.append(imageWrap, caption);
    container.append(figure);
    loadSnapshotImage(image, snapshot.kv_key).catch(console.error);
  }
}

const revealObserver = reduceMotion
  ? null
  : new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.add("visible");
      revealObserver.unobserve(entry.target);
    }
  }, { threshold: 0.12 });

function initializeReveals() {
  for (const item of document.querySelectorAll(".reveal:not([data-reveal-bound])")) {
    item.dataset.revealBound = "true";
    if (reduceMotion) item.classList.add("visible");
    else revealObserver.observe(item);
  }
}

function switchView(name) {
  currentView = name;
  window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
  for (const view of views) {
    const active = view.dataset.view === name;
    view.hidden = !active;
    view.classList.toggle("active", active);
  }
  for (const button of viewButtons) {
    const active = button.dataset.viewTarget === name;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  }
  if (name === "overview") {
    setTimeout(() => overviewMap.invalidateSize(), 0);
  } else if (name === "trips") {
    setTimeout(() => {
      tripMap.invalidateSize();
      if (activeTripBounds) {
        tripMap.fitBounds(activeTripBounds, { padding: [38, 38], animate: false });
      }
    }, 0);
  }
  requestAnimationFrame(initializeReveals);
}

function openTokenDialog(message = "") {
  tokenInput.value = token;
  tokenError.textContent = message;
  if (!tokenDialog.open) tokenDialog.showModal();
  setTimeout(() => tokenInput.focus(), 0);
}

function handleError(error, fallback = "데이터를 불러오지 못했습니다.") {
  console.error(error);
  const unauthorized = error?.status === 401;
  setConnection("error", unauthorized ? "인증 필요" : "연결 실패");
  if (unauthorized) openTokenDialog("View Token을 확인해주세요.");
  else tokenError.textContent = fallback;
}

async function refresh() {
  if (refreshInFlight) return;
  if (!token) {
    setConnection("error", "연결 필요");
    renderEmptyState();
    openTokenDialog();
    return;
  }

  refreshInFlight = true;
  refreshButton.classList.add("loading");
  setConnection("", "동기화 중");
  try {
    const [{ state, snapshots, vehicleStatus }, { trips }] = await Promise.all([
      api("/api/state"),
      api("/api/trips"),
    ]);
    renderState(state, vehicleData(vehicleStatus));
    currentSnapshots = snapshots || [];
    renderSnapshots();
    renderTrips(trips || []);
    renderChart(trips || []);
    setConnection("online", "Wayon + GMOne");

    if (!activeTripId && trips?.length) {
      await selectTrip(trips[0].id);
    }
  } catch (error) {
    handleError(error);
  } finally {
    refreshInFlight = false;
    refreshButton.classList.remove("loading");
  }
}

viewButtons.forEach((button) => {
  button.addEventListener("click", () => switchView(button.dataset.viewTarget));
});

document.querySelector(".brand").addEventListener("click", (event) => {
  event.preventDefault();
  switchView("overview");
});

cameraFilterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    currentCameraFilter = button.dataset.cameraFilter;
    cameraFilterButtons.forEach((item) => item.classList.toggle("active", item === button));
    renderSnapshots();
  });
});

refreshButton.addEventListener("click", () => refresh());
tokenButton.addEventListener("click", () => openTokenDialog());
closeTokenDialog.addEventListener("click", () => tokenDialog.close());
recenterButton.addEventListener("click", () => {
  if (currentPosition) overviewMap.setView(currentPosition, Math.max(overviewMap.getZoom(), 15), { animate: true });
});
clearRouteButton.addEventListener("click", showCurrentPositionOnTripMap);

tokenForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const nextToken = tokenInput.value.trim();
  if (!nextToken) {
    tokenError.textContent = "View Token을 입력해주세요.";
    return;
  }
  token = nextToken;
  localStorage.setItem("wayonViewToken", token);
  tokenError.textContent = "";
  tokenDialog.close();
  await refresh();
});

disconnectButton.addEventListener("click", () => {
  token = "";
  tokenInput.value = "";
  localStorage.removeItem("wayonViewToken");
  renderEmptyState();
  setConnection("error", "연결 필요");
  tokenError.textContent = "저장된 연결을 해제했습니다.";
});

renderEmptyState();
renderTrips([]);
renderChart([]);
renderSnapshots();
showCurrentPositionOnTripMap();
initializeReveals();
refresh();
setInterval(refresh, REFRESH_INTERVAL_MS);
