#!/usr/bin/env python3
import sys
from pathlib import Path


METHOD_START = ".method public static isCameraNotification("
METHOD_END = ".end method"


def disable_broad_origin_matches(smali: str) -> str:
  start = smali.index(METHOD_START)
  end = smali.index(METHOD_END, start)
  method = smali[start:end]

  for origin in ("carrot", "comma"):
    block = "".join((
      f'    const-string v1, "{origin}"\n\n',
      "    invoke-static {v0, v1}, Lcom/navdy/hud/app/maps/widget/",
      "TrafficIncidentWidgetPresenter;->containsIgnoreCase(Ljava/lang/String;Ljava/lang/String;)Z\n\n",
      "    move-result v2\n\n",
      "    if-nez v2, :cond_1",
    ))
    if method.count(block) != 2:
      raise ValueError(f"expected two {origin} origin checks")
    method = method.replace(block, block.rsplit("\n", 1)[0] + "\n\n    nop")

  return smali[:start] + method + smali[end:]


def main() -> int:
  if len(sys.argv) != 2:
    print(f"usage: {Path(sys.argv[0]).name} TrafficIncidentWidgetPresenter.smali", file=sys.stderr)
    return 2
  path = Path(sys.argv[1])
  path.write_text(disable_broad_origin_matches(path.read_text()))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
