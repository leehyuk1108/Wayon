#!/usr/bin/env python3
import re
import sys
from pathlib import Path


METHOD_START = ".method public static isCameraNotification("
CLEAR_METHOD_START = ".method private static isCameraClearNotification("
CLEAR_ACTION_START = ".method private clearCameraText()V"
METHOD_END = ".end method"
PRIVATE_DISTANCE_FIELD = ".field private static lastCameraDistance:Ljava/lang/String;"
PUBLIC_DISTANCE_FIELD = ".field public static lastCameraDistance:Ljava/lang/String;"
LAST_SPEED_FIELD = ".field private static lastCameraSpeed:Ljava/lang/String;"
MOBILE_FIELD = ".field private static lastCameraIsMobile:Z"
SECTION_FIELD = ".field public static lastCameraIsSection:Z"
MOBILE_RESOURCE = (
  '    <public type="drawable" name="carrot_mobile_camera_speed_sign_background" id="0x7f02029f" />'
)
RESOURCE_ANCHOR = '    <public type="drawable" name="navdy_acc_control_arrow" id="0x7f02029e" />'


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


MOBILE_DETECTION = r'''    const/4 v4, 0x0

    iget-object v0, p1, Lcom/navdy/service/library/events/notification/NotificationEvent;->title:Ljava/lang/String;

    const-string v3, "mobile"

    invoke-static {v0, v3}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->containsIgnoreCase(Ljava/lang/String;Ljava/lang/String;)Z

    move-result v0

    if-nez v0, :mobile_camera_detected

    const-string/jumbo v3, "\uc774\ub3d9\uc2dd"

    iget-object v0, p1, Lcom/navdy/service/library/events/notification/NotificationEvent;->title:Ljava/lang/String;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->containsIgnoreCase(Ljava/lang/String;Ljava/lang/String;)Z

    move-result v0

    if-nez v0, :mobile_camera_detected

    iget-object v0, p1, Lcom/navdy/service/library/events/notification/NotificationEvent;->subtitle:Ljava/lang/String;

    const-string v3, "mobile"

    invoke-static {v0, v3}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->containsIgnoreCase(Ljava/lang/String;Ljava/lang/String;)Z

    move-result v0

    if-nez v0, :mobile_camera_detected

    const-string/jumbo v3, "\uc774\ub3d9\uc2dd"

    iget-object v0, p1, Lcom/navdy/service/library/events/notification/NotificationEvent;->subtitle:Ljava/lang/String;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->containsIgnoreCase(Ljava/lang/String;Ljava/lang/String;)Z

    move-result v0

    if-nez v0, :mobile_camera_detected

    iget-object v0, p1, Lcom/navdy/service/library/events/notification/NotificationEvent;->message:Ljava/lang/String;

    const-string v3, "mobile"

    invoke-static {v0, v3}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->containsIgnoreCase(Ljava/lang/String;Ljava/lang/String;)Z

    move-result v0

    if-nez v0, :mobile_camera_detected

    const-string/jumbo v3, "\uc774\ub3d9\uc2dd"

    iget-object v0, p1, Lcom/navdy/service/library/events/notification/NotificationEvent;->message:Ljava/lang/String;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->containsIgnoreCase(Ljava/lang/String;Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :mobile_camera_ready

    :mobile_camera_detected
    const/4 v4, 0x1

    :mobile_camera_ready'''

SECTION_DETECTION = r'''    const/4 v5, 0x0

    iget-object v0, p1, Lcom/navdy/service/library/events/notification/NotificationEvent;->title:Ljava/lang/String;

    const-string v3, "section"

    invoke-static {v0, v3}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->containsIgnoreCase(Ljava/lang/String;Ljava/lang/String;)Z

    move-result v0

    if-nez v0, :section_camera_detected

    const-string/jumbo v3, "\uad6c\uac04"

    iget-object v0, p1, Lcom/navdy/service/library/events/notification/NotificationEvent;->title:Ljava/lang/String;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->containsIgnoreCase(Ljava/lang/String;Ljava/lang/String;)Z

    move-result v0

    if-nez v0, :section_camera_detected

    iget-object v0, p1, Lcom/navdy/service/library/events/notification/NotificationEvent;->subtitle:Ljava/lang/String;

    const-string v3, "section"

    invoke-static {v0, v3}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->containsIgnoreCase(Ljava/lang/String;Ljava/lang/String;)Z

    move-result v0

    if-nez v0, :section_camera_detected

    const-string/jumbo v3, "\uad6c\uac04"

    iget-object v0, p1, Lcom/navdy/service/library/events/notification/NotificationEvent;->subtitle:Ljava/lang/String;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->containsIgnoreCase(Ljava/lang/String;Ljava/lang/String;)Z

    move-result v0

    if-nez v0, :section_camera_detected

    iget-object v0, p1, Lcom/navdy/service/library/events/notification/NotificationEvent;->message:Ljava/lang/String;

    const-string v3, "section"

    invoke-static {v0, v3}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->containsIgnoreCase(Ljava/lang/String;Ljava/lang/String;)Z

    move-result v0

    if-nez v0, :section_camera_detected

    const-string/jumbo v3, "\uad6c\uac04"

    iget-object v0, p1, Lcom/navdy/service/library/events/notification/NotificationEvent;->message:Ljava/lang/String;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->containsIgnoreCase(Ljava/lang/String;Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :section_camera_ready

    :section_camera_detected
    const/4 v5, 0x1

    :section_camera_ready'''

DISTANCE_FORMATTING = r'''    invoke-virtual {v2}, Ljava/lang/String;->toLowerCase()Ljava/lang/String;

    move-result-object v0

    const-string v1, "km"

    invoke-virtual {v0, v1}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v3

    if-nez v3, :camera_distance_format_done

    const-string v0, "[^0-9]"

    const-string v1, ""

    invoke-virtual {v2, v0, v1}, Ljava/lang/String;->replaceAll(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/String;->length()I

    move-result v1

    if-lez v1, :camera_distance_format_done

    invoke-static {v0}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I

    move-result v0

    const/16 v1, 0x3e8

    if-lt v0, v1, :camera_distance_format_done

    add-int/lit8 v0, v0, 0x32

    div-int/lit8 v0, v0, 0x64

    div-int/lit8 v1, v0, 0xa

    rem-int/lit8 v0, v0, 0xa

    new-instance v3, Ljava/lang/StringBuilder;

    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v3, v1}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v3

    const-string v1, "."

    invoke-virtual {v3, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    invoke-virtual {v3, v0}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v3

    const-string v0, "km"

    invoke-virtual {v3, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v2

    :camera_distance_format_done
'''


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


def register_mobile_camera_resource(presenter_path: Path) -> None:
  public_path = next((parent / "res/values/public.xml" for parent in presenter_path.parents
                      if (parent / "res/values/public.xml").is_file()), None)
  if public_path is None:
    raise ValueError("decoded APK public.xml not found")
  public_xml = public_path.read_text()
  if MOBILE_RESOURCE in public_xml:
    return
  if RESOURCE_ANCHOR not in public_xml:
    raise ValueError("mobile camera drawable ID anchor not found")
  public_path.write_text(public_xml.replace(RESOURCE_ANCHOR, RESOURCE_ANCHOR + "\n" + MOBILE_RESOURCE, 1))


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


def add_camera_type_fields(smali: str) -> str:
  if MOBILE_FIELD in smali and SECTION_FIELD in smali:
    return smali
  if LAST_SPEED_FIELD not in smali:
    raise ValueError("camera speed field not found")
  fields = [field for field in (MOBILE_FIELD, SECTION_FIELD) if field not in smali]
  return smali.replace(LAST_SPEED_FIELD, LAST_SPEED_FIELD + "\n\n" + "\n\n".join(fields), 1)


def patch_camera_distance_formatting(smali: str) -> str:
  start = smali.index(".method public onNotificationEvent(")
  end = smali.index(METHOD_END, start)
  method = smali[start:end]
  if ":camera_distance_format_done" in method or 'const-string v0, "[^0-9]"' in method:
    return smali
  anchor = """    :goto_0
    invoke-static {p1}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->extractCameraSpeed(Lcom/navdy/service/library/events/notification/NotificationEvent;)Ljava/lang/String;"""
  replacement = "    :goto_0\n" + DISTANCE_FORMATTING + "\n" + anchor.split("\n", 1)[1]
  if anchor not in method:
    raise ValueError("camera distance formatting anchor not found")
  method = method.replace(anchor, replacement, 1)
  return smali[:start] + method + smali[end:]


def patch_camera_background(smali: str) -> str:
  start = smali.index(".method private applyCameraText(")
  end = smali.index(METHOD_END, start)
  method = smali[start:end]
  if ":camera_background_ready" in method or (
    "lastCameraIsMobile:Z" in method and "->setBackgroundResource(I)V" in method
  ):
    return smali

  method = method.replace("    .locals 4", "    .locals 5", 1)
  method = method.replace(
    "    .prologue\n",
    """    .prologue
    sget-boolean v4, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsMobile:Z

    if-eqz v4, :camera_background_regular

    const v4, 0x7f02029f

    goto :camera_background_ready

    :camera_background_regular
    const v4, 0x7f020286

    :camera_background_ready
""",
    1,
  )
  method, count = re.subn(
    r"(    if-eqz v0, :cond_0\n\n+)(    const v1, -0x1000000)",
    r"\1    invoke-virtual {v0, v4}, Landroid/view/View;->setBackgroundResource(I)V\n\n\2",
    method,
    count=1,
  )
  if count != 1:
    raise ValueError("primary camera background anchor not found")
  method = re.sub(
    r"(    check-cast (v\d+), Landroid/widget/TextView;\n\n+)(    const v\d+, -0x1000000)",
    lambda match: match.group(1) +
    f"    invoke-virtual {{{match.group(2)}, v4}}, Landroid/view/View;->setBackgroundResource(I)V\n\n" +
    match.group(3),
    method,
  )
  return smali[:start] + method + smali[end:]


def patch_camera_distance_music_typeface(smali: str) -> str:
  start = smali.index(".method private applyCameraText(")
  end = smali.index(METHOD_END, start)
  method = smali[start:end]
  if ":camera_distance_music_typeface" in method or "Typeface;->DEFAULT:Landroid/graphics/Typeface;" in method:
    return smali
  anchor = """    iget-object v0, p0, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->distanceTextView:Landroid/widget/TextView;

    if-eqz v0, :cond_0

    const/4 v1, -0x1"""
  replacement = """    iget-object v0, p0, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->distanceTextView:Landroid/widget/TextView;

    if-eqz v0, :cond_0

    :camera_distance_music_typeface
    sget-object v1, Landroid/graphics/Typeface;->DEFAULT:Landroid/graphics/Typeface;

    const/4 v2, 0x0

    invoke-virtual {v0, v1, v2}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;I)V

    const/4 v1, -0x1"""
  if anchor not in method:
    raise ValueError("camera distance typeface anchor not found")
  method = method.replace(anchor, replacement, 1)
  return smali[:start] + method + smali[end:]


def patch_section_legacy_card_visibility(smali: str) -> str:
  start = smali.index(".method private applyCameraText(")
  end = smali.index(METHOD_END, start)
  method = smali[start:end]
  if ":section_legacy_camera_visibility_ready" in method:
    return smali

  anchor = """    if-eqz v2, :cond_3

    const/4 v3, 0x0

    invoke-virtual {v2, v3}, Landroid/view/View;->setVisibility(I)V"""
  replacement = """    if-eqz v2, :cond_3

    sget-boolean v3, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsSection:Z

    if-eqz v3, :section_legacy_camera_regular

    const/16 v3, 0x8

    goto :section_legacy_camera_visibility_ready

    :section_legacy_camera_regular
    const/4 v3, 0x0

    :section_legacy_camera_visibility_ready
    invoke-virtual {v2, v3}, Landroid/view/View;->setVisibility(I)V"""
  if anchor not in method:
    raise ValueError("stock camera container visibility anchor not found")
  method = method.replace(anchor, replacement, 1)
  return smali[:start] + method + smali[end:]


def patch_encoded_camera_speed(smali: str) -> str:
  start = smali.index(".method public static getLastCameraSpeedLimit()I")
  end = smali.index(METHOD_END, start)
  method = smali[start:end]
  if ":camera_speed_positive" in method or (
    "lastCameraIsMobile:Z" in method and "neg-int v0, v0" in method
  ):
    return smali
  anchor = """    move-result v0

    return v0"""
  replacement = """    move-result v0

    sget-boolean v1, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsMobile:Z

    if-eqz v1, :camera_speed_positive

    neg-int v0, v0

    :camera_speed_positive
    return v0"""
  if anchor not in method:
    raise ValueError("camera speed return anchor not found")
  method = method.replace(anchor, replacement, 1)
  return smali[:start] + method + smali[end:]


def patch_camera_type_notification_state(smali: str) -> str:
  start = smali.index(".method public onNotificationEvent(")
  end = smali.index(METHOD_END, start)
  method = smali[start:end]
  if (
    "sput-boolean v0, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsSection:Z" in method and
    "sput-boolean v5, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsSection:Z" in method and
    'const-string/jumbo v3, "section"' in method
  ):
    return smali

  has_existing_mobile_state = (
    "sput-boolean v4, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsMobile:Z" in method
  )
  if ":mobile_camera_ready" in method or has_existing_mobile_state:
    method = method.replace("    .locals 5", "    .locals 6", 1)
    clear_anchor = """    sput-boolean v0, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsMobile:Z

    invoke-direct {p0}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->clearCameraText()V"""
    clear_replacement = """    sput-boolean v0, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsMobile:Z

    sput-boolean v0, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsSection:Z

    invoke-direct {p0}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->clearCameraText()V"""
    if clear_anchor not in method:
      raise ValueError("existing mobile clear anchor not found")
    method = method.replace(clear_anchor, clear_replacement, 1)

    detection_pattern = re.compile(
      r"(    :(?:mobile_camera_ready|cond_\d+)\n)(    sget-object v0, "
      r"Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraSpeed:Ljava/lang/String;)"
    )
    method, count = detection_pattern.subn(
      lambda match: match.group(1) + "\n" + SECTION_DETECTION + "\n\n" + match.group(2),
      method,
      count=1,
    )
    if count != 1:
      raise ValueError("existing mobile detection anchor not found")

    dedup_pattern = re.compile(
      r"(    sget-boolean v0, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;"
      r"->lastCameraIsMobile:Z\n\n    if-ne v0, v4, (:\w+)\n)"
    )
    method, count = dedup_pattern.subn(
      lambda match: match.group(1) + "\n"
      "    sget-boolean v0, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsSection:Z\n\n"
      f"    if-ne v0, v5, {match.group(2)}\n",
      method,
      count=1,
    )
    if count != 1:
      raise ValueError("existing mobile dedup anchor not found")

    apply_anchor = """    sput-boolean v4, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsMobile:Z

    invoke-direct {p0, v1, v2}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->applyCameraText(Ljava/lang/String;Ljava/lang/String;)V"""
    apply_replacement = """    sput-boolean v4, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsMobile:Z

    sput-boolean v5, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsSection:Z

    invoke-direct {p0, v1, v2}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->applyCameraText(Ljava/lang/String;Ljava/lang/String;)V"""
    if apply_anchor not in method:
      raise ValueError("existing mobile apply anchor not found")
    method = method.replace(apply_anchor, apply_replacement, 1)
    return smali[:start] + method + smali[end:]

  method = method.replace("    .locals 4", "    .locals 6", 1)
  clear_anchor = """    sput-object v1, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraDistance:Ljava/lang/String;

    invoke-direct {p0}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->clearCameraText()V"""
  clear_replacement = """    sput-object v1, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraDistance:Ljava/lang/String;

    const/4 v0, 0x0

    sput-boolean v0, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsMobile:Z

    sput-boolean v0, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsSection:Z

    invoke-direct {p0}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->clearCameraText()V"""
  method = method.replace(clear_anchor, clear_replacement, 1)

  speed_anchor = """    move-result-object v1

    sget-object v0, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraSpeed:Ljava/lang/String;"""
  speed_replacement = """    move-result-object v1

""" + MOBILE_DETECTION + "\n\n" + SECTION_DETECTION + """

    sget-object v0, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraSpeed:Ljava/lang/String;"""
  if speed_anchor not in method:
    raise ValueError("camera notification speed anchor not found")
  method = method.replace(speed_anchor, speed_replacement, 1)

  same_distance = """    if-nez v0, :goto_1

    :apply_camera_notification"""
  compare_type = """    if-nez v0, :apply_camera_notification

    sget-boolean v0, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsMobile:Z

    if-ne v0, v4, :goto_1

    sget-boolean v0, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsSection:Z

    if-ne v0, v5, :goto_1

    :apply_camera_notification"""
  if same_distance not in method:
    raise ValueError("camera notification dedup anchor not found")
  method = method.replace(same_distance, compare_type, 1)

  apply_anchor = """    sput-object v2, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraDistance:Ljava/lang/String;

    invoke-direct {p0, v1, v2}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->applyCameraText(Ljava/lang/String;Ljava/lang/String;)V"""
  apply_replacement = """    sput-object v2, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraDistance:Ljava/lang/String;

    sput-boolean v4, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsMobile:Z

    sput-boolean v5, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->lastCameraIsSection:Z

    invoke-direct {p0, v1, v2}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->applyCameraText(Ljava/lang/String;Ljava/lang/String;)V"""
  method = method.replace(apply_anchor, apply_replacement, 1)
  return smali[:start] + method + smali[end:]


def main() -> int:
  if len(sys.argv) != 2:
    print(f"usage: {Path(sys.argv[0]).name} TrafficIncidentWidgetPresenter.smali", file=sys.stderr)
    return 2
  path = Path(sys.argv[1])
  register_mobile_camera_resource(path)
  smali = path.read_text()
  validate_camera_clear_action(smali)
  smali = expose_camera_distance(smali)
  smali = restore_camera_clear_match(smali)
  smali = add_camera_type_fields(smali)
  smali = patch_camera_distance_formatting(smali)
  smali = patch_camera_background(smali)
  smali = patch_camera_distance_music_typeface(smali)
  smali = patch_section_legacy_card_visibility(smali)
  smali = patch_encoded_camera_speed(smali)
  smali = patch_camera_type_notification_state(smali)
  path.write_text(disable_broad_origin_matches(smali))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
