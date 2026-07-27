#!/usr/bin/env node
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { createInterface } from "node:readline";

const SERVER_INFO = { name: "wayon", version: "1.0.0" };
const DEFAULT_ENDPOINT = "https://wayon-cloud.hyuklee.workers.dev";
const DEFAULT_CONFIG = join(homedir(), ".config", "wayon", "ai.credentials.json");

function loadConfig() {
  const path = process.env.WAYON_AI_CONFIG || DEFAULT_CONFIG;
  let file = {};
  if (existsSync(path)) file = JSON.parse(readFileSync(path, "utf8"));
  const endpoint = String(process.env.WAYON_AI_ENDPOINT || file.endpoint || DEFAULT_ENDPOINT).replace(/\/+$/, "");
  const token = String(process.env.WAYON_AI_READ_TOKEN || file.token || "");
  if (!token) throw new Error(`Wayon AI token missing. Set WAYON_AI_READ_TOKEN or ${path}`);
  return { endpoint, token };
}

async function apiJson(path) {
  const { endpoint, token } = loadConfig();
  const response = await fetch(`${endpoint}${path}`, {
    headers: { authorization: `Bearer ${token}`, accept: "application/json" },
  });
  if (!response.ok) {
    const body = (await response.text()).slice(0, 500);
    throw new Error(`Wayon API ${response.status}: ${body}`);
  }
  return response.json();
}

async function apiImage(snapshotId) {
  const { endpoint, token } = loadConfig();
  const response = await fetch(`${endpoint}/api/ai/images/${encodeURIComponent(snapshotId)}`, {
    headers: { authorization: `Bearer ${token}`, accept: "image/jpeg" },
  });
  if (!response.ok) throw new Error(`Wayon image API ${response.status}`);
  const data = Buffer.from(await response.arrayBuffer()).toString("base64");
  return { data, mimeType: response.headers.get("content-type") || "image/jpeg" };
}

const TOOLS = [
  {
    name: "wayon_get_context",
    description: "Get read-only current Wayon vehicle/comma state, freshness, voltage, power, numeric temperatures, location, OpenPilot state, latest trip, impacts, events, and snapshots. Panda error counters are cumulative since Panda boot, so a nonzero total alone is not an active fault.",
    inputSchema: {
      type: "object",
      properties: {
        impacts: { type: "integer", minimum: 1, maximum: 50, default: 8 },
        events: { type: "integer", minimum: 1, maximum: 100, default: 20 },
        snapshots: { type: "integer", minimum: 1, maximum: 50, default: 12 },
      },
      additionalProperties: false,
    },
  },
  {
    name: "wayon_list_trips",
    description: "List recent Wayon trip summaries.",
    inputSchema: {
      type: "object",
      properties: { limit: { type: "integer", minimum: 1, maximum: 250, default: 25 } },
      additionalProperties: false,
    },
  },
  {
    name: "wayon_get_trip",
    description: "Get one Wayon trip including route points.",
    inputSchema: {
      type: "object",
      properties: { tripId: { type: "string" } },
      required: ["tripId"],
      additionalProperties: false,
    },
  },
  {
    name: "wayon_list_impacts",
    description: "List offroad impact detections and associated wide/driver camera snapshot IDs.",
    inputSchema: {
      type: "object",
      properties: { limit: { type: "integer", minimum: 1, maximum: 100, default: 25 } },
      additionalProperties: false,
    },
  },
  {
    name: "wayon_list_vehicle_events",
    description: "List vehicle lock, unlock, and parked-unlocked events.",
    inputSchema: {
      type: "object",
      properties: { limit: { type: "integer", minimum: 1, maximum: 250, default: 50 } },
      additionalProperties: false,
    },
  },
  {
    name: "wayon_list_snapshots",
    description: "List wide and driver camera snapshots, including impact association and image IDs.",
    inputSchema: {
      type: "object",
      properties: { limit: { type: "integer", minimum: 1, maximum: 100, default: 25 } },
      additionalProperties: false,
    },
  },
  {
    name: "wayon_get_snapshot_image",
    description: "Load one authorized Wayon JPEG snapshot as an MCP image. Driver-camera images are privacy-sensitive.",
    inputSchema: {
      type: "object",
      properties: { snapshotId: { type: "string" } },
      required: ["snapshotId"],
      additionalProperties: false,
    },
  },
];

function integer(value, fallback, max) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? Math.min(parsed, max) : fallback;
}

function textContent(value) {
  return [{ type: "text", text: JSON.stringify(value, null, 2) }];
}

async function callTool(name, args = {}) {
  if (name === "wayon_get_context") {
    const query = new URLSearchParams({
      impacts: String(integer(args.impacts, 8, 50)),
      events: String(integer(args.events, 20, 100)),
      snapshots: String(integer(args.snapshots, 12, 50)),
    });
    return { content: textContent(await apiJson(`/api/ai/context?${query}`)) };
  }
  if (name === "wayon_list_trips") {
    return { content: textContent(await apiJson(`/api/ai/trips?limit=${integer(args.limit, 25, 250)}`)) };
  }
  if (name === "wayon_get_trip") {
    if (!args.tripId) throw new Error("tripId required");
    return { content: textContent(await apiJson(`/api/ai/trips/${encodeURIComponent(args.tripId)}`)) };
  }
  if (name === "wayon_list_impacts") {
    return { content: textContent(await apiJson(`/api/ai/impacts?limit=${integer(args.limit, 25, 100)}`)) };
  }
  if (name === "wayon_list_vehicle_events") {
    return { content: textContent(await apiJson(`/api/ai/events?limit=${integer(args.limit, 50, 250)}`)) };
  }
  if (name === "wayon_list_snapshots") {
    return { content: textContent(await apiJson(`/api/ai/snapshots?limit=${integer(args.limit, 25, 100)}`)) };
  }
  if (name === "wayon_get_snapshot_image") {
    if (!args.snapshotId) throw new Error("snapshotId required");
    const image = await apiImage(args.snapshotId);
    return {
      content: [
        { type: "text", text: `Wayon snapshot ${args.snapshotId}` },
        { type: "image", data: image.data, mimeType: image.mimeType },
      ],
    };
  }
  throw new Error(`Unknown tool: ${name}`);
}

async function handle(message) {
  if (message.method === "initialize") {
    return {
      protocolVersion: message.params?.protocolVersion || "2024-11-05",
      capabilities: { tools: {} },
      serverInfo: SERVER_INFO,
      instructions: "Read-only Wayon data. Check freshness.stale before calling telemetry live. Panda error counters are cumulative since boot; alert only on an increase between fresh samples from the same boot. Never infer vehicle control capability.",
    };
  }
  if (message.method === "ping") return {};
  if (message.method === "tools/list") return { tools: TOOLS };
  if (message.method === "tools/call") return callTool(message.params?.name, message.params?.arguments || {});
  if (message.method?.startsWith("notifications/")) return undefined;
  throw Object.assign(new Error(`Method not found: ${message.method}`), { code: -32601 });
}

function write(message) {
  process.stdout.write(`${JSON.stringify(message)}\n`);
}

const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
input.on("line", async (line) => {
  if (!line.trim()) return;
  let message;
  try {
    message = JSON.parse(line);
    const result = await handle(message);
    if (message.id != null && result !== undefined) write({ jsonrpc: "2.0", id: message.id, result });
  } catch (error) {
    if (message?.id != null) {
      write({
        jsonrpc: "2.0",
        id: message.id,
        error: { code: error.code || -32000, message: String(error.message || error) },
      });
    }
  }
});
