const el = (id) => document.getElementById(id);

const tokenForm = el("tokenForm");
const tokenInput = el("tokenInput");
const connectionStatus = el("connectionStatus");
const rangeValue = el("rangeValue");
const rangeUnit = el("rangeUnit");
const rangeSubtext = el("rangeSubtext");
const driveState = el("driveState");
const lastGpsTime = el("lastGpsTime");
const rangePercent = el("rangePercent");
const dailyBadge = el("dailyBadge");
const rangeBars = el("rangeBars");
const vehicleMeta = el("vehicleMeta");
const ignitionState = el("ignitionState");
const batteryInfo = el("batteryInfo");
const odometer = el("odometer");
const vehicleUpdatedAt = el("vehicleUpdatedAt");
const currentAddress = el("currentAddress");
const currentCoords = el("currentCoords");
const speed = el("speed");
const driveGlyph = el("driveGlyph");
const fuelLevel = el("fuelLevel");
const fuelUnit = el("fuelUnit");
const oilLife = el("oilLife");
const snapshotsEl = el("snapshots");
const snapshotStatus = el("snapshotStatus");
const tripStatus = el("tripStatus");
const tirePressure = el("tirePressure");
const dtcStatus = el("dtcStatus");
const monthTotal = el("monthTotal");
const chartMonth = el("chartMonth");
const monthChart = el("monthChart");
const chartMax = el("chartMax");
const monthAvg = el("monthAvg");
const monthMaxSpeed = el("monthMaxSpeed");
const monthTime = el("monthTime");
const tripsEl = el("trips");

const RANGE_BAR_COUNT = 82;
for (let i = 0; i < RANGE_BAR_COUNT; i += 1) {
  rangeBars.append(document.createElement("i"));
}

function tokenFromHash() {
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  return params.get("token") || "";
}

let token = tokenFromHash() || localStorage.getItem("wayonViewToken") || "";
if (token) {
  localStorage.setItem("wayonViewToken", token);
}
tokenInput.value = token;

const map = L.map("map", {
  zoomControl: true,
  attributionControl: true,
}).setView([36.35, 127.9], 7);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap",
  maxZoom: 19,
}).addTo(map);

let currentMarker = null;
let routeLayer = L.layerGroup().addTo(map);
let activeTripId = null;

function authHeaders() {
  return token ? { authorization: `Bearer ${token}` } : {};
}

function setConnection(kind, text) {
  connectionStatus.classList.toggle("online", kind === "online");
  connectionStatus.classList.toggle("error", kind === "error");
  connectionStatus.innerHTML = `<i></i> ${text}`;
}

function finiteNumber(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function fmtNumber(value, digits = 1) {
  const n = finiteNumber(value);
  return n == null ? "--" : n.toFixed(digits);
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

function fmtTimeOnly(value) {
  return fmtDate(value, { month: undefined, day: undefined });
}

function fmtMonth(value = new Date()) {
  return value.toLocaleString("en-US", { month: "short", year: "numeric" }).toUpperCase();
}

function fmtDuration(seconds) {
  const total = Math.max(0, Number(seconds) || 0);
  const hours = Math.floor(total / 3600);
  const minutes = Math.round((total % 3600) / 60);
  if (hours > 0) return `${hours}H ${minutes}M`;
  return `${minutes}M`;
}

function fmtDistance(meters) {
  const km = (Number(meters) || 0) / 1000;
  if (km >= 100) return `${Math.round(km)} km`;
  if (km >= 10) return `${km.toFixed(1)} km`;
  return `${km.toFixed(2)} km`;
}

function fmtKph(mps) {
  const n = finiteNumber(mps);
  return n == null ? "--" : String(Math.round(Math.max(0, n * 3.6)));
}

function fmtCoords(lat, lon, accuracy) {
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return "--";
  const suffix = Number.isFinite(accuracy) ? ` · ACC ${accuracy.toFixed(1)}M` : "";
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

function firstNumber(...values) {
  for (const value of values) {
    const candidate = typeof value === "string" ? value.replace(/,/g, "").replace(/[^\d.-]/g, "") : value;
    if (candidate === "" || candidate == null) continue;
    const n = finiteNumber(candidate);
    if (n != null) return n;
  }
  return null;
}

function vehicleData(vehicleStatus) {
  return vehicleStatus?.ok && vehicleStatus.data ? vehicleStatus.data : {};
}

function cleanValue(value) {
  const text = String(value ?? "").trim();
  return text && text !== "--" ? text : "";
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
  return liters == null ? null : Math.min(100, (liters / 82) * 100);
}

function tirePressureSummary(status) {
  const source = `${cleanValue(status.tire_pressure_all)} ${cleanValue(status.tire_pressure)}`;
  const matches = [...source.matchAll(/(\d+)\s*(kpa|psi)/gi)].slice(0, 4);
  if (!matches.length) return "--";
  const unit = matches[0][2].toUpperCase();
  return `${matches.map((match) => match[1]).join("/")} ${unit}`;
}

function rangeFields(raw, status) {
  const rangeKm = firstNumber(
    status.range,
    raw.rangeKm,
    raw.range_km,
    raw.vehicleRangeKm,
    raw.fuelRangeKm,
    raw.batteryRangeKm,
    raw.myChevrolet?.rangeKm,
    raw.myChevrolet?.range_km,
  );
  const percent = firstNumber(
    fuelPercent(status),
    raw.rangePercent,
    raw.range_percent,
    raw.batteryPercent,
    raw.battery_percent,
    raw.fuelPercent,
    raw.fuel_percent,
    raw.fuelLevelPercent,
    raw.fuel_level_percent,
    raw.myChevrolet?.batteryPercent,
    raw.myChevrolet?.fuelLevelPercent,
  );
  return { rangeKm, percent };
}

function updateRangeBars(percent) {
  const fillCount = percent == null ? 0 : Math.round((Math.max(0, Math.min(100, percent)) / 100) * RANGE_BAR_COUNT);
  const warnStart = Math.round(RANGE_BAR_COUNT * 0.82);
  [...rangeBars.children].forEach((bar, index) => {
    bar.className = "";
    if (index < fillCount) bar.classList.add("fill");
    if (index >= warnStart) bar.classList.add("warn");
  });
}

function markerIcon(onroad) {
  return L.divIcon({
    className: "",
    html: `<div class="car-marker${onroad ? " onroad" : ""}"></div>`,
    iconSize: [15, 15],
    iconAnchor: [7, 7],
  });
}

function speedColor(mps) {
  const kph = Math.max(0, Number(mps) * 3.6 || 0);
  if (kph < 45) return "#3ab97c";
  if (kph < 85) return "#d6c95a";
  return "#ff8a1f";
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
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

async function loadSnapshotImage(img, key) {
  const response = await fetch(`/api/snapshot?key=${encodeURIComponent(key)}`, {
    headers: authHeaders(),
    cache: "no-store",
  });
  if (!response.ok) return;
  const blob = await response.blob();
  img.src = URL.createObjectURL(blob);
}

function renderEmptyState() {
  driveState.textContent = "--";
  driveGlyph.textContent = "--";
  rangeValue.textContent = "--";
  rangeUnit.textContent = "km";
  rangeSubtext.textContent = "주행 가능 거리 데이터 없음";
  lastGpsTime.textContent = "GPS --";
  rangePercent.textContent = "--%";
  dailyBadge.innerHTML = "LIVE<br>--";
  ignitionState.textContent = "--";
  batteryInfo.textContent = "--";
  odometer.textContent = "--";
  vehicleUpdatedAt.textContent = "--";
  currentAddress.textContent = "위치 데이터 대기 중";
  currentCoords.textContent = "--";
  speed.textContent = "--";
  fuelLevel.textContent = "--";
  fuelUnit.textContent = " L";
  oilLife.textContent = "--";
  tirePressure.textContent = "--";
  dtcStatus.textContent = "--";
  updateRangeBars(null);
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
  const { rangeKm, percent } = rangeFields(raw, status);
  const lat = finiteNumber(state.latitude);
  const lon = finiteNumber(state.longitude);
  const accuracy = finiteNumber(state.gps_accuracy_m);
  const gpsTime = raw.gps?.timestampMillis ? new Date(Number(raw.gps.timestampMillis)).toISOString() : state.updated_at;
  const fuel = cleanValue(status.fuel);
  const fuelLitersValue = fuelLiters(status);
  const oil = firstNumber(status.oil);
  const vehicleBattery = firstNumber(status.battery);
  const batteryLevel = firstNumber(status.battery_level);
  const odometerValue = cleanValue(status.mileage);
  const vehicleLastUpdate = cleanValue(status.last_update);

  driveState.textContent = onroad ? "주행중" : "주차됨";
  driveGlyph.textContent = onroad ? (enabled ? "E" : "D") : "P";
  rangeValue.textContent = rangeKm == null ? "--" : String(Math.round(rangeKm));
  rangeUnit.textContent = "km";
  rangeSubtext.textContent = fuelLitersValue == null ? "Firebase fuel 데이터 없음" : `연료 ${Math.round(fuelLitersValue)}L / 82L`;
  rangePercent.textContent = percent == null ? "--%" : `${Math.round(percent)}%`;
  dailyBadge.innerHTML = percent == null ? "FUEL<br>--" : `FUEL<br>${Math.round(percent)}%`;
  lastGpsTime.textContent = `GPS ${fmtDate(gpsTime)}`;
  vehicleMeta.textContent = raw.dongleId ? `Wayon linked · ${raw.dongleId}` : "Wayon linked";
  ignitionState.textContent = ignition ? "ON" : "OFF";
  batteryInfo.textContent = batteryLevel == null && vehicleBattery == null
    ? (state.voltage_v == null ? "--" : `${fmtNumber(state.voltage_v, 2)} V`)
    : `${batteryLevel == null ? "--" : `${Math.round(batteryLevel)}%`} · ${vehicleBattery == null ? fmtNumber(state.voltage_v, 2) : fmtNumber(vehicleBattery, 1)} V`;
  odometer.textContent = odometerValue ? `${odometerValue} km` : "--";
  vehicleUpdatedAt.textContent = vehicleLastUpdate || fmtDate(state.updated_at);
  speed.textContent = fmtKph(state.speed_mps);
  fuelLevel.textContent = fuelLitersValue == null ? (fuel || "--") : String(Math.round(fuelLitersValue));
  fuelUnit.textContent = fuel.includes("%") ? " %" : " L";
  oilLife.textContent = oil == null ? "--" : String(Math.round(oil));
  tirePressure.textContent = tirePressureSummary(status);
  dtcStatus.textContent = cleanValue(status.dtc) || "--";
  updateRangeBars(percent);

  if (Number.isFinite(lat) && Number.isFinite(lon)) {
    const position = [lat, lon];
    currentAddress.textContent = onroad ? "차량 위치 실시간 반영 중" : "마지막 차량 위치";
    currentCoords.textContent = fmtCoords(lat, lon, accuracy);

    if (!currentMarker) {
      currentMarker = L.marker(position, { icon: markerIcon(onroad), zIndexOffset: 1000 }).addTo(map);
    } else {
      currentMarker.setLatLng(position);
      currentMarker.setIcon(markerIcon(onroad));
    }
    currentMarker.bindPopup(`${onroad ? "주행중" : "주차됨"}<br>${fmtDate(state.updated_at)}`);

    if (!activeTripId) {
      map.setView(position, Math.max(map.getZoom(), 13), { animate: true });
    }
  } else if (currentMarker) {
    currentMarker.remove();
    currentMarker = null;
    currentAddress.textContent = "위치 데이터 없음";
    currentCoords.textContent = "--";
  }
}

function renderSnapshots(snapshots) {
  const latest = [...snapshots].slice(0, 2);
  snapshotsEl.innerHTML = "";
  snapshotStatus.textContent = snapshots.length ? `${snapshots.length} FRAMES` : "NO FRAME";

  if (!latest.length) {
    for (const label of ["실외", "실내"]) {
      const empty = document.createElement("div");
      empty.className = "snapshot empty";
      empty.textContent = `${label} · 데이터 없음`;
      snapshotsEl.append(empty);
    }
    return;
  }

  for (const snapshot of latest) {
    const figure = document.createElement("figure");
    figure.className = "snapshot";
    const img = document.createElement("img");
    const caption = document.createElement("figcaption");
    const camera = snapshot.camera === "driver" ? "실내" : "실외";
    caption.textContent = `${camera} · ${fmtDate(snapshot.captured_at)}`;
    figure.append(img, caption);
    snapshotsEl.append(figure);
    loadSnapshotImage(img, snapshot.kv_key);
  }
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

function drawRoute(route) {
  routeLayer.clearLayers();
  const points = routePoints(route);
  if (points.length < 2) {
    return;
  }

  for (let i = 1; i < points.length; i += 1) {
    const prev = points[i - 1];
    const next = points[i];
    L.polyline([[prev.lat, prev.lon], [next.lat, next.lon]], {
      color: speedColor(next.speed),
      weight: 6,
      opacity: 0.92,
      lineCap: "round",
    }).addTo(routeLayer);
  }
  const bounds = L.latLngBounds(points.map((point) => [point.lat, point.lon]));
  map.fitBounds(bounds, { padding: [42, 42], animate: true });
}

async function selectTrip(id) {
  activeTripId = id;
  for (const button of tripsEl.querySelectorAll(".trip-card")) {
    button.classList.toggle("active", button.dataset.id === id);
  }
  const trip = await api(`/api/trips/${encodeURIComponent(id)}`);
  drawRoute(trip.route || []);
}

function renderTrips(trips) {
  tripsEl.innerHTML = "";
  tripStatus.textContent = trips.length ? `${trips.length} ROUTES` : "NO ROUTE";

  if (!trips.length) {
    const empty = document.createElement("div");
    empty.className = "empty-message";
    empty.textContent = "저장된 주행 기록이 없습니다.";
    tripsEl.append(empty);
    return;
  }

  for (const trip of trips.slice(0, 8)) {
    const button = document.createElement("button");
    button.className = "trip-card";
    button.type = "button";
    button.dataset.id = trip.id;
    button.classList.toggle("active", trip.id === activeTripId);
    button.innerHTML = `
      <strong>${fmtDate(trip.started_at, { year: undefined })}</strong>
      <p>${fmtTimeOnly(trip.started_at)} - ${fmtTimeOnly(trip.ended_at)}<br>${trip.route_point_count || 0} route points</p>
      <div class="km">${fmtDistance(trip.distance_m)}</div>
      <small>${fmtDuration(trip.duration_s)} · AVG ${fmtKph(trip.avg_speed_mps)} · MAX ${fmtKph(trip.max_speed_mps)}</small>
    `;
    button.addEventListener("click", () => selectTrip(trip.id).catch(console.error));
    tripsEl.append(button);
  }
}

function renderChart(trips) {
  const now = new Date();
  const dayMs = 24 * 60 * 60 * 1000;
  const days = [];
  for (let i = 30; i >= 0; i -= 1) {
    const date = new Date(now.getTime() - i * dayMs);
    const key = date.toISOString().slice(0, 10);
    days.push({ key, km: 0 });
  }
  const byKey = new Map(days.map((day) => [day.key, day]));
  let totalKm = 0;
  let totalDuration = 0;
  let maxSpeed = null;

  for (const trip of trips) {
    const ended = new Date(trip.ended_at || trip.started_at || 0);
    if (Number.isNaN(ended.getTime())) continue;
    if (now - ended > 31 * dayMs) continue;

    const km = (Number(trip.distance_m) || 0) / 1000;
    totalKm += km;
    totalDuration += Number(trip.duration_s) || 0;
    const tripMax = finiteNumber(trip.max_speed_mps);
    if (tripMax != null) maxSpeed = Math.max(maxSpeed ?? tripMax, tripMax);

    const key = ended.toISOString().slice(0, 10);
    const day = byKey.get(key);
    if (day) day.km += km;
  }

  const maxKm = Math.max(1, ...days.map((day) => day.km));
  monthChart.querySelectorAll("i").forEach((node) => node.remove());
  for (const day of days) {
    const bar = document.createElement("i");
    bar.style.height = `${Math.max(3, (day.km / maxKm) * 100)}%`;
    bar.title = `${day.key}: ${day.km.toFixed(1)} km`;
    monthChart.insertBefore(bar, monthChart.querySelector(".axis"));
  }

  monthTotal.textContent = `${totalKm.toFixed(totalKm >= 100 ? 0 : 1)} km`;
  chartMonth.textContent = fmtMonth(now);
  chartMax.textContent = String(Math.ceil(maxKm));
  const drivenDays = days.filter((day) => day.km > 0).length || 1;
  monthAvg.textContent = `${(totalKm / drivenDays).toFixed(1)} km`;
  monthMaxSpeed.textContent = `${fmtKph(maxSpeed)} km/h`;
  monthTime.textContent = fmtDuration(totalDuration);
}

async function refresh() {
  if (!token) {
    setConnection("error", "VIEW TOKEN 필요");
    renderEmptyState();
    renderSnapshots([]);
    renderTrips([]);
    renderChart([]);
    return;
  }

  const [{ state, snapshots, vehicleStatus }, { trips }] = await Promise.all([
    api("/api/state"),
    api("/api/trips"),
  ]);
  const status = vehicleData(vehicleStatus);

  renderState(state, status);
  renderSnapshots(snapshots || []);
  renderTrips(trips || []);
  renderChart(trips || []);
  setConnection("online", `WAYON + FIREBASE SYNC · ${fmtDate(new Date())}`);

  if (!activeTripId && trips?.length) {
    await selectTrip(trips[0].id);
  }
}

tokenForm.addEventListener("submit", (event) => {
  event.preventDefault();
  token = tokenInput.value.trim();
  localStorage.setItem("wayonViewToken", token);
  const hash = new URLSearchParams({ token }).toString();
  window.history.replaceState(null, "", `#${hash}`);
  refresh().catch((error) => {
    console.error(error);
    setConnection("error", "연결 실패");
    alert("연결에 실패했습니다. 토큰과 배포 상태를 확인해주세요.");
  });
});

refresh().catch((error) => {
  console.error(error);
  setConnection("error", `연결 실패 · ${error.message || error}`);
});

setInterval(() => {
  refresh().catch((error) => {
    console.error(error);
    setConnection("error", `연결 실패 · ${error.message || error}`);
  });
}, 30000);
