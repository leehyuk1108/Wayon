#!/usr/bin/env python3
import sys
from pathlib import Path


METHOD_START = ".method private static buildBrightnessPacket(ZI)[B"
METHOD_END = ".end method"

UNIFORM_BRIGHTNESS = """    const/16 v1, 0x8d

    filled-new-array {v0, p0, p1, p1}, [I

    move-result-object p0

    invoke-static {v1, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildPacket(I[I)[B"""

ZONE_2_FIXED_BRIGHTNESS = """    const/16 v1, 0x1e

    filled-new-array {v0, p0, p1, v1}, [I

    move-result-object p0

    const/16 v1, 0x8d

    invoke-static {v1, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildPacket(I[I)[B"""


def patch_brightness_packet(smali: str) -> str:
  start = smali.index(METHOD_START)
  end = smali.index(METHOD_END, start)
  method = smali[start:end]
  if ZONE_2_FIXED_BRIGHTNESS in method:
    return smali
  if method.count(UNIFORM_BRIGHTNESS) != 1:
    raise ValueError("expected one uniform Zone 1/Zone 2 brightness payload")
  method = method.replace(UNIFORM_BRIGHTNESS, ZONE_2_FIXED_BRIGHTNESS)
  return smali[:start] + method + smali[end:]


def main() -> int:
  if len(sys.argv) != 2:
    print(f"usage: {Path(sys.argv[0]).name} AmbientLightController.smali", file=sys.stderr)
    return 2
  path = Path(sys.argv[1])
  path.write_text(patch_brightness_packet(path.read_text()))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
