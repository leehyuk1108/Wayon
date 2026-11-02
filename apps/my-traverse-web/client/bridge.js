/* Browser adapter for the unchanged My Traverse Next Android assets. */
(function (root) {
  "use strict";

  const API = "/api/wayon/";
  const POLL_MS = 15000;
  const MAX_SNAPSHOT_AGE = 7 * 86400000;
  const COMMANDS = new Set([
    "VEHICLE_START", "VEHICLE_STOP", "DOOR_LOCK", "DOOR_UNLOCK", "DRIVER_DOOR_UNLOCK",
    "TRUNK_OPEN", "TRUNK_CLOSE", "PANIC", "MAIN_LIGHT_OFF", "MAIN_LIGHT_ON",
    "WINDOW_OPEN", "WINDOW_CLOSE", "SUNROOF_OPEN", "SUNROOF_CLOSE", "SUNROOF_TILT",
  ]);
  let generation = 0;
  let active = false;
  let session = null;
  let account = null;
  let feed = null;
  let vehicle = null;
  let history = [];
  let fullHistory = false;
  let feedJob = null;
  let tripsJob = null;
  let accountBusy = false;
  let commandBusy = false;
  let lastCommandAt = -Infinity;
  let refreshBusy = false;
  let liveActive = false;
  let liveRequest = 0;
  let pollTimer = null;
  const timers = new Set();
  const requests = new Set();

  const object = value => value && typeof value === "object" && !Array.isArray(value) ? value : null;
  const clone = value => JSON.parse(JSON.stringify(value));
  const text = value => (typeof value === "string" || typeof value === "number")
    && String(value).trim() !== "" && value !== "null" ? String(value) : null;
  function number(value) {
    if (typeof value !== "number" && (typeof value !== "string" || !/^[+-]?\d+(?:\.\d+)?$/.test(value.trim()))) return null;
    const result = Number(value);
    return Number.isFinite(result) && Math.abs(result) <= Number.MAX_SAFE_INTEGER ? result : null;
  }
  function bounded(value, min, max) {
    const result = number(value);
    return result !== null && result >= min && result <= max ? result : null;
  }
  function numericText(value, min, max) {
    return bounded(value, min, max) === null ? "--" : String(value).trim();
  }
  function integer(value, max = Number.MAX_SAFE_INTEGER) {
    const result = bounded(value, 0, max);
    return Number.isInteger(result) ? result : null;
  }
  function boolean(value) {
    if (typeof value === "boolean") return value;
    if (typeof value === "number" && Number.isFinite(value)) return Math.trunc(value) !== 0;
    if (typeof value === "string" && /^(true|1)$/i.test(value)) return true;
    if (typeof value === "string" && /^(false|0)$/i.test(value)) return false;
    return null;
  }
  function jsonObject(value) {
    try { return object(typeof value === "string" ? JSON.parse(value) : value); } catch (_) { return null; }
  }
  function epoch(value) {
    if (!text(value)) return null;
    const source = String(value);
    const iso = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(source)
      ? source.replace(" ", "T") + "+09:00" : source;
    // Never interpret a timezone-less timestamp in the phone's local timezone.
    const parts = iso.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/);
    if (!parts || +parts[2] < 1 || +parts[2] > 12 || +parts[3] < 1
      || +parts[3] > new Date(Date.UTC(+parts[1], +parts[2], 0)).getUTCDate()
      || +parts[4] > 23 || +parts[5] > 59 || +parts[6] > 59) return null;
    const result = Date.parse(iso);
    return Number.isFinite(result) ? result : null;
  }
  function kst(time, date = false) {
    if (integer(time, 253402268399999) === null) return date ? "----.--.--" : "--:--";
    const iso = new Date(time + 9 * 3600000).toISOString();
    return date ? iso.slice(0, 10) : iso.slice(11, 16);
  }
  function timestamp(value) {
    const time = epoch(value);
    return time === null ? null : new Date(time).toISOString();
  }
  function emit(name, ...args) {
    if (typeof root[name] === "function") return root[name](...args);
  }
  const notice = (message, type = "info") => emit("showStatus", message, type, 4000);
  const allowed = name => active && session?.authenticated === true && !!session.csrfToken
    && session.capabilities?.[name] === true && (name !== "commands"
      || (account?.loggedIn === true && !accountBusy && session.capabilities.supportedCommands.length > 0));
  const current = id => active && id === generation;
  function later(fn, delay) {
    const id = root.setTimeout(() => { timers.delete(id); return fn(); }, delay);
    timers.add(id);
    return id;
  }
  function cancelTimer(id) { root.clearTimeout(id); timers.delete(id); }
  function aborted() { const error = new Error("Request superseded"); error.name = "AbortError"; return error; }

  async function request(path, method = "GET", body, id = generation) {
    if (!current(id)) throw aborted();
    if (method !== "GET" && !session?.csrfToken) throw new Error("Session verification is required.");
    const controller = new AbortController();
    requests.add(controller);
    const timeout = later(() => controller.abort(), method === "GET" ? 20000 : 90000);
    try {
      const headers = { Accept: "application/json" };
      if (method !== "GET") headers["X-CSRF-Token"] = session.csrfToken;
      if (body !== undefined) headers["Content-Type"] = "application/json";
      const response = await root.fetch(path, {
        method, credentials: "same-origin", cache: "no-store", headers,
        signal: controller.signal, ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
      if (!current(id)) throw aborted();
      if (response.status === 401) {
        stop();
        root.dispatchEvent(new CustomEvent("traverseweb:sessionlost"));
        throw aborted();
      }
      if (!response.ok) throw new Error(`Request failed (HTTP ${response.status}).`);
      const payload = response.status === 204 ? {} : await response.json();
      if (!current(id)) throw aborted();
      if (!object(payload)) throw new Error("Invalid server response.");
      return payload;
    } finally {
      cancelTimer(timeout);
      requests.delete(controller);
    }
  }

  // Match WayonCloudFeedParser's source precedence, enrichment and fuel units.
  function parseVehicle(status) {
    if (!object(status) || boolean(status.ok) !== true) return null;
    const sources = object(status.sources);
    const firebase = object(sources?.firebase);
    const gmone = object(sources?.gmone) || (!sources ? status : null);
    const firebaseData = object(firebase?.data);
    const gmoneData = object(gmone?.data);
    const sourceTime = source => epoch(source?.data?.last_update) ?? epoch(source?.updatedAt);
    const firebaseTime = sourceTime(firebase);
    const gmoneTime = sourceTime(gmone);
    const preferFirebase = firebaseData && firebaseTime !== null && (gmoneTime === null || firebaseTime > gmoneTime);
    const sourceData = preferFirebase ? { ...gmoneData, ...firebaseData } : object(status.data);
    if (!sourceData || !Object.keys(sourceData).length) return null;
    const data = clone(sourceData);
    const source = preferFirebase ? text(firebaseData.source) || "firebase" : text(status.source);
    const updatedAt = preferFirebase ? timestamp(firebaseData.last_update) || timestamp(firebase.updatedAt) : timestamp(status.updatedAt);
    const time = epoch(data.last_update) ?? epoch(updatedAt);
    if (time === null || Date.now() - time > MAX_SNAPSHOT_AGE || time > Date.now() + 120000) return null;
    const stale = preferFirebase ? false : boolean(status.stale) === true;
    const details = clone(object(data.gmone_details) || object(gmoneData?.gmone_details) || {});
    const fuel = clone(object(details.fuel) || {});
    const positive = value => number(value) > 0 ? number(value) : null;
    const percent = value => number(value) !== null && number(value) >= 0 && number(value) <= 100 ? number(value) : null;
    const capacity = positive(details.rawStatus?.fCap) ?? positive(fuel.capacityLiters);
    const level = percent(details.rawStatus?.fLvl) ?? percent(fuel.levelPercent);
    if (capacity !== null && level !== null) {
      const liters = capacity * level / 100;
      data.fuel = liters.toFixed(1);
      details.fuel = { ...fuel, capacityLiters: capacity, levelPercent: level, levelLiters: liters };
    } else if (capacity !== null) {
      if (number(data.fuel) > capacity) data.fuel = "--";
      if (number(fuel.levelLiters) > capacity) { delete fuel.levelLiters; details.fuel = fuel; }
    }
    if (!Object.hasOwn(details, "module") && object(gmone?.module) && Object.keys(gmone.module).length) details.module = clone(gmone.module);
    if (object(gmone?.health) && Object.keys(gmone.health).length) details.diagnostics = { ...details.diagnostics, ...clone(gmone.health) };
    if (object(gmone?.diagnostic) && Object.keys(gmone.diagnostic).length) details.refresh = { ...details.refresh, collector: clone(gmone.diagnostic) };
    if (Object.keys(details).length) {
      details.meta = { source, updatedAt: updatedAt || timestamp(data.last_update), collectedAt: timestamp(gmone?.collectedAt), stale, cached: true };
      data.gmone_details = details;
    }
    return { data, source, updatedAt: updatedAt || timestamp(data.last_update), stale, time };
  }
  function tire(value) {
    if (typeof value !== "string" || value.length > 512 || /[^0-9A-Za-z\uac00-\ud7a3\s.,:;/_-]/.test(value)) return "--";
    let found = false, invalid = false;
    const result = value.replace(/(-?\d+(?:\.\d+)?)\s*(kpa|psi)\b/gi, (_, raw, unit) => {
      found = true;
      unit = unit.toLowerCase();
      let pressure = bounded(raw, 0, unit === "psi" ? 300 : 2000);
      if (pressure === null) { invalid = true; return "--"; }
      if (unit === "kpa" && pressure > 0 && pressure < 100) pressure *= 4;
      return `${Number(pressure.toFixed(1))} ${unit}`;
    });
    return found && !invalid ? result : "--";
  }
  function renderVehicle() {
    if (!vehicle || Date.now() - vehicle.time > MAX_SNAPSHOT_AGE) {
      vehicle = null;
      emit("setVehicleDataState", "unavailable", "", false);
      emit("updateGmoneDetails", null);
      return;
    }
    const data = vehicle.data;
    // These arguments reach innerHTML in the original renderer. Only validated
    // numeric strings and reconstructed timestamps/pressure text may cross it.
    const mileage = numericText(data.mileage, 0, 1e9);
    if (mileage === "--") {
      const element = root.document.getElementById?.("val-mileage");
      if (element) element.textContent = "--";
    }
    emit("setVehicleDataState", "cached", vehicle.updatedAt, false);
    emit("updateCarStatus", numericText(data.range, 0, 1e7), numericText(data.battery, 0, 1000),
      numericText(data.battery_level, 0, 100), mileage, numericText(data.fuel, 0, 100000),
      timestamp(data.last_update) || vehicle.updatedAt || "", numericText(data.oil, 0, 100),
      tire(data.tire_pressure), tire(text(data.tire_pressure_all) || data.tire_pressure));
    emit("updateGmoneDetails", object(data.gmone_details) ? JSON.stringify(data.gmone_details) : null);
  }
  const coordinate = (value, limit) => number(value) !== null && Math.abs(number(value)) <= limit ? number(value) : null;
  const locationText = (lat, lon) => lat !== null && lon !== null ? `${lat.toFixed(5)}, ${lon.toFixed(5)}` : "\uc54c \uc218 \uc5c6\uc74c";
  const speed = value => bounded(value, 0, 1000) === null ? "-- km/h" : `${Math.round(number(value) * 3.6)} km/h`;
  function parseTrips(trips) {
    return (Array.isArray(trips) ? trips : []).filter(object).map(trip => {
      let route = trip.route;
      try { if (typeof route === "string") route = JSON.parse(route); } catch (_) { route = []; }
      if (!Array.isArray(route)) route = [];
      route = route.filter(object).map(point => {
        const latitude = coordinate(point.latitude ?? point.lat, 90);
        const longitude = coordinate(point.longitude ?? point.lon ?? point.lng, 180);
        // The original route reader uses Number(value): omit unknown coordinates
        // so they cannot become Number(null) === 0 on the map.
        return { ...(latitude === null ? {} : { latitude }), ...(longitude === null ? {} : { longitude }),
          speedMps: bounded(point.speedMps ?? point.speed_mps ?? point.speed, 0, 1000), time: timestamp(point.time) };
      });
      const duration = integer(trip.duration_s, 366 * 86400);
      const distance = bounded(trip.distance_m, 0, 1e9);
      const routeSpeeds = route.map(point => number(point?.speedMps)).filter(value => value !== null);
      const startLatitude = coordinate(trip.start_lat, 90), startLongitude = coordinate(trip.start_lon, 180);
      const endLatitude = coordinate(trip.end_lat, 90), endLongitude = coordinate(trip.end_lon, 180);
      return {
        id: text(trip.id), date: kst(epoch(trip.started_at), true), time: kst(epoch(trip.started_at)), endedAt: timestamp(trip.ended_at),
        distance: distance === null ? "-- km" : `${(distance / 1000).toFixed(2)} km`,
        duration: duration === null ? "--:--:--" : [Math.floor(duration / 3600), Math.floor(duration / 60) % 60, duration % 60].map(n => String(n).padStart(2, "0")).join(":"),
        avgSpeed: speed(bounded(trip.avg_speed_mps, 0, 1000) ?? (duration > 0 && distance !== null ? distance / duration : null)),
        topSpeed: speed(bounded(trip.max_speed_mps, 0, 1000) ?? (routeSpeeds.length ? routeSpeeds.reduce((a, b) => Math.max(a, b)) : null)),
        startLatitude, startLongitude, endLatitude, endLongitude,
        startAddress: text(trip.start_address) || locationText(startLatitude, startLongitude),
        endAddress: text(trip.end_address) || locationText(endLatitude, endLongitude),
        route, routePointCount: integer(trip.route_point_count, 1e8) ?? route.length,
        analysis: object(trip.analysis) || {}, health: object(trip.health) || {},
        startedAt: timestamp(trip.started_at),
      };
    }).sort((a, b) => (epoch(b.startedAt) || 0) - (epoch(a.startedAt) || 0));
  }
  function cloudState() {
    const state = object(feed?.state);
    if (!state) return null;
    const raw = jsonObject(state.raw_json) || {};
    const gps = object(raw.gps) || {};
    const op = object(raw.openpilot) || {};
    const lock = object(feed.vehicleLock) || {};
    return {
      updatedAt: timestamp(state.updated_at), gpsUpdatedAtEpochMs: epoch(gps.updatedAt) ?? integer(gps.timestampMillis, 253402268399999),
      onroad: boolean(state.onroad), ignition: boolean(state.ignition) ?? boolean(raw.ignition),
      openpilotEnabled: boolean(state.enabled) ?? boolean(op.enabled), openpilotActive: boolean(op.active),
      openpilotEngageable: boolean(op.engageable), openpilotState: text(op.state),
      thermalStatus: text(state.thermal_status) || text(raw.thermalStatus), gpsFresh: boolean(gps.fresh),
      voltageV: bounded(state.voltage_v, 0, 1000), vehicleInput: object(raw.vehicleInput), deviceInput: object(raw.deviceInput),
      latitude: coordinate(state.latitude, 90), longitude: coordinate(state.longitude, 180),
      speedMps: bounded(state.speed_mps, 0, 1000), speedKph: bounded(state.speed_mps, 0, 1000) === null ? null : number(state.speed_mps) * 3.6,
      doorLocked: boolean(lock.locked), doorLockUpdatedAt: timestamp(lock.occurredAt),
    };
  }
  function renderCloud() {
    const state = cloudState();
    if (!state || state.onroad === null || epoch(state.updatedAt) === null) {
      emit("markWayonCloudUnavailable", "Vehicle telemetry is unavailable.");
      return;
    }
    const address = text(feed.state.address) || locationText(state.latitude, state.longitude);
    const gpsTime = state.gpsUpdatedAtEpochMs === null ? "GPS \uc2dc\uac04 \uc5c6\uc74c" : kst(state.gpsUpdatedAtEpochMs);
    const tracking = state.onroad && state.ignition !== false && state.gpsFresh !== false;
    emit("updateWayonCloudState", state.voltageV === null ? "--" : state.voltageV.toFixed(1), gpsTime,
      tracking ? "ONROAD" : "OFFROAD", speed(state.speedMps), state.latitude, state.longitude, address, state.gpsUpdatedAtEpochMs);
    emit("updateWayonLiveState", JSON.stringify(state));
    const latest = history[0];
    emit("updateSavedLocation", address, gpsTime, latest?.distance || "-- km", latest?.duration || "--:--:--",
      latest?.avgSpeed || "-- km/h", latest?.topSpeed || "-- km/h");
  }
  function renderAccount() {
    emit("updateGmoneAccountState", account?.loggedIn === true, account?.email || "",
      account?.message || (account?.loggedIn ? "Account connected" : "Account login required"), accountBusy);
    emit("updateVehicleCommandReady", allowed("commands") && !accountBusy);
  }
  function render() {
    if (!active) return;
    renderVehicle();
    renderCloud();
    // Gallery remains usable even when the separate telemetry portion is missing.
    emit("updateWayonCloudSnapshots", JSON.stringify(Array.isArray(feed?.snapshots) ? feed.snapshots : []));
    emit("onWayonCloudDataUpdated");
  }
  function schedulePoll() {
    cancelTimer(pollTimer);
    pollTimer = null;
    if (active && !liveActive && !root.document.hidden) pollTimer = later(() => { pollTimer = null; refreshFeed(); }, POLL_MS);
  }
  function refreshFeed() {
    if (!active || root.document.hidden) return Promise.resolve(false);
    if (feedJob) return feedJob;
    const id = generation;
    const job = (async () => {
      try {
        const next = await request(API + "json", "GET", undefined, id);
        const nextVehicle = parseVehicle(next.vehicleStatus);
        if (!nextVehicle || !vehicle || nextVehicle.time + 1000 >= vehicle.time) vehicle = nextVehicle;
        feed = next;
        if (!fullHistory) history = parseTrips(next.trips);
        render();
        return true;
      } catch (error) {
        if (current(id)) {
          feed = null;
          vehicle = null;
          if (!fullHistory) history = [];
          render();
          notice(error.name === "AbortError" ? "Vehicle data request timed out." : error.message, "danger");
        }
        return false;
      } finally {
        if (current(id)) { feedJob = null; schedulePoll(); }
      }
    })();
    feedJob = job;
    return job;
  }
  function refreshTrips() {
    if (!active) return Promise.resolve(false);
    if (tripsJob) return tripsJob;
    const id = generation;
    tripsJob = (async () => {
      try {
        const payload = await request(API + "trips?limit=1000", "GET", undefined, id);
        if (!Array.isArray(payload.trips)) throw new Error("Trip history is unavailable.");
        history = parseTrips(payload.trips);
        fullHistory = true;
        return true;
      } catch (error) { if (current(id)) notice(error.message, "danger"); return false; }
      finally { if (current(id)) { tripsJob = null; emit("onWayonCloudHistoryUpdated"); } }
    })();
    return tripsJob;
  }
  async function refreshVehicle() {
    if (!active) return false;
    if (refreshBusy || commandBusy) { notice("A vehicle request is already in progress."); return false; }
    const id = generation;
    refreshBusy = true;
    try {
      const result = await request(API + "gmone/refresh", "POST", {}, id);
      if (result.ok === false) throw new Error("Vehicle refresh was not accepted.");
      const requestedAt = epoch(result.requestedAt);
      if (requestedAt === null) throw new Error("Refresh acknowledgement is missing its timestamp.");
      notice("Vehicle refresh requested; waiting for the vehicle.");
      const deadline = Date.now() + 90000;
      const poll = async () => {
        if (!current(id)) return;
        try {
          const status = await request(API + "gmone/refresh", "GET", undefined, id);
          if (status.pending === false && (epoch(status.completedAt) ?? -Infinity) >= requestedAt) {
            refreshBusy = false;
            await refreshFeed();
            if (current(id)) notice("Vehicle refresh completed.", "success");
          } else if (Date.now() < deadline) later(poll, 2500);
          else { refreshBusy = false; notice("Vehicle response is delayed; the next refresh will check again."); }
        } catch (error) { if (current(id)) { refreshBusy = false; notice(error.message, "danger"); } }
      };
      later(poll, 2500);
      return true;
    } catch (error) { if (current(id)) { refreshBusy = false; notice(error.message, "danger"); } return false; }
  }
  async function command(commandName, buttonId, extended = false) {
    const feedback = (state, success = null) => extended
      ? emit("updateGmoneExtendedControlState", buttonId, state === "sending", success)
      : emit("setButtonFeedback", buttonId, state, commandName);
    if (!allowed("commands") || !COMMANDS.has(commandName) || !session.capabilities.supportedCommands.includes(commandName)) {
      feedback("danger", false); notice("\ud604\uc7ac \uc0ac\uc6a9\ud560 \uc218 \uc5c6\ub294 \ucc28\ub7c9 \uba85\ub839\uc785\ub2c8\ub2e4. \ub85c\uadf8\uc778 \uc0c1\ud0dc\uc640 \uc9c0\uc6d0 \uae30\ub2a5\uc744 \ud655\uc778\ud574 \uc8fc\uc138\uc694.", "danger"); return false;
    }
    if (commandBusy || Date.now() - lastCommandAt < 3000) {
      feedback("cooldown", false); notice("\ub2e4\ub978 \ucc28\ub7c9 \uba85\ub839\uc744 \ubcf4\ub0b4\uae30 \uc804\uc5d0 \uc7a0\uc2dc \uae30\ub2e4\ub824 \uc8fc\uc138\uc694."); return false;
    }
    const id = generation;
    commandBusy = true;
    lastCommandAt = Date.now();
    feedback("sending");
    try {
      const requestId = root.crypto.randomUUID();
      const result = await request("/api/command", "POST", { command: commandName, requestId, confirmed: true }, id);
      if (result.command !== commandName || (Object.hasOwn(result, "requestId") && result.requestId !== requestId)) {
        throw new Error("Command response does not match the request.");
      }
      if (["account_invalid_or_expired", "session_expired"].includes(result.code)) {
        session.capabilities.commands = false;
        account = { ...account, loggedIn: false, message: "\uba40\ud2f0\ud329 \uc778\uc99d\uc774 \ub9cc\ub8cc\ub418\uc5c8\uc2b5\ub2c8\ub2e4. \ub2e4\uc2dc \ub85c\uadf8\uc778\ud574 \uc8fc\uc138\uc694." };
        renderAccount();
        renderVehicle();
      }
      if (result.ok !== true || result.state !== "server_responded") {
        if (result.state === "blocked" && result.ok === false) {
          feedback("danger", false);
          notice(text(result.message) || "\ucc28\ub7c9 \uba85\ub839\uc744 \ubcf4\ub0b4\uc9c0 \uc54a\uc558\uc2b5\ub2c8\ub2e4. \ucc28\ub7c9 \uc0c1\ud0dc\uc640 \ub85c\uadf8\uc778 \uc0c1\ud0dc\ub97c \ud655\uc778\ud574 \uc8fc\uc138\uc694.", "danger");
          return false;
        }
        throw new Error("Command protocol success was not confirmed.");
      }
      // Protocol success is not vehicle telemetry. Avoid Android's completion
      // label and optimistic engine/closure changes until a new status arrives.
      feedback("");
      notice("\uba40\ud2f0\ud329 \uc11c\ubc84\uc758 \uba85\ub839 \ucc98\ub9ac \uc751\ub2f5\uc744 \ud655\uc778\ud588\uc2b5\ub2c8\ub2e4. \uc2e4\uc81c \ucc28\ub7c9 \ub3d9\uc791\uc740 \ubcc4\ub3c4\ub85c \ud655\uc778\ud574 \uc8fc\uc138\uc694.");
      [250, 7500, 15000, 25000, 40000].forEach(delay => later(() => { if (current(id)) refreshFeed(); }, delay));
      return true;
    } catch (error) {
      if (current(id)) { feedback(""); notice("\uba85\ub839 \uc644\ub8cc\ub97c \ud655\uc778\ud558\uc9c0 \ubabb\ud588\uc2b5\ub2c8\ub2e4. \uc7ac\uc804\uc1a1\ud558\uc9c0 \ub9d0\uace0 \ucc28\ub7c9 \uc0c1\ud0dc\ub97c \ud655\uc778\ud574 \uc8fc\uc138\uc694.", "danger"); }
      return false;
    } finally { if (current(id)) commandBusy = false; }
  }
  async function changeAccount(method, credentials) {
    if (!active || accountBusy || commandBusy) { notice("Account changes are unavailable while a request is in progress.", "danger"); return false; }
    const id = generation;
    accountBusy = true;
    renderAccount();
    try {
      const result = await request("/api/account", method, credentials, id);
      if (typeof result.loggedIn !== "boolean") throw new Error("Invalid account response.");
      // Account mutations are authoritative; start drops old reads and cached UI
      // before displaying anything for the newly selected backend account.
      await start({ ...session, capabilities: { ...session.capabilities, commands: result.loggedIn },
        account: { loggedIn: result.loggedIn, email: text(result.email) || "", message: text(result.message) || "" } });
      return result.loggedIn === (method === "POST");
    } catch (error) {
      if (current(id)) {
        // Failed account verification must never leave the old command grant active.
        session.capabilities = { ...session.capabilities, commands: false };
        accountBusy = false;
        renderAccount();
        notice(error.message, "danger");
      }
      return false;
    }
  }
  async function requestLive() {
    if (!allowed("live")) { emit("onWayonLiveSessionError", "\ud604\uc7ac \ucc28\ub7c9 Live\ub97c \uc0ac\uc6a9\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4."); return false; }
    const id = generation, attempt = ++liveRequest;
    try {
      const result = await request("/api/live/session", "POST", {}, id);
      if (attempt !== liveRequest) return false;
      const url = new URL(result.websocketUrl, root.location.href);
      if (url.protocol === "https:") url.protocol = "wss:";
      if (url.protocol === "http:") url.protocol = "ws:";
      const expectedProtocol = root.location.protocol === "https:" ? "wss:" : "ws:";
      if (url.protocol !== expectedProtocol || url.host !== root.location.host || url.pathname !== "/api/live/stream"
        || url.username || url.password || !text(result.protocol)) throw new Error("Invalid live proxy session.");
      emit("onWayonLiveSession", url.href, result.protocol);
      return true;
    } catch (error) { if (current(id) && attempt === liveRequest) emit("onWayonLiveSessionError", error.message); return false; }
  }
  async function ambient(raw) {
    if (!allowed("ambient")) { emit("onAmbientCommandResult", null, "failed"); notice("\ud604\uc7ac \uc570\ube44\uc5b8\ud2b8 \uc81c\uc5b4\ub97c \uc0ac\uc6a9\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.", "danger"); return false; }
    const id = generation;
    try {
      const payload = jsonObject(raw);
      if (!payload) throw new Error("Invalid ambient settings.");
      emit("onAmbientCommandResult", null, "sending");
      const result = await request("/api/ambient", "POST", payload, id);
      if (result.ok === false) throw new Error("Ambient request failed.");
      emit("onAmbientCommandResult", JSON.stringify(result), result.status || "pending");
      if (!result.id) return true;
      let remaining = 6;
      const poll = async () => {
        if (!current(id)) return;
        try {
          const status = await request(API + "ambient/status", "GET", undefined, id);
          const matched = status.command?.id === result.id;
          if (matched) emit("onAmbientCommandResult", JSON.stringify(status), status.command.status);
          if (matched && ["acknowledged", "failed", "expired"].includes(status.command.status)) return;
          if (--remaining > 0) later(poll, 1000);
          else emit("onAmbientCommandResult", null, "expired");
        } catch (error) { if (current(id)) { emit("onAmbientCommandResult", null, "failed"); notice(error.message, "danger"); } }
      };
      later(poll, 1000);
      return true;
    } catch (error) { if (current(id)) { emit("onAmbientCommandResult", null, "failed"); notice(error.message, "danger"); } return false; }
  }
  function unsupported(feature) { notice(`\uc6f9\uc571\uc5d0\uc11c\ub294 ${feature} \uae30\ub2a5\uc744 \uc9c0\uc6d0\ud558\uc9c0 \uc54a\uc2b5\ub2c8\ub2e4.`, "danger"); return false; }
  function stop() {
    active = false;
    generation++;
    liveRequest++;
    for (const controller of requests) controller.abort();
    requests.clear();
    for (const timer of timers) root.clearTimeout(timer);
    timers.clear();
    session = account = feed = vehicle = feedJob = tripsJob = pollTimer = null;
    history = [];
    fullHistory = accountBusy = commandBusy = refreshBusy = liveActive = false;
    lastCommandAt = -Infinity;
    emit("stopWayonLiveView");
    emit("closeSnapshotViewer");
    emit("closeSnapshotHistory");
    emit("closeBlackboxPlayer");
    emit("updateVehicleCommandReady", false);
    emit("updateGmoneAccountState", false, "", "Account login required", false);
    emit("setVehicleDataState", "unavailable", "", false);
    emit("updateGmoneDetails", null);
    emit("markWayonCloudUnavailable", "Session is not active.");
    emit("updateHeroLocationMap", null, null, "", "", false, null, false);
    emit("updateMyLocation", null, null, null, "");
    emit("updateWayonImpactState", null);
    emit("updateWayonCloudSnapshots", "[]");
    emit("updateWayonCloudKeyInput", "");
    emit("onWayonCloudHistoryUpdated");
  }
  async function start(provided) {
    stop();
    active = true;
    const id = generation;
    try {
      const next = provided || await request("/api/session", "GET", undefined, id);
      if (!current(id)) return false;
      if (next.authenticated !== true) { stop(); return false; }
      const capabilities = { ...object(next.capabilities) };
      capabilities.supportedCommands = Array.isArray(capabilities.supportedCommands)
        ? capabilities.supportedCommands.filter(name => typeof name === "string" && COMMANDS.has(name)) : [];
      session = { authenticated: true, csrfToken: text(next.csrfToken), capabilities };
      account = object(next.account) || { loggedIn: session.capabilities.commands === true, email: text(next.email) || "" };
      emit("updateWayonCloudKeyInput", "session");
      renderAccount();
      emit("setVehicleDataState", "loading", "", true);
      return await refreshFeed();
    } catch (error) { if (current(id)) { stop(); notice(error.message, "danger"); } return false; }
  }

  root.Android = {
    refreshCarData: refreshVehicle,
    refreshWayonCloudData: refreshFeed,
    refreshVehicleScreen: refreshFeed,
    refreshWayonCloudTrips: refreshTrips,
    getDrivingHistory: () => JSON.stringify(history),
    clearDrivingHistory: () => unsupported("\uc11c\ubc84 \uc8fc\ud589 \uc774\ub825 \uc0ad\uc81c"),
    loadInitialApiUrl() { if (active) { emit("updateWayonCloudKeyInput", "session"); renderAccount(); } },
    saveApiUrl: () => unsupported("API \ud0a4 \uc9c1\uc811 \uc800\uc7a5"),
    saveWayonCloudKey: () => { emit("updateWayonCloudKeyInput", active ? "session" : ""); return unsupported("\ud074\ub77c\uc6b0\ub4dc \ud0a4 \uc9c1\uc811 \uc800\uc7a5"); },
    loginGmone(email, password) {
      if (!text(email) || !text(password)) { notice("Enter an email and password.", "danger"); return Promise.resolve(false); }
      return changeAccount("POST", { email: email.trim(), password });
    },
    logoutGmone: () => changeAccount("DELETE"),
    refreshGmoneAccount: refreshVehicle,
    handleClick: (key, name, buttonId) => command(key, buttonId),
    handleLongPress: (key, name, buttonId) => command(key, buttonId),
    sendGmoneExtendedControl: (key, buttonId) => command(key, buttonId, true),
    requestWayonLiveSession: requestLive,
    setWayonLiveActive(value) {
      liveActive = value === true;
      if (!liveActive) { liveRequest++; if (active && !root.document.hidden) refreshFeed(); }
      schedulePoll();
    },
    applyAmbientOverride: ambient,
    loadSavedLocation() { if (active) renderCloud(); },
    refreshMyLocation() {
      const id = generation;
      if (!active) return false;
      if (!root.navigator.geolocation) { emit("updateMyLocation", null, null, null, "\ud604\uc7ac \uc704\uce58\ub97c \ud655\uc778\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4."); return unsupported("\ud734\ub300\ud3f0 \uc704\uce58 \uc870\ud68c"); }
      root.navigator.geolocation.getCurrentPosition(position => {
        if (current(id)) emit("updateMyLocation", coordinate(position.coords.latitude, 90), coordinate(position.coords.longitude, 180),
          number(position.coords.accuracy), kst(number(position.timestamp)));
      }, () => {
        if (current(id)) { emit("updateMyLocation", null, null, null, "\ud604\uc7ac \uc704\uce58\ub97c \ud655\uc778\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4."); notice("\ud734\ub300\ud3f0 \uc704\uce58\ub97c \ud655\uc778\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.", "danger"); }
      }, { timeout: 10000, maximumAge: 30000, enableHighAccuracy: false });
      return true;
    },
    openSavedLocationMap() {
      const state = active ? cloudState() : null;
      if (state?.latitude == null || state?.longitude == null) { notice("\ucc28\ub7c9 \uc704\uce58\ub97c \ud655\uc778\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.", "danger"); return false; }
      root.open(`https://maps.apple.com/?ll=${state.latitude},${state.longitude}&q=Parked%20vehicle`, "_blank", "noopener,noreferrer");
      return true;
    },
    acknowledgeWayonImpact() { emit("updateWayonImpactState", null); },
    setWindowPositionSensorsVisible: visible => emit("updateWindowPositionSensorsVisibility", visible === true),
    refreshGmoneSettings: () => { emit("updateGmoneSettingsSaveState", false, "\uc6f9\uc571\uc5d0\uc11c\ub294 \uc124\uc815\uc744 \uc870\ud68c\ub9cc \ud560 \uc218 \uc788\uc2b5\ub2c8\ub2e4."); return unsupported("\ubaa8\ub4c8 \uc124\uc815 \uc9c1\uc811 \uc0c8\ub85c\uace0\uce68"); },
    saveGmoneSettings: () => { emit("updateGmoneSettingsSaveState", false, "\uc124\uc815\uc744 \uc800\uc7a5\ud558\uc9c0 \uc54a\uc558\uc2b5\ub2c8\ub2e4."); return unsupported("\ubaa8\ub4c8 \uc124\uc815 \ubcc0\uacbd"); },
    refreshGmoneDiagnostics: () => { emit("updateGmoneDiagnosticActionState", "refresh", false, "\uc6f9\uc571\uc5d0\uc11c \uc9c0\uc6d0\ud558\uc9c0 \uc54a\ub294 \uae30\ub2a5\uc785\ub2c8\ub2e4."); return unsupported("\uace0\uc7a5\ucf54\ub4dc \uc9c1\uc811 \uc0c8\ub85c\uace0\uce68"); },
    clearGmoneDiagnosticCodes: () => { emit("updateGmoneDiagnosticActionState", "clear", false, "\uc6f9\uc571\uc5d0\uc11c \uc9c0\uc6d0\ud558\uc9c0 \uc54a\ub294 \uae30\ub2a5\uc785\ub2c8\ub2e4."); return unsupported("\uace0\uc7a5\ucf54\ub4dc \uc0ad\uc81c"); },
    setDtcNotificationExcluded: () => unsupported("\uace0\uc7a5\ucf54\ub4dc \uc54c\ub9bc \uc124\uc815"),
    setAutoRefresh: () => unsupported("\ub9e4\uc2dc\uac04 \ubc31\uadf8\ub77c\uc6b4\ub4dc \ucc28\ub7c9 \uc870\ud68c"),
    handleVentilationToggle: () => unsupported("\uc608\uc57d \ud658\uae30"),
    handleHeatEjectToggle: () => unsupported("\uc608\uc57d \uc5f4 \ubc30\ucd9c"),
    showPairedDeviceList: () => unsupported("\uc548\ub4dc\ub85c\uc774\ub4dc \ube14\ub8e8\ud22c\uc2a4 \uc5f0\uacb0 \uc124\uc815"),
    refreshDeviceList: () => { emit("updateDeviceList", "<p>\uc6f9\uc571\uc5d0\uc11c\ub294 \ube14\ub8e8\ud22c\uc2a4 \uae30\uae30 \ubaa9\ub85d\uc744 \ud655\uc778\ud560 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.</p>"); return unsupported("\uc548\ub4dc\ub85c\uc774\ub4dc \ube14\ub8e8\ud22c\uc2a4 \uae30\uae30 \uc870\ud68c"); },
    toggleBluetoothTest: () => unsupported("\uc548\ub4dc\ub85c\uc774\ub4dc \ube14\ub8e8\ud22c\uc2a4 \ud14c\uc2a4\ud2b8"),
    checkBluetoothStatusForDebug: () => unsupported("\uc548\ub4dc\ub85c\uc774\ub4dc \ube14\ub8e8\ud22c\uc2a4 \uc0c1\ud0dc \ud655\uc778"),
  };
  root.TraverseWeb = Object.freeze({ start, stop, render, csrfToken: () => active ? session?.csrfToken || "" : "" });
  root.document.addEventListener("visibilitychange", () => {
    if (!active) return;
    if (root.document.hidden) cancelTimer(pollTimer);
    else if (!liveActive) refreshFeed();
  });
  root.addEventListener("online", () => { if (active && !liveActive) refreshFeed(); });
})(window);
