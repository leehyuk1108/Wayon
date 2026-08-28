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
  assert "mHandler.postDelayed(this, readAmbientTransitionStepMs());" in source


def test_onroad_payloads_do_not_restart_brightness_sync() -> None:
  source = controller_source()
  state = source[source.index("private void setVehicleState"):source.index("private void updateCpuWakeLock")]
  onroad = state[state.index("if (onroad) {"):state.index("stopBrightnessSync();")]
  assert "if (onroadChanged)" in onroad
  assert onroad.count("startBrightnessSync();") == 1


def test_new_fade_discards_stale_ambient_commands() -> None:
  source = controller_source()
  fade = source[source.index("private void startAmbientFade"):source.index("private void applyAmbientBrightness")]
  assert "removePendingAmbientStatePackets();" in fade


def test_overspeed_stays_red_until_restore() -> None:
  source = controller_source()
  red_down = source.index("mFadePhase == FADE_PHASE_RED_DOWN && mFadeStep == 0")
  restore = source.index("mFadePhase == FADE_PHASE_EXIT_RED_DOWN && mFadeStep == 0", red_down)
  red_pulse_branch = source[red_down:restore]
  assert "mFadePhase = FADE_PHASE_RED_UP;" in red_pulse_branch
  assert "PACKET_RESTORE" not in red_pulse_branch


def test_remembered_ble_address_is_tried_before_scan() -> None:
  source = controller_source()
  connect = source[source.index("private void connectIfNeeded()"):source.index("private void scheduleReconnect()")]
  assert connect.index("connectRememberedCandidate()") < connect.index("connectBondedCandidate()")
  assert connect.index("connectBondedCandidate()") < connect.index("startLeScan")
  assert "CONNECT_ATTEMPT_TIMEOUT_MS = 10000" in source
  assert 'Log.w(TAG, "ambient direct connection timed out; falling back to scan")' in source
