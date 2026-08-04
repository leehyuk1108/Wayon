#!/usr/bin/env python3
import sys
from pathlib import Path


METHOD_START = ".method private flushNext()V"
METHOD_END = ".end method"

STALE_RECONNECT = """    .line 423
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectIfNeeded()V"""

GATT_RECOVERY = """    .line 423
    const/4 v1, 0x0

    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyReady:Z

    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStartQueued:Z

    const/4 v2, 0x0

    iput-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    iput-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->closeGatt()V

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect()V"""


def patch_flush_next(smali: str) -> str:
  start = smali.index(METHOD_START)
  end = smali.index(METHOD_END, start)
  method = smali[start:end]
  if method.count(STALE_RECONNECT) != 1:
    raise ValueError("expected one stale write reconnect path in flushNext")
  method = method.replace(STALE_RECONNECT, GATT_RECOVERY)
  return smali[:start] + method + smali[end:]


def main() -> int:
  if len(sys.argv) != 2:
    print(f"usage: {Path(sys.argv[0]).name} AmbientLightController.smali", file=sys.stderr)
    return 2
  path = Path(sys.argv[1])
  path.write_text(patch_flush_next(path.read_text()))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
