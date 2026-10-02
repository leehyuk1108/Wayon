"""Add reliable delivery recovery on top of the exact installed v153r2 build."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("previous_patch", HERE.parent / "v153-ambient-session/apply.py")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
once, method = previous.once, previous.method
C, S, ROOT = previous.C, previous.S, previous.ROOT
CONTROLLER = previous.CONTROLLER
TIMEOUT = ROOT + "AmbientLightController$9.smali"
CALLBACK = previous.CALLBACK
NAMES = [CONTROLLER, TIMEOUT, CALLBACK]


def transform(files):
  result = dict(files)
  controller = files[CONTROLLER]
  # Route both application commands and the one-byte ACK through one ATT lane.
  for registers in ("v1, v2", "v0, v1"):
    old = f"    invoke-virtual {{{registers}}}, Landroid/bluetooth/BluetoothGatt;->writeCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)Z"
    new = f"""    iget-object v4, p0, {C}->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;
    check-cast v4, {S}
    invoke-virtual {{v4, {registers}}}, {S}->write(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z"""
    controller = once(controller, old, new)
  controller = once(controller, ".method private writeAck()V\n    .locals 3", ".method private writeAck()V\n    .locals 5")
  controller = once(controller, ".method private needsConnection()Z\n    .locals 1\n", f""".method private needsConnection()Z
    .locals 1
    iget-object v0, p0, {C}->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;
    check-cast v0, {S}
    invoke-virtual {{v0}}, {S}->needsDelivery()Z
    move-result v0
    if-eqz v0, :check_light_policy
    const/4 v0, 0x1
    return v0
    :check_light_policy
""")
  # Keep an explicit retry intent even if the off command was already dequeued.
  controller += f"""
.method static synthetic access$10200({C})V
    .locals 1
    iget-object v0, p0, {C}->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;
    check-cast v0, {S}
    invoke-virtual {{v0}}, {S}->deliveryTimeout()V
    return-void
.end method
"""
  result[CONTROLLER] = controller
  callback = files[CALLBACK]
  # ACK-only packets complete a request but must not themselves be ACKed.
  callback = once(callback, "    if-ne p1, p2, :cond_1\n\n    .line 191", """    const/4 v1, -0x1
    if-eq p1, v1, :accepted_response
    if-ne p1, p2, :cond_1
    :accepted_response
    move v1, p1

    .line 191""")
  callback = once(callback, f"    invoke-static {{p1}}, {C}->access$2700({C})V", f"""    const/4 v0, -0x1
    if-eq v1, v0, :no_ack_for_ack
    invoke-static {{p1}}, {C}->access$2700({C})V
    :no_ack_for_ack""")
  result[CALLBACK] = callback
  result[TIMEOUT] = method(files[TIMEOUT], "public run()V", f""".method public run()V
    .locals 1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$9;->this$0:{C}
    invoke-static {{v0}}, {C}->access$10200({C})V
    return-void
.end method""")
  return result
