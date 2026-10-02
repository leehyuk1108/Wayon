"""Narrow transport patch for the exact live v152 APK; no lighting-policy edits."""
import re
import sys
from pathlib import Path

ROOT = "smali_classes2/com/navdy/hud/app/ambient/"
CONTROLLER = ROOT + "AmbientLightController.smali"
CALLBACK = ROOT + "AmbientLightController$1.smali"
SCAN = ROOT + "AmbientLightController$2.smali"
C = "Lcom/navdy/hud/app/ambient/AmbientLightController;"
S = "Lcom/navdy/hud/app/ambient/AmbientGattSession;"
NAMES = [CONTROLLER, CALLBACK, SCAN]


def once(text, old, new):
  assert text.count(old) == 1, (old[:100], text.count(old))
  return text.replace(old, new, 1)


def method(text, signature, body):
  pattern = rf"(?ms)^\.method {re.escape(signature)}\n.*?^\.end method"
  assert len(re.findall(pattern, text)) == 1, signature
  return re.sub(pattern, lambda _: body, text)


def transform(files):
  result = dict(files)
  controller = files[CONTROLLER]
  controller = once(controller,
      f"    iput-object v0, p0, {C}->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;",
      f"""    new-instance v1, {S}
    iget-object v2, p0, {C}->mHandler:Landroid/os/Handler;
    invoke-direct {{v1, v0, v2, p1}}, {S}-><init>(Landroid/bluetooth/BluetoothGattCallback;Landroid/os/Handler;Landroid/content/Context;)V
    iput-object v1, p0, {C}->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;""")
  controller = once(controller,
      f"    iput-object p1, p0, {C}->mGatt:Landroid/bluetooth/BluetoothGatt;\n\n    .line 1455",
      f"""    iput-object p1, p0, {C}->mGatt:Landroid/bluetooth/BluetoothGatt;
    check-cast v2, {S}
    invoke-virtual {{v2, p1}}, {S}->attach(Landroid/bluetooth/BluetoothGatt;)V

    .line 1455""")
  # Offroad disconnects can empty the queue and skip scheduling entirely.
  # Enforce the cooldown independently of needsConnection and future payloads.
  controller = once(controller,
      ".method private scheduleReconnect(J)V\n    .locals 4\n",
      f""".method private scheduleReconnect(J)V
    .locals 4
    iget-object v0, p0, {C}->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;
    check-cast v0, {S}
    invoke-virtual {{v0, p1, p2}}, {S}->deferReconnect(J)J
    move-result-wide p1
""")
  controller = once(controller,
      ".method private connectIfNeeded()V\n    .locals 5\n",
      f""".method private connectIfNeeded()V
    .locals 5
    iget-object v0, p0, {C}->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;
    check-cast v0, {S}
    invoke-virtual {{v0}}, {S}->canConnect()Z
    move-result v0
    if-nez v0, :cooldown_elapsed
    return-void
    :cooldown_elapsed
""")
  controller = method(controller, "private closeGatt()V", f""".method private closeGatt()V
    .locals 3
    iget-object v0, p0, {C}->mGatt:Landroid/bluetooth/BluetoothGatt;
    iget-object v1, p0, {C}->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;
    check-cast v1, {S}
    invoke-virtual {{v1}}, {S}->detach()V
    const/4 v1, 0x0
    iput-object v1, p0, {C}->mGatt:Landroid/bluetooth/BluetoothGatt;
    iput-boolean v1, p0, {C}->mConnecting:Z
    iput-boolean v1, p0, {C}->mConnected:Z
    iput-boolean v1, p0, {C}->mNotifyReady:Z
    iput-boolean v1, p0, {C}->mWriting:Z
    iput-boolean v1, p0, {C}->mStartQueued:Z
    iput-object v1, p0, {C}->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;
    iput-object v1, p0, {C}->mNotifyCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;
    iget-object v1, p0, {C}->mHandler:Landroid/os/Handler;
""" + "\n".join(f"""    iget-object v2, p0, {C}->{name}:Ljava/lang/Runnable;
    invoke-virtual {{v1, v2}}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V"""
      for name in ["mConnectTimeoutRunnable", "mWritePaceRunnable", "mWriteTimeoutRunnable",
                   "mFlushAfterAckRunnable", "mBrightnessSyncRunnable"]) + """
    if-eqz v0, :done
    :try_disconnect
    invoke-virtual {v0}, Landroid/bluetooth/BluetoothGatt;->disconnect()V
    :end_disconnect
    .catch Ljava/lang/Exception; {:try_disconnect .. :end_disconnect} :disconnect_error
    goto :try_close
    :disconnect_error
    move-exception v1
    :try_close
    invoke-virtual {v0}, Landroid/bluetooth/BluetoothGatt;->close()V
    :end_close
    .catch Ljava/lang/Exception; {:try_close .. :end_close} :close_error
    goto :done
    :close_error
    move-exception v1
    :done
    return-void
.end method""")
  # A queued advertisement must not replace an already connecting/connected GATT.
  controller += f"""
.method static synthetic access$10100({C})Z
    .locals 1
    iget-boolean v0, p0, {C}->mScanning:Z
    if-eqz v0, :reject
    iget-boolean v0, p0, {C}->mConnecting:Z
    if-nez v0, :reject
    iget-boolean v0, p0, {C}->mConnected:Z
    if-nez v0, :reject
    const/4 v0, 0x1
    return v0
    :reject
    const/4 v0, 0x0
    return v0
.end method
"""
  result[CONTROLLER] = controller
  scan = files[SCAN]
  scan = once(scan, "    .locals 0\n\n    .line 204", f"""    .locals 1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$2;->this$0:{C}
    invoke-static {{v0}}, {C}->access$10100({C})Z
    move-result v0
    if-nez v0, :scan_active
    return-void
    :scan_active

    .line 204""")
  result[SCAN] = scan
  callback = files[CALLBACK]
  # Keep notifyReady false when CCCD setup cannot even be queued. The session's
  # setup timeout will disconnect/retry instead of sending unacknowledged writes.
  start = callback.index("    .line 159\n    :cond_2", callback.index(".method public onServicesDiscovered"))
  end = callback.index("    :cond_3", start)
  callback = callback[:start] + """    :cond_2
    const-string p1, "NavdyAmbient"
    const-string p2, "ambient notifications not queued; waiting for bounded recovery"
    invoke-static {p1, p2}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I
    return-void

""" + callback[end:]
  result[CALLBACK] = callback
  return result


if __name__ == "__main__":
  base = Path(sys.argv[1])
  for name, content in transform({name: (base / name).read_text() for name in NAMES}).items():
    (base / name).write_text(content)
