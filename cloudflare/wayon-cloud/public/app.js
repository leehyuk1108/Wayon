const tokenForm = document.getElementById("tokenForm");
const tokenInput = document.getElementById("tokenInput");
const driveState = document.getElementById("driveState");
const voltage = document.getElementById("voltage");
const fan = document.getElementById("fan");
const updatedAt = document.getElementById("updatedAt");
const snapshotsEl = document.getElementById("snapshots");
const tripsEl = document.getElementById("trips");
const snapshotStatus = document.getElementById("snapshotStatus");
const tripStatus = document.getElementById("tripStatus");

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
}).setView([36.35, 127.9], 7);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap",
  maxZoom: 19,
}).addTo(map);

let currentMarker = null;
let routeLayer = null;
let activeTripId = null;

function authHeaders() {
  return token ? { authorization: `Bearer ${token}` } : {};
}

function fmtNumber(value, digits = 1) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(digits) : "-";
}

function fmtDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
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
  return `${km.toFixed(km >= 10 ? 1 : 2)}km`;
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

function renderState(state) {
  if (!state) {
    driveState.textContent = "대기 중";
    voltage.textContent = "-";
    fan.textContent = "-";
    updatedAt.textContent = "-";
    return;
  }

  driveState.textContent = state.onroad ? "주행 중" : "주차 중";
  voltage.textContent = state.voltage_v ? `${fmtNumber(state.voltage_v, 2)}V` : "-";
  fan.textContent = state.fan_percent == null ? "-" : `${state.fan_percent}%`;
  updatedAt.textContent = fmtDate(state.updated_at);

  if (state.latitude && state.longitude) {
    const position = [state.latitude, state.longitude];
    if (!currentMarker) {
      currentMarker = L.marker(position).addTo(map);
    } else {
      currentMarker.setLatLng(position);
    }
    currentMarker.bindPopup(`현재 위치<br>${fmtDate(state.updated_at)}`);
    map.setView(position, Math.max(map.getZoom(), 13));
  }
}

function renderSnapshots(snapshots) {
  snapshotsEl.innerHTML = "";
  snapshotStatus.textContent = snapshots.length ? `${snapshots.length}개` : "없음";

  for (const snapshot of snapshots) {
    const figure = document.createElement("figure");
    figure.className = "snapshot";
    const img = document.createElement("img");
    const caption = document.createElement("figcaption");
    caption.textContent = `${snapshot.camera === "driver" ? "운전자" : "전방 광각"} · ${fmtDate(snapshot.captured_at)}`;
    figure.append(img, caption);
    snapshotsEl.append(figure);
    loadSnapshotImage(img, snapshot.kv_key);
  }
}

function drawRoute(route) {
  if (routeLayer) {
    routeLayer.remove();
    routeLayer = null;
  }

  const points = route
    .map((point) => [point.latitude, point.longitude])
    .filter(([lat, lon]) => Number.isFinite(lat) && Number.isFinite(lon));
  if (!points.length) return;

  routeLayer = L.polyline(points, {
    color: "#27c184",
    weight: 5,
    opacity: 0.9,
  }).addTo(map);
  map.fitBounds(routeLayer.getBounds(), { padding: [28, 28] });
}

async function selectTrip(id) {
  activeTripId = id;
  for (const button of tripsEl.querySelectorAll(".trip")) {
    button.classList.toggle("active", button.dataset.id === id);
  }
  const trip = await api(`/api/trips/${encodeURIComponent(id)}`);
  drawRoute(trip.route || []);
}

function renderTrips(trips) {
  tripsEl.innerHTML = "";
  tripStatus.textContent = trips.length ? `${trips.length}개` : "없음";

  for (const trip of trips) {
    const button = document.createElement("button");
    button.className = "trip";
    button.type = "button";
    button.dataset.id = trip.id;
    button.innerHTML = `
      <strong>${fmtDate(trip.started_at)} 출발</strong>
      <span>${fmtDistance(trip.distance_m)} · ${fmtDuration(trip.duration_s)} · ${trip.route_point_count} points</span>
    `;
    button.addEventListener("click", () => selectTrip(trip.id));
    tripsEl.append(button);
  }
}

async function refresh() {
  if (!token) return;

  const [{ state, snapshots }, { trips }] = await Promise.all([
    api("/api/state"),
    api("/api/trips"),
  ]);
  renderState(state);
  renderSnapshots(snapshots || []);
  renderTrips(trips || []);

  if (!activeTripId && trips && trips.length) {
    await selectTrip(trips[0].id);
  }
}

tokenForm.addEventListener("submit", (event) => {
  event.preventDefault();
  token = tokenInput.value.trim();
  localStorage.setItem("wayonViewToken", token);
  refresh().catch((error) => {
    console.error(error);
    alert("연결에 실패했습니다. 토큰과 배포 상태를 확인해주세요.");
  });
});

refresh().catch(console.error);
setInterval(() => refresh().catch(console.error), 30000);
