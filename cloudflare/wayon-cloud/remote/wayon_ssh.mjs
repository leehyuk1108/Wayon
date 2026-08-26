#!/usr/bin/env node
import {
  chmodSync,
  mkdtempSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { generateKeyPairSync, randomBytes } from "node:crypto";
import { spawn } from "node:child_process";

function sshString(value) {
  const bytes = Buffer.from(value);
  const length = Buffer.alloc(4);
  length.writeUInt32BE(bytes.length);
  return Buffer.concat([length, bytes]);
}

function sshMpint(value) {
  let bytes = Buffer.from(value, "base64url");
  while (bytes.length > 1 && bytes[0] === 0) bytes = bytes.subarray(1);
  if (bytes[0] & 0x80) bytes = Buffer.concat([Buffer.from([0]), bytes]);
  return sshString(bytes);
}

function shellQuote(value) {
  return `'${String(value).replaceAll("'", `'"'"'`)}'`;
}

const { privateKey, publicKey } = generateKeyPairSync("rsa", { modulusLength: 3072 });
const jwk = publicKey.export({ format: "jwk" });
const publicBlob = Buffer.concat([
  sshString("ssh-rsa"),
  sshMpint(jwk.e),
  sshMpint(jwk.n),
]);
const temporaryRoot = mkdtempSync(join(tmpdir(), "wayon-ssh-"));
const identityPath = join(temporaryRoot, "identity");
const publicKeyPath = join(temporaryRoot, "identity.pub");
const knownHostsPath = join(temporaryRoot, "known_hosts");
writeFileSync(identityPath, privateKey.export({ type: "pkcs1", format: "pem" }), { mode: 0o600 });
writeFileSync(
  publicKeyPath,
  `ssh-rsa ${publicBlob.toString("base64")} wayon-${randomBytes(8).toString("hex")}\n`,
  { mode: 0o600 },
);
chmodSync(identityPath, 0o600);

const scriptRoot = dirname(fileURLToPath(import.meta.url));
const proxyPath = join(scriptRoot, "wayon_ssh_proxy.mjs");
const proxyCommand = `${shellQuote(process.execPath)} ${shellQuote(proxyPath)}`;
const extraArgs = process.argv.slice(2);
const sshExecutable = process.env.WAYON_SSH_BIN || "ssh";
const child = spawn(sshExecutable, [
  "-i", identityPath,
  "-o", "IdentitiesOnly=yes",
  "-o", `UserKnownHostsFile=${knownHostsPath}`,
  "-o", "StrictHostKeyChecking=accept-new",
  "-o", `ProxyCommand=${proxyCommand}`,
  ...extraArgs,
  "comma@wayon-device",
], {
  stdio: "inherit",
  env: { ...process.env, WAYON_SSH_PUBLIC_KEY_FILE: publicKeyPath },
});

const cleanup = () => {
  try { rmSync(temporaryRoot, { recursive: true, force: true }); } catch {}
};
child.once("exit", (code, signal) => {
  cleanup();
  if (signal) process.kill(process.pid, signal);
  else process.exit(code ?? 1);
});
process.once("SIGINT", () => child.kill("SIGINT"));
process.once("SIGTERM", () => child.kill("SIGTERM"));
