from pathlib import Path


CONTROLLER = Path(__file__).parent / "hud_patch" / "engaged-path-v7-alert-banner-speed-warning" / "src" / "com" / "navdy" / "hud" / "app" / "ambient" / "AmbientLightController.java"


def controller_source() -> str:
  return CONTROLLER.read_text()


def test_ambient_state_machine_is_kept_in_source() -> None:
  source = controller_source()
  assert "OFFROAD_DOOR_CLOSE_DELAY_MS = 20000" in source
  assert "OFFROAD_DOOR_MAX_ON_MS = 1200000" in source
  assert "OFFROAD_TRANSITION_LIGHT_MS = 120000" in source
  assert "OFFROAD_DOOR_ZONE_1_BRIGHTNESS = 20" in source
  assert "OFFROAD_DOOR_ZONE_2_BRIGHTNESS = 100" in source


def test_ambient_watchdog_fades_off_after_three_seconds() -> None:
  source = controller_source()
  assert "VEHICLE_DATA_TIMEOUT_MS = 3000" in source
  assert "controller.noteVehicleDataReceived();" in source
  watchdog = source[source.index("mVehicleDataWatchdogRunnable"):source.index("private BluetoothAdapter mAdapter")]
  assert 'Log.w(TAG, "comma vehicle data timeout; fading ambient off")' in watchdog
  assert "startAmbientFade(0, 0, AMBIENT_NORMAL_FADE_MS);" in watchdog


def test_ambient_fade_is_capped_at_thirty_hertz() -> None:
  source = controller_source()
  assert "DEFAULT_AMBIENT_TRANSITION_STEP_MS = 33" in source
  assert "MIN_AMBIENT_TRANSITION_STEP_MS = 33" in source
  assert "mHandler.postDelayed(this, readAmbientFrameStepMs());" in source
  assert "readAmbientTransitionStepMs() * 2" in source


def test_onroad_payloads_do_not_restart_brightness_sync() -> None:
  source = controller_source()
  state = source[source.index("private void setVehicleState"):source.index("private void updateCpuWakeLock")]
  onroad = state[state.index("if (onroad) {"):state.index("stopBrightnessSync();")]
  assert "if (onroadChanged)" in onroad
  assert onroad.count("startBrightnessSync();") == 1


def test_new_fade_discards_stale_ambient_commands() -> None:
  source = controller_source()
  fade = source[source.index("private void startAmbientFade"):source.index("private void applyAmbientFrame")]
  assert "removePendingAmbientStatePackets();" in fade


def test_fade_interpolates_color_and_brightness_together() -> None:
  source = controller_source()
  runnable = source[source.index("private final Runnable mAmbientFadeRunnable"):source.index("private final Runnable mOffroadDelayedOffRunnable")]
  fade = source[source.index("private void startAmbientFade"):source.index("private void hardAmbientOff")]
  assert "mAmbientFadeStartZone1Red = mCurrentZone1Red" in fade
  assert "mAmbientTargetZone2Blue = colorPacketValue(targetColor, 10, 255)" in fade
  assert "interpolate(mAmbientFadeStartZone1Red, mAmbientTargetZone1Red, eased)" in runnable
  assert "applyAmbientFrame(zone1, zone2" in runnable
  assert "sendAmbientFrame(" in fade
  assert "sendPacket(PACKET_RESTORE);" not in fade


def test_profile_payload_is_applied_once_and_drives_state_colors() -> None:
  source = controller_source()
  profile = source[source.index("private void setAmbientProfile"):source.index("private JSONObject profileSection")]
  payload = source[source.index("public static void onOpenpilotPayload(Context context, String payload)"):source.index("public static void onOpenpilotPayload(Context context, JSONObject payload)")]
  assert 'json.optJSONObject("ambientOverride")' in payload
  assert "controller.setAmbientOverride(ambientOverride);" in payload
  assert "profile.toString().equals(mProfile.toString())" in profile
  assert 'return profileColorPacket("driving", "zone1", "onroadDoor", "zone2")' in source


def test_daytime_overspeed_uses_two_red_brightness_levels() -> None:
  source = controller_source()
  blink = source[source.index("private final Runnable mBlinkRunnable"):source.index("private final Runnable mWriteTimeoutRunnable")]
  assert "DAY_WARNING_DIM_PERCENT = 45" in source
  assert "DAY_WARNING_STEP_INTERVAL_MS = 700" in source
  assert "mDayWarningDimmed ? dimLevel : brightness" in blink
  assert "mDayWarningDimmed = !mDayWarningDimmed" in blink
  assert "FADE_STEPS" not in blink
  assert "PACKET_RESTORE" not in blink


def test_night_overspeed_stays_fixed_red() -> None:
  source = controller_source()
  blink = source[source.index("private final Runnable mBlinkRunnable"):source.index("private final Runnable mWriteTimeoutRunnable")]
  low_light = blink[blink.index("brightness < MIN_FADE_AMBIENT_BRIGHTNESS"):blink.index("if (!mWarningAnimationStarted)")]
  assert "sendPacket(warningColorPacket());" in low_light
  assert "LOW_LIGHT_CHECK_INTERVAL_MS" in low_light
  assert "mDayWarningDimmed = !mDayWarningDimmed" not in low_light


def test_remembered_ble_address_is_tried_before_scan() -> None:
  source = controller_source()
  connect = source[source.index("private void connectIfNeeded()"):source.index("private void scheduleReconnect()")]
  assert connect.index("connectRememberedCandidate()") < connect.index("connectBondedCandidate()")
  assert connect.index("connectBondedCandidate()") < connect.index("startLeScan")
  assert "CONNECT_ATTEMPT_TIMEOUT_MS = 10000" in source
  assert 'Log.w(TAG, "ambient direct connection timed out; falling back to scan")' in source
