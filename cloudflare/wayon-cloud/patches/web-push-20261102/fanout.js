// WAYON_WEB_PUSH_V1_BEGIN
// Optional server-to-server ingress only; never accept a caller-selected URL or scope.
// The receiver must verify DEVICE_ID and claim (deviceId, type, id, test) before delivery and must
// not reopen uncertain claims. This hook neither retries nor changes FCM receipts.
const WAYON_WEB_PUSH_URL = "https://my-traverse-web.hyuklee.workers.dev/api/internal/notify";
const WAYON_WEB_PUSH_TIMEOUT_MS = 1500;
const WAYON_WEB_PUSH_MAX_BYTES = 8192;

function wayonWebPushText(value, limit) {
  return typeof value === "string" && value.length > 0 && value.length <= limit * 2 &&
    value.trim() === value && Array.from(value).length <= limit &&
    !/[\p{Cc}\p{Cf}\p{Cs}\p{Zl}\p{Zp}]/u.test(value);
}

function wayonWebPushPayload(deviceId, data, now = Date.now()) {
  if (!data || typeof data !== "object" || Array.isArray(data) || data.deviceId !== deviceId ||
      (data.test !== "true" && data.test !== "false")) return null;
  let eventId, occurredAt, visible;
  switch (data.type) {
    case "wayon_parking_sign":
      eventId = data.parkingEventId;
      break;
    case "wayon_automatic_shutdown":
    case "wayon_door_lock":
    case "wayon_parking_unlocked":
      eventId = data.vehicleEventId;
      break;
    case "wayon_impact":
      eventId = data.impactId;
      break;
    default:
      return null;
  }
  if (!wayonWebPushText(eventId, 128) || !/^[A-Za-z0-9._:-]+$/.test(eventId)) return null;
  if (data.type === "wayon_door_lock" && data.locked !== "true" && data.locked !== "false") return null;
  occurredAt = data.type === "wayon_impact" ? data.detectedAt : data.occurredAt;
  if (typeof occurredAt !== "string" || occurredAt.length > 40 ||
      !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$/.test(occurredAt)) return null;
  const timestamp = Date.parse(occurredAt);
  if (!Number.isFinite(timestamp) || now - timestamp > 600000 || timestamp - now > 120000) return null;
  visible = visibleFcmNotification(data);
  const test = data.test === "true";
  const testSuffix = test ? " \uD14C\uC2A4\uD2B8" : "";
  if (!visible && data.type === "wayon_impact") {
    visible = {title: "\uCC28\uB7C9 \uCDA9\uACA9 \uAC10\uC9C0" + testSuffix, body: "\uCC28\uB7C9 \uCDA9\uACA9 \uC774\uBCA4\uD2B8\uAC00 \uAC10\uC9C0\uB418\uC5C8\uC2B5\uB2C8\uB2E4."};
  } else if (!visible && data.type === "wayon_parking_unlocked") {
    visible = {title: "\uC8FC\uCC28 \uD6C4 \uC7A0\uAE08 \uD655\uC778" + testSuffix, body: "\uC8FC\uCC28 \uD6C4 \uCC28\uB7C9 \uC7A0\uAE08\uC774 \uD655\uC778\uB418\uC9C0 \uC54A\uC558\uC2B5\uB2C8\uB2E4."};
  }
  if (!visible || !wayonWebPushText(visible.title, 128) || !wayonWebPushText(visible.body, 2048)) return null;
  // Deliberately exclude tokens, raw evidence, images, locations and health data.
  const body = JSON.stringify({deviceId, type: data.type, id: eventId, title: visible.title, body: visible.body,
    occurredAt: new Date(timestamp).toISOString(), test});
  return new TextEncoder().encode(body).byteLength <= WAYON_WEB_PUSH_MAX_BYTES ? body : null;
}

async function sendWayonWebPush(env, deviceId, data) {
  let timer, controller;
  try {
    const secret = env.MY_TRAVERSE_WEB_PUSH_TOKEN;
    const owner = env.WAYON_AI_DEVICE_ID || env.WAYON_LEGACY_FIREBASE_DEVICE_ID;
    if (typeof secret !== "string" || secret.trim() !== secret || !/^[A-Za-z0-9_-]{32,256}$/.test(secret) ||
        typeof owner !== "string" || owner.trim() !== owner || !validDeviceId(owner) || owner !== deviceId) return false;
    const body = wayonWebPushPayload(deviceId, data);
    if (!body) return false;
    controller = new AbortController();
    const deadline = new Promise(resolve => {
      timer = setTimeout(() => { controller.abort(); resolve(null); }, WAYON_WEB_PUSH_TIMEOUT_MS);
    });
    // The race bounds the await even if an injected transport ignores abort.
    const response = await Promise.race([fetch(WAYON_WEB_PUSH_URL, {
      method: "POST", redirect: "manual", signal: controller.signal,
      headers: {authorization: `Bearer ${secret}`, "content-type": "application/json"}, body,
    }), deadline]);
    if (response?.body) void response.body.cancel().catch(() => {});
    return Boolean(response?.ok);
  } catch (_) {
    return false;
  } finally {
    clearTimeout(timer);
    controller?.abort();
  }
}
// WAYON_WEB_PUSH_V1_END
