"""OFF barriers over the verified v154r2 controller, not an older source tree."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("delivery", HERE.parent / "v154-ambient-delivery/apply.py")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
once, method = previous.once, previous.method
C, S, ROOT = previous.C, previous.S, previous.ROOT
CONTROLLER = previous.CONTROLLER
NAMES = [CONTROLLER]


def edit(text, signature, transform):
  start = text.index(".method " + signature + "\n")
  end = text.index(".end method", start) + len(".end method")
  return text[:start] + transform(text[start:end]) + text[end:]


def transform(files):
  text = files[CONTROLLER]
  # All producers, including delayed door/manual/overspeed work, cross this gate.
  text += f"""
.method private ambientOutputBlocked()Z
    .locals 1
    iget-boolean v0, p0, {C}->mReverseActive:Z
    if-nez v0, :blocked
    iget-boolean v0, p0, {C}->mVehicleDataTimedOut:Z
    :blocked
    return v0
.end method
"""
  text = edit(text, "private sendPacket([B)V", lambda body: once(body,
      "    .locals 2\n", f"""    .locals 2
    invoke-direct {{p0}}, {C}->ambientOutputBlocked()Z
    move-result v0
    if-eqz v0, :output_allowed
    invoke-static {{p1}}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->isState([B)Z
    move-result v0
    if-eqz v0, :output_allowed
    invoke-static {{p1}}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->isOff([B)Z
    move-result v0
    if-nez v0, :output_allowed
    return-void
    :output_allowed
    invoke-static {{p1}}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->isOff([B)Z
    move-result v0
    if-eqz v0, :normal_queue
    invoke-direct {{p0}}, {C}->removePendingAmbientStatePackets()V
    :normal_queue
"""))
  text = edit(text, "private startAmbientFade(IIJ[B)V", lambda body: once(body,
      "    .locals 2\n", f"""    .locals 2
    invoke-direct {{p0}}, {C}->ambientOutputBlocked()Z
    move-result v0
    if-eqz v0, :fade_allowed
    const-string v0, "output blocked"
    invoke-direct {{p0, v0}}, {C}->hardAmbientOff(Ljava/lang/String;)V
    return-void
    :fade_allowed
"""))
  # Reconnect must not revive old targets while comma data has timed out.
  text = edit(text, "private restoreActiveStateAfterConnect()V", lambda body: once(body,
      f"    iget-boolean v0, p0, {C}->mReverseActive:Z",
      f"    invoke-direct {{p0}}, {C}->ambientOutputBlocked()Z\n    move-result v0"))
  # Withdraw queued frames at BOTH queue levels. An accepted ATT write is never
  # canceled; the serial lane completes it before writing the latest OFF.
  text = edit(text, "private hardAmbientOff(Ljava/lang/String;)V", lambda body: once(body,
      "    .locals 2\n", f"""    .locals 2
    iget-object v0, p0, {C}->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;
    check-cast v0, {S}
    invoke-virtual {{v0, p1}}, {S}->offRequested(Ljava/lang/String;)V
    invoke-direct {{p0}}, {C}->stopBlink()V
    invoke-direct {{p0}}, {C}->stopBrightnessSync()V
    const/4 v0, 0x0
    iput-boolean v0, p0, {C}->mRequestedOverspeed:Z
    iput-boolean v0, p0, {C}->mOverspeedActive:Z
    iput-boolean v0, p0, {C}->mWriting:Z
    iget-object v0, p0, {C}->mHandler:Landroid/os/Handler;
    iget-object v1, p0, {C}->mOverspeedStateRunnable:Ljava/lang/Runnable;
    invoke-virtual {{v0, v1}}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V
    iget-object v1, p0, {C}->mWriteTimeoutRunnable:Ljava/lang/Runnable;
    invoke-virtual {{v0, v1}}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V
    iget-object v1, p0, {C}->mWritePaceRunnable:Ljava/lang/Runnable;
    invoke-virtual {{v0, v1}}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V
    iget-object v1, p0, {C}->mFlushAfterAckRunnable:Ljava/lang/Runnable;
    invoke-virtual {{v0, v1}}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V
"""))
  # Retain gear transitions in the persistent journal, not only volatile logcat.
  text = edit(text, "private setGearText(Ljava/lang/String;)V", lambda body: once(body,
      f"    iput-object p1, p0, {C}->mLastGear:Ljava/lang/String;",
      f"""    iput-object p1, p0, {C}->mLastGear:Ljava/lang/String;
    iget-object v0, p0, {C}->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;
    check-cast v0, {S}
    invoke-virtual {{v0, p1}}, {S}->gearReceived(Ljava/lang/String;)V"""))
  # Hard OFF now stops polling. Enabling/editing the profile onroad must restart
  # it, otherwise automatic brightness would freeze after a master OFF/ON cycle.
  text = edit(text, "private setAmbientProfile(Lorg/json/JSONObject;)V", lambda body: once(body,
      f"    invoke-direct {{p0}}, {C}->applyVehicleStateTargets()V", f"""    iget-boolean p1, p0, {C}->mOnroad:Z
    if-eqz p1, :profile_offroad
    iget-boolean p1, p0, {C}->mVehicleDataTimedOut:Z
    if-nez p1, :profile_offroad
    invoke-direct {{p0}}, {C}->startBrightnessSync()V
    goto :goto_0
    :profile_offroad
    invoke-direct {{p0}}, {C}->applyVehicleStateTargets()V"""))
  return {CONTROLLER: text}


def helper_sources():
  base = HERE.parent / "v154-ambient-delivery"
  lane = (base / "AmbientWriteLane.java").read_text()
  lane = once(lane, "  public boolean offer(", """  public static boolean isState(byte[] value) {
    return value != null && value.length >= 8 && value[0] == 0x2e && value[1] == (byte) 0x8d;
  }

  public static boolean isOff(byte[] value) {
    return isState(value) && value.length == 8 && value[2] == 4
        && value[3] == 0 && value[4] == 0 && value[5] == 0 && value[6] == 0;
  }

  public void discardQueuedState() {
    for (Iterator<Item> it = queue.iterator(); it.hasNext();) {
      if (isState(it.next().value)) it.remove();
    }
  }

  public boolean offer(""")
  lane = once(lane, "    Item item = new Item(gatt, characteristic);", """    Item item = new Item(gatt, characteristic);
    if (isOff(item.value)) discardQueuedState();""")
  session = (base / "AmbientGattSession.java").read_text()
  session = once(session, "  private byte[] lastCommand;", """  private byte[] lastCommand;
  private String lastOffReason;
  private long lastOffRecordMs;""")
  session = once(session, "  public boolean needsDelivery()", """  public void offRequested(String reason) {
    deliveryPending = true;
    if (writes != null) writes.discardQueuedState();
    long now = SystemClock.elapsedRealtime();
    if (!reason.equals(lastOffReason) || now - lastOffRecordMs >= 60000L) {
      record("off requested reason=" + reason + " sessionPresent=" + (current != null));
      lastOffReason = reason;
      lastOffRecordMs = now;
    }
  }

  public void gearReceived(String gear) { record("gear received=" + gear); }

  public boolean needsDelivery()""")
  return {"AmbientWriteLane.java": lane, "AmbientGattSession.java": session}
