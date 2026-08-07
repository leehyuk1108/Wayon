#!/usr/bin/env python3
import sys
from pathlib import Path


METHOD_START = ".method public static isCameraNotification("
CLEAR_METHOD_START = ".method private static isCameraClearNotification("
CLEAR_ACTION_START = ".method private clearCameraText()V"
METHOD_END = ".end method"
PRIVATE_DISTANCE_FIELD = ".field private static lastCameraDistance:Ljava/lang/String;"
PUBLIC_DISTANCE_FIELD = ".field public static lastCameraDistance:Ljava/lang/String;"


CLEAR_METHOD = """.method private static isCameraClearNotification(Lcom/navdy/service/library/events/notification/NotificationEvent;)Z
    .locals 3
    .param p0, "event"    # Lcom/navdy/service/library/events/notification/NotificationEvent;

    if-eqz p0, :cond_clear_false

    iget-object v0, p0, Lcom/navdy/service/library/events/notification/NotificationEvent;->title:Ljava/lang/String;

    const-string v1, "Camera Clear"

    invoke-virtual {v1, v0}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    move-result v2

    if-nez v2, :cond_clear_true

    iget-object v0, p0, Lcom/navdy/service/library/events/notification/NotificationEvent;->message:Ljava/lang/String;

    const-string v1, "No camera"

    invoke-virtual {v1, v0}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    move-result v2

    if-nez v2, :cond_clear_true

    :cond_clear_false
    const/4 v0, 0x0

    return v0

    :cond_clear_true
    const/4 v0, 0x1

    return v0
.end method"""


def restore_camera_clear_match(smali: str) -> str:
  start = smali.index(CLEAR_METHOD_START)
  end = smali.index(METHOD_END, start) + len(METHOD_END)
  return smali[:start] + CLEAR_METHOD + smali[end:]


def validate_camera_clear_action(smali: str) -> None:
  start = smali.index(CLEAR_ACTION_START)
  end = smali.index(METHOD_END, start)
  method = smali[start:end]
  if "const/4 v3, 0x4" not in method or "Landroid/view/View;->setVisibility(I)V" not in method:
    raise ValueError("camera clear action does not hide the camera widget")


def expose_camera_distance(smali: str) -> str:
  if PUBLIC_DISTANCE_FIELD in smali:
    return smali
  if PRIVATE_DISTANCE_FIELD not in smali:
    raise ValueError("camera distance field not found")
  return smali.replace(PRIVATE_DISTANCE_FIELD, PUBLIC_DISTANCE_FIELD, 1)


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
    disabled_block = block.rsplit("    if-nez v2, :cond_1", 1)[0] + "    nop"
    if method.count(block) == 2:
      method = method.replace(block, disabled_block)
    elif method.count(disabled_block) != 2:
      raise ValueError(f"expected two {origin} origin checks")

  return smali[:start] + method + smali[end:]


def main() -> int:
  if len(sys.argv) != 2:
    print(f"usage: {Path(sys.argv[0]).name} TrafficIncidentWidgetPresenter.smali", file=sys.stderr)
    return 2
  path = Path(sys.argv[1])
  smali = path.read_text()
  validate_camera_clear_action(smali)
  smali = expose_camera_distance(smali)
  smali = restore_camera_clear_match(smali)
  path.write_text(disable_broad_origin_matches(smali))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
