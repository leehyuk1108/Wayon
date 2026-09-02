package com.navdy.hud.app.ambient;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCallback;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattDescriptor;
import android.bluetooth.BluetoothGattService;
import android.bluetooth.BluetoothProfile;
import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
import android.os.SystemClock;
import android.provider.Settings;
import android.util.Log;

import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.ArrayDeque;
import java.util.Date;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;
import java.util.TimeZone;
import java.util.UUID;

public final class AmbientLightController {
  private static final String TAG = "NavdyAmbient";
  private static final UUID SERVICE_UUID = UUID.fromString("0000ae30-0000-1000-8000-00805f9b34fb");
  private static final UUID LEGACY_SERVICE_UUID = UUID.fromString("0000ae00-0000-1000-8000-00805f9b34fb");
  private static final UUID WRITE_UUID = UUID.fromString("0000ae01-0000-1000-8000-00805f9b34fb");
  private static final UUID NOTIFY_UUID = UUID.fromString("0000ae02-0000-1000-8000-00805f9b34fb");
  private static final UUID CLIENT_CONFIG_UUID = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb");
  private static final int MIN_AMBIENT_BRIGHTNESS = 1;
  private static final int MAX_AMBIENT_BRIGHTNESS = 50;
  private static final int SCREEN_BRIGHTNESS_ONE_PERCENT = 16;
  private static final int SCREEN_BRIGHTNESS_EIGHT_PERCENT = 41;
  private static final int MID_AMBIENT_BRIGHTNESS = 8;
  private static final int SCREEN_BRIGHTNESS_FIFTY_PERCENT = 100;
  private static final int OUTDOOR_AMBIENT_BRIGHTNESS = 50;
  private static final int ZONE_2_AMBIENT_BRIGHTNESS = 40;
  private static final int MIN_FADE_AMBIENT_BRIGHTNESS = 8;
  private static final int DAY_WARNING_DIM_PERCENT = 45;
  private static final int BRIGHTNESS_UPDATE_DELTA = 2;
  private static final long AMBIENT_NORMAL_FADE_MS = 1000;
  private static final String AMBIENT_DEVICE_ADDRESS_SETTING = "navdy_ambient_device_address";
  private static final String AMBIENT_PROFILE_SETTING = "navdy_ambient_profile_json";
  private static final String AMBIENT_TRANSITION_STEP_SETTING = "navdy_ambient_transition_step_ms";
  private static final String ACK_SETTLE_INTERVAL_SETTING = "navdy_ambient_ack_settle_ms";
  private static final int DEFAULT_AMBIENT_TRANSITION_STEP_MS = 33;
  private static final int MIN_AMBIENT_TRANSITION_STEP_MS = 33;
  private static final int MAX_AMBIENT_TRANSITION_STEP_MS = 250;
  private static final int DEFAULT_ACK_SETTLE_INTERVAL_MS = 10;
  private static final int MIN_ACK_SETTLE_INTERVAL_MS = 5;
  private static final int MAX_ACK_SETTLE_INTERVAL_MS = 100;
  private static final long BRIGHTNESS_SYNC_INTERVAL_MS = 5000;
  private static final long CONNECT_RETRY_MS = 5000;
  private static final long CONNECT_ATTEMPT_TIMEOUT_MS = 10000;
  private static final long GATT_ERROR_RETRY_MS = 1500;
  private static final long START_PACKET_PACE_INTERVAL_MS = 120;
  private static final long DAY_WARNING_STEP_INTERVAL_MS = 700;
  private static final long LOW_LIGHT_CHECK_INTERVAL_MS = 1000;
  private static final long OVERSPEED_ON_DELAY_MS = 1000;
  private static final long OVERSPEED_OFF_DELAY_MS = 2000;
  private static final long OVERSPEED_MIN_ACTIVE_MS = 3000;
  private static final long OFFROAD_DELAYED_OFF_MS = 60000;
  private static final long OFFROAD_DOOR_CLOSE_DELAY_MS = 20000;
  private static final long OFFROAD_DOOR_MAX_ON_MS = 1200000;
  private static final long OFFROAD_TRANSITION_LIGHT_MS = 120000;
  private static final long MANUAL_OVERRIDE_MAX_MS = 1200000;
  private static final int OFFROAD_DOOR_ZONE_1_BRIGHTNESS = 20;
  private static final int OFFROAD_DOOR_ZONE_2_BRIGHTNESS = 100;
  private static final long VEHICLE_DATA_TIMEOUT_MS = 3000;

  private static final byte[] PACKET_START = new byte[] {
      0x2e, (byte) 0x81, 0x01, 0x01, 0x7c
  };
  private static final byte[] PACKET_ACK = new byte[] {
      (byte) 0xff
  };

  private static final byte[] PACKET_OFF = new byte[] {
      0x2e, (byte) 0x8d, 0x04, 0x00, 0x00, 0x00, 0x00, 0x6e
  };
  private static final byte[] PACKET_RED = new byte[] {
      0x2e, (byte) 0x8d, 0x08, 0x01, 0x08, (byte) 0xff, 0x00, 0x00,
      (byte) 0xff, (byte) 0xeb, (byte) 0xcd, (byte) 0xab
  };
  private static final byte[] PACKET_RESTORE = new byte[] {
      0x2e, (byte) 0x8d, 0x08, 0x01, 0x08, (byte) 0xff, (byte) 0xff,
      (byte) 0xff, (byte) 0xff, (byte) 0xeb, (byte) 0xcd, (byte) 0xad
  };

  private static AmbientLightController sInstance;

  private final Context mContext;
  private final PowerManager.WakeLock mCpuWakeLock;
  private final Handler mHandler = new Handler(Looper.getMainLooper());
  private final ArrayDeque<byte[]> mQueue = new ArrayDeque<byte[]>();
  private final Set<String> mSeenScanDevices = new HashSet<String>();

  private final BluetoothGattCallback mGattCallback = new BluetoothGattCallback() {
    @Override
    public void onConnectionStateChange(BluetoothGatt gatt, int status, int newState) {
      if (gatt != mGatt) {
        Log.i(TAG, "ignoring stale ambient gatt callback status=" + status + " state=" + newState);
        try {
          gatt.close();
        } catch (Exception ignored) {
        }
        return;
      }
      mConnecting = false;
      mHandler.removeCallbacks(mConnectTimeoutRunnable);
      if (newState == BluetoothProfile.STATE_CONNECTED) {
        Log.i(TAG, "ambient gatt connected");
        mSkipRememberedOnce = false;
        mConnected = true;
        mReconnectScheduled = false;
        mHandler.removeCallbacks(mReconnectRunnable);
        mGatt = gatt;
        gatt.discoverServices();
      } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
        Log.i(TAG, "ambient gatt disconnected status=" + status);
        mConnected = false;
        mWriting = false;
        mHandler.removeCallbacks(mWritePaceRunnable);
        mHandler.removeCallbacks(mWriteTimeoutRunnable);
        mHandler.removeCallbacks(mFlushAfterAckRunnable);
        mHandler.removeCallbacks(mBrightnessSyncRunnable);
        mWriteCharacteristic = null;
        mNotifyCharacteristic = null;
        mNotifyReady = false;
        mStartQueued = false;
        closeGatt();
        scheduleReconnect(status == 133 ? GATT_ERROR_RETRY_MS : CONNECT_RETRY_MS);
      }
    }

    @Override
    public void onServicesDiscovered(BluetoothGatt gatt, int status) {
      mWriteCharacteristic = findWriteCharacteristic(gatt);
      mNotifyCharacteristic = findNotifyCharacteristic(gatt);
      mNotifyReady = false;
      mStartQueued = false;
      Log.i(TAG, "ambient services status=" + status + " write=" + (mWriteCharacteristic != null)
          + " notify=" + (mNotifyCharacteristic != null));
      if (mWriteCharacteristic != null) {
        configureWriteCharacteristic(mWriteCharacteristic);
        queueStartPacket();
      }
      restoreActiveStateAfterConnect();
      if (enableNotifications(gatt, mNotifyCharacteristic)) {
        return;
      }
      mNotifyReady = true;
      flushNext();
    }

    @Override
    public void onCharacteristicWrite(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic, int status) {
      Log.i(TAG, "ambient write status=" + status);
      if (characteristic != null
          && characteristic.getWriteType() == BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE) {
        return;
      }
      mHandler.removeCallbacks(mWriteTimeoutRunnable);
      mHandler.removeCallbacks(mWritePaceRunnable);
      mWriting = false;
      flushNext();
    }

    @Override
    public void onDescriptorWrite(BluetoothGatt gatt, BluetoothGattDescriptor descriptor, int status) {
      Log.i(TAG, "ambient notify descriptor status=" + status);
      mNotifyReady = true;
      flushNext();
    }

    @Override
    public void onCharacteristicChanged(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic) {
      byte[] value = characteristic.getValue();
      if (value == null || value.length == 0) {
        return;
      }
      Log.i(TAG, "ambient notify " + bytesToHex(value));
      if (value[0] == 0x2e) {
        mHandler.removeCallbacks(mWriteTimeoutRunnable);
        mHandler.removeCallbacks(mWritePaceRunnable);
        mWriting = true;
        writeAck();
        mHandler.removeCallbacks(mFlushAfterAckRunnable);
        mHandler.postDelayed(mFlushAfterAckRunnable, readAckSettleIntervalMs());
      }
    }
  };

  private final BluetoothAdapter.LeScanCallback mScanCallback = new BluetoothAdapter.LeScanCallback() {
    @Override
    public void onLeScan(BluetoothDevice device, int rssi, byte[] scanRecord) {
      if (device == null) {
        return;
      }
      if (!matchesAmbientDevice(device, scanRecord)) {
        logSeenScanDevice(device, rssi);
        return;
      }
      Log.i(TAG, "ambient candidate " + safeName(device) + " " + device.getAddress());
      stopScan();
      connectDevice(device);
    }
  };

  private final Runnable mStopScanRunnable = new Runnable() {
    @Override
    public void run() {
      stopScan();
      scheduleReconnect();
    }
  };

  private final Runnable mReconnectRunnable = new Runnable() {
    @Override
    public void run() {
      mReconnectScheduled = false;
      connectIfNeeded();
    }
  };

  private final Runnable mConnectTimeoutRunnable = new Runnable() {
    @Override
    public void run() {
      if (!mConnecting || mConnected) {
        return;
      }
      Log.w(TAG, "ambient direct connection timed out; falling back to scan");
      closeGatt();
      scheduleReconnect(0L);
    }
  };

  private final Runnable mOverspeedStateRunnable = new Runnable() {
    @Override
    public void run() {
      if (mRequestedOverspeed != mOverspeedActive) {
        setOverspeed(mRequestedOverspeed);
      }
    }
  };

  private final Runnable mBlinkRunnable = new Runnable() {
    @Override
    public void run() {
      if (!mOverspeedActive || mReverseActive) {
        return;
      }
      int brightness = readAmbientBrightness();
      if (brightness < MIN_FADE_AMBIENT_BRIGHTNESS) {
        if (!mWarningAnimationStarted || !mLowLightWarning) {
          sendPacket(warningColorPacket());
          sendPacket(buildBrightnessPacket(true, brightness, warningZone2Brightness()));
          mWarningAnimationStarted = true;
          mLowLightWarning = true;
          mDayWarningDimmed = false;
        } else if (mLastAmbientBrightness < 0
            || Math.abs(brightness - mLastAmbientBrightness) >= BRIGHTNESS_UPDATE_DELTA) {
          sendPacket(buildBrightnessPacket(true, brightness, warningZone2Brightness()));
        }
        mLastAmbientBrightness = brightness;
        mHandler.postDelayed(this, LOW_LIGHT_CHECK_INTERVAL_MS);
        return;
      }

      if (!mWarningAnimationStarted) {
        sendPacket(warningColorPacket());
        mWarningAnimationStarted = true;
        mLowLightWarning = false;
        mDayWarningDimmed = false;
      } else if (mLowLightWarning) {
        mLowLightWarning = false;
        mDayWarningDimmed = false;
      }

      int dimLevel = Math.max(1,
          ((brightness * DAY_WARNING_DIM_PERCENT) + 50) / 100);
      int zone1Level = mDayWarningDimmed ? dimLevel : brightness;
      sendPacket(buildBrightnessPacket(true, zone1Level, warningZone2Brightness()));
      mLastAmbientBrightness = brightness;
      mDayWarningDimmed = !mDayWarningDimmed;
      mHandler.postDelayed(this, DAY_WARNING_STEP_INTERVAL_MS);
    }
  };

  private final Runnable mWriteTimeoutRunnable = new Runnable() {
    @Override
    public void run() {
      if (!mWriting) {
        return;
      }
      Log.w(TAG, "ambient write timeout");
      mHandler.removeCallbacks(mWritePaceRunnable);
      mWriting = false;
      flushNext();
    }
  };

  private final Runnable mWritePaceRunnable = new Runnable() {
    @Override
    public void run() {
      if (!mWriting) {
        return;
      }
      mHandler.removeCallbacks(mWriteTimeoutRunnable);
      mWriting = false;
      flushNext();
    }
  };

  private final Runnable mFlushAfterAckRunnable = new Runnable() {
    @Override
    public void run() {
      mWriting = false;
      flushNext();
    }
  };

  private final Runnable mBrightnessSyncRunnable = new Runnable() {
    @Override
    public void run() {
      if (!mAmbientActive || mReverseActive) {
        return;
      }
      syncAmbientBrightness(false);
      mHandler.postDelayed(this, BRIGHTNESS_SYNC_INTERVAL_MS);
    }
  };

  private final Runnable mAmbientFadeRunnable = new Runnable() {
    @Override
    public void run() {
      if (mReverseActive) {
        return;
      }
      long elapsedMs = SystemClock.elapsedRealtime() - mAmbientFadeStartedAtMs;
      float progress = mAmbientFadeDurationMs > 0L
          ? Math.min(1.0f, (float) elapsedMs / (float) mAmbientFadeDurationMs) : 1.0f;
      float eased = progress * progress * (3.0f - (2.0f * progress));
      int zone1 = Math.round(mAmbientFadeStartZone1
          + ((mAmbientTargetZone1 - mAmbientFadeStartZone1) * eased));
      int zone2 = Math.round(mAmbientFadeStartZone2
          + ((mAmbientTargetZone2 - mAmbientFadeStartZone2) * eased));
      int zone1Red = interpolate(mAmbientFadeStartZone1Red, mAmbientTargetZone1Red, eased);
      int zone1Green = interpolate(mAmbientFadeStartZone1Green, mAmbientTargetZone1Green, eased);
      int zone1Blue = interpolate(mAmbientFadeStartZone1Blue, mAmbientTargetZone1Blue, eased);
      int zone2Red = interpolate(mAmbientFadeStartZone2Red, mAmbientTargetZone2Red, eased);
      int zone2Green = interpolate(mAmbientFadeStartZone2Green, mAmbientTargetZone2Green, eased);
      int zone2Blue = interpolate(mAmbientFadeStartZone2Blue, mAmbientTargetZone2Blue, eased);
      applyAmbientFrame(zone1, zone2,
          zone1Red, zone1Green, zone1Blue,
          zone2Red, zone2Green, zone2Blue,
          progress >= 1.0f);
      if (progress < 1.0f) {
        mHandler.postDelayed(this, readAmbientFrameStepMs());
      }
    }
  };

  private final Runnable mOffroadDelayedOffRunnable = new Runnable() {
    @Override
    public void run() {
      if (!mOnroad && !mDoorOpen) {
        mExitCourtesyActive = false;
        if (mManualOverrideActive) {
          startAmbientFade(normalZone1Brightness(), normalZone2Brightness(), profileFadeMs());
        } else {
          startAmbientFade(0, 0, profileFadeMs());
        }
      }
    }
  };

  private final Runnable mOffroadDoorMaxRunnable = new Runnable() {
    @Override
    public void run() {
      if (!mOnroad && mDoorOpen) {
        mOffroadDoorMaxExpired = true;
        mExitCourtesyActive = false;
        hardAmbientOff("offroad door max-on timeout");
      }
    }
  };

  private final Runnable mOffroadDoorCloseRunnable = new Runnable() {
    @Override
    public void run() {
      if (!mOnroad && !mDoorOpen && !mReverseActive) {
        mExitCourtesyActive = false;
        if (mManualOverrideActive) {
          startAmbientFade(normalZone1Brightness(), normalZone2Brightness(), profileFadeMs());
        } else {
          startAmbientFade(0, 0, profileFadeMs());
        }
      }
    }
  };

  private final Runnable mManualOverrideExpiryRunnable = new Runnable() {
    @Override
    public void run() {
      if (mManualOverrideActive && System.currentTimeMillis() >= mManualOverrideExpiresAtMs) {
        clearManualOverride("expired");
      }
    }
  };

  private final Runnable mVehicleDataWatchdogRunnable = new Runnable() {
    @Override
    public void run() {
      long ageMs = SystemClock.elapsedRealtime() - mLastVehicleDataAtMs;
      if (ageMs < VEHICLE_DATA_TIMEOUT_MS) {
        mHandler.postDelayed(this, VEHICLE_DATA_TIMEOUT_MS - ageMs);
        return;
      }
      Log.w(TAG, "comma vehicle data timeout; fading ambient off");
      mVehicleDataTimedOut = true;
      mVehicleStateKnown = false;
      mOnroad = false;
      mDoorOpen = false;
      mRequestedOverspeed = false;
      mHandler.removeCallbacks(mOverspeedStateRunnable);
      mOverspeedActive = false;
      mOverspeedActivatedAtMs = 0L;
      stopBlink();
      stopBrightnessSync();
      cancelOffroadTimers();
      updateCpuWakeLock();
      if (mReverseActive) {
        hardAmbientOff("comma data timeout in reverse");
      } else {
        startAmbientFade(0, 0, AMBIENT_NORMAL_FADE_MS);
      }
    }
  };

  private BluetoothAdapter mAdapter;
  private BluetoothGatt mGatt;
  private BluetoothGattCharacteristic mWriteCharacteristic;
  private BluetoothGattCharacteristic mNotifyCharacteristic;
  private boolean mConnected;
  private boolean mConnecting;
  private boolean mSkipRememberedOnce;
  private boolean mScanning;
  private boolean mReconnectScheduled;
  private boolean mWriting;
  private boolean mNotifyReady;
  private boolean mStartQueued;
  private boolean mReverseActive;
  private boolean mOverspeedActive;
  private boolean mRequestedOverspeed;
  private long mOverspeedActivatedAtMs;
  private boolean mAmbientActive;
  private boolean mWarningAnimationStarted;
  private boolean mLowLightWarning;
  private boolean mDayWarningDimmed;
  private boolean mVehicleStateKnown;
  private boolean mVehicleDataTimedOut;
  private boolean mOnroad;
  private boolean mDoorOpen;
  private boolean mOffroadDoorMaxExpired;
  private long mLastVehicleDataAtMs;
  private int mCurrentZone1;
  private int mCurrentZone2;
  private int mAmbientFadeStartZone1;
  private int mAmbientFadeStartZone2;
  private int mAmbientTargetZone1;
  private int mAmbientTargetZone2;
  private int mCurrentZone1Red = 255;
  private int mCurrentZone1Green = 255;
  private int mCurrentZone1Blue = 255;
  private int mCurrentZone2Red = 255;
  private int mCurrentZone2Green = 255;
  private int mCurrentZone2Blue = 255;
  private int mAmbientFadeStartZone1Red;
  private int mAmbientFadeStartZone1Green;
  private int mAmbientFadeStartZone1Blue;
  private int mAmbientFadeStartZone2Red;
  private int mAmbientFadeStartZone2Green;
  private int mAmbientFadeStartZone2Blue;
  private int mAmbientTargetZone1Red;
  private int mAmbientTargetZone1Green;
  private int mAmbientTargetZone1Blue;
  private int mAmbientTargetZone2Red;
  private int mAmbientTargetZone2Green;
  private int mAmbientTargetZone2Blue;
  private long mAmbientFadeStartedAtMs;
  private long mAmbientFadeDurationMs;
  private int mLastAmbientBrightness = -1;
  private String mLastGear = "";
  private boolean mExitCourtesyActive;
  private boolean mManualOverrideActive;
  private long mManualOverrideExpiresAtMs;
  private String mManualOverrideId = "";
  private boolean mManualZone1Enabled = true;
  private boolean mManualZone2Enabled = true;
  private int mManualZone1Red = 255;
  private int mManualZone1Green = 255;
  private int mManualZone1Blue = 255;
  private int mManualZone2Red = 255;
  private int mManualZone2Green = 255;
  private int mManualZone2Blue = 255;
  private int mManualZone1Brightness = 20;
  private int mManualZone2Brightness = 40;
  private JSONObject mProfile = new JSONObject();

  private AmbientLightController(Context context) {
    mContext = context.getApplicationContext();
    loadAmbientProfile();
    PowerManager powerManager = (PowerManager) mContext.getSystemService(Context.POWER_SERVICE);
    mCpuWakeLock = powerManager == null ? null
        : powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "NavdyAmbient:OffroadController");
    if (mCpuWakeLock != null) {
      mCpuWakeLock.setReferenceCounted(false);
    }
    mLastVehicleDataAtMs = SystemClock.elapsedRealtime();
    mHandler.postDelayed(mVehicleDataWatchdogRunnable, VEHICLE_DATA_TIMEOUT_MS);
  }

  public static synchronized AmbientLightController get(Context context) {
    if (sInstance == null) {
      sInstance = new AmbientLightController(context);
    }
    return sInstance;
  }

  public static void onOpenpilotPayload(Context context, String payload) {
    if (context == null || payload == null) {
      return;
    }
    try {
      final JSONObject json = new JSONObject(payload);
      final String gear = json.optString("gear", json.optString("gearShifter", ""));
      final boolean hasOnroad = json.has("onroad");
      final boolean hasDoorOpen = json.has("doorOpen");
      final boolean onroad = json.optBoolean("onroad", true);
      final boolean doorOpen = json.optBoolean("doorOpen", false);
      final JSONObject ambientOverride = json.optJSONObject("ambientOverride");
      final AmbientLightController controller = get(context);
      controller.mHandler.post(new Runnable() {
        @Override
        public void run() {
          controller.noteVehicleDataReceived();
          if (gear != null && gear.length() > 0) {
            controller.setGearText(gear);
          }
          if (hasOnroad || hasDoorOpen) {
            boolean nextOnroad = hasOnroad ? onroad
                : (controller.mVehicleStateKnown ? controller.mOnroad : true);
            boolean nextDoorOpen = hasDoorOpen ? doorOpen
                : (controller.mVehicleStateKnown ? controller.mDoorOpen : false);
            controller.setVehicleState(nextOnroad, nextDoorOpen);
          }
          if (ambientOverride != null) {
            controller.setAmbientOverride(ambientOverride);
          }
        }
      });
    } catch (Exception e) {
      Log.w(TAG, "bad openpilot payload", e);
    }
  }

  public static void onOpenpilotPayload(Context context, JSONObject payload) {
    if (payload != null) {
      onOpenpilotPayload(context, payload.toString());
    }
  }

  public static void onGearText(final Context context, final String gear) {
    if (context == null || gear == null) {
      return;
    }
    final AmbientLightController controller = get(context);
    controller.mHandler.post(new Runnable() {
      @Override
      public void run() {
        controller.setGearText(gear);
      }
    });
  }

  public static void onOverspeedChanged(final Context context, final boolean overspeed) {
    if (context == null) {
      return;
    }
    final AmbientLightController controller = get(context);
    controller.mHandler.post(new Runnable() {
      @Override
      public void run() {
        controller.requestOverspeed(overspeed);
      }
    });
  }

  public static void onCameraSpeedChanged(final Context context, final int speed, final int limit) {
    if (context == null) {
      return;
    }
    final AmbientLightController controller = get(context);
    controller.mHandler.post(new Runnable() {
      @Override
      public void run() {
        controller.requestCameraSpeed(speed, limit);
      }
    });
  }

  private void requestCameraSpeed(int speed, int limit) {
    if (limit <= 0 || speed <= limit) {
      requestOverspeed(false);
    } else if (speed >= limit + 2) {
      requestOverspeed(true);
    } else {
      // In the +1 km/h deadband, retain the active state and cancel a pending transition.
      requestOverspeed(mOverspeedActive);
    }
  }

  private static long parseIsoTimeMs(String value) {
    if (value == null || value.length() == 0) {
      return 0L;
    }
    String[] formats = new String[] {
        "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'",
        "yyyy-MM-dd'T'HH:mm:ss'Z'"
    };
    for (String format : formats) {
      try {
        SimpleDateFormat parser = new SimpleDateFormat(format, Locale.US);
        parser.setTimeZone(TimeZone.getTimeZone("UTC"));
        Date parsed = parser.parse(value);
        if (parsed != null) {
          return parsed.getTime();
        }
      } catch (Exception ignored) {
      }
    }
    return 0L;
  }

  private static int zoneValue(JSONObject zone, String name, int fallback, int maximum) {
    return zone == null ? fallback : clamp(zone.optInt(name, fallback), 0, maximum);
  }

  private static int colorValue(JSONObject zone, int index, int fallback) {
    if (zone == null || zone.optJSONArray("rgb") == null) {
      return fallback;
    }
    return clamp(zone.optJSONArray("rgb").optInt(index, fallback), 0, 255);
  }

  private void loadAmbientProfile() {
    String stored = Settings.System.getString(
        mContext.getContentResolver(), AMBIENT_PROFILE_SETTING);
    if (stored == null || stored.length() == 0) {
      mProfile = new JSONObject();
      return;
    }
    try {
      mProfile = new JSONObject(stored);
    } catch (Exception e) {
      Log.w(TAG, "bad stored ambient profile", e);
      mProfile = new JSONObject();
    }
  }

  private void setAmbientProfile(JSONObject profile) {
    if (profile == null) {
      return;
    }
    if (profile.toString().equals(mProfile.toString()) && !mManualOverrideActive) {
      return;
    }
    mProfile = profile;
    Settings.System.putString(
        mContext.getContentResolver(), AMBIENT_PROFILE_SETTING, profile.toString());
    mManualOverrideActive = false;
    mManualOverrideExpiresAtMs = 0L;
    mManualOverrideId = "";
    mHandler.removeCallbacks(mManualOverrideExpiryRunnable);
    Log.i(TAG, "ambient profile saved");
    if (!profileMasterEnabled()) {
      hardAmbientOff("profile disabled");
    } else if (!mReverseActive) {
      applyVehicleStateTargets();
    }
  }

  private JSONObject profileSection(String name) {
    JSONObject section = mProfile.optJSONObject(name);
    return section == null ? new JSONObject() : section;
  }

  private JSONObject profileZone(String section, String zone) {
    JSONObject value = profileSection(section).optJSONObject(zone);
    return value == null ? new JSONObject() : value;
  }

  private boolean profileMasterEnabled() {
    return mProfile.optBoolean("enabled", true);
  }

  private boolean profileFeatureEnabled(String name, boolean fallback) {
    return profileSection(name).optBoolean("enabled", fallback);
  }

  private int profileBrightness(String section, String zone, int fallback) {
    return zoneValue(profileZone(section, zone), "brightness", fallback, 100);
  }

  private long profileTimingMs(String name, long fallback, long minimum, long maximum) {
    return Math.max(minimum,
        Math.min(maximum, profileSection("timing").optLong(name, fallback)));
  }

  private long profileFadeMs() {
    return profileTimingMs("fadeMilliseconds", AMBIENT_NORMAL_FADE_MS, 200L, 5000L);
  }

  private long profileDoorCloseDelayMs() {
    return profileTimingMs("doorCloseDelaySeconds", 20L, 0L, 120L) * 1000L;
  }

  private long profileDoorMaxOnMs() {
    return profileTimingMs("doorMaxOnMinutes", 20L, 1L, 60L) * 60000L;
  }

  private long profileExitCourtesyMs() {
    return Math.max(0L,
        Math.min(600L, profileSection("exitCourtesy").optLong("durationSeconds", 120L))) * 1000L;
  }

  private byte[] profileColorPacket(String zone1Section, String zone1Name,
                                    String zone2Section, String zone2Name) {
    JSONObject zone1 = profileZone(zone1Section, zone1Name);
    JSONObject zone2 = profileZone(zone2Section, zone2Name);
    return buildColorPacket(
        colorValue(zone1, 0, 255), colorValue(zone1, 1, 255), colorValue(zone1, 2, 255),
        colorValue(zone2, 0, 255), colorValue(zone2, 1, 255), colorValue(zone2, 2, 255));
  }

  private byte[] drivingColorPacket() {
    return profileColorPacket("driving", "zone1", "driving", "zone2");
  }

  private byte[] onroadDoorColorPacket() {
    return profileColorPacket("onroadDoor", "zone1", "onroadDoor", "zone2");
  }

  private byte[] offroadDoorColorPacket() {
    return profileColorPacket("offroadDoor", "zone1", "offroadDoor", "zone2");
  }

  private byte[] exitCourtesyColorPacket() {
    return profileColorPacket("driving", "zone1", "exitCourtesy", "zone2");
  }

  private byte[] activeStateColorPacket() {
    if (mManualOverrideActive) {
      return normalColorPacket();
    }
    if (mExitCourtesyActive) {
      return exitCourtesyColorPacket();
    }
    if (!mOnroad && mDoorOpen && profileFeatureEnabled("offroadDoor", true)) {
      return offroadDoorColorPacket();
    }
    if (mOnroad && mDoorOpen && profileFeatureEnabled("onroadDoor", true)) {
      return onroadDoorColorPacket();
    }
    return drivingColorPacket();
  }

  private void setAmbientOverride(JSONObject command) {
    String mode = command.optString("mode", "manual");
    if ("profile".equalsIgnoreCase(mode)) {
      setAmbientProfile(command.optJSONObject("profile"));
      return;
    }
    if ("auto".equalsIgnoreCase(mode)) {
      clearManualOverride("auto command");
      return;
    }
    if (!"manual".equalsIgnoreCase(mode)) {
      return;
    }
    String id = command.optString("id", "");
    if (mManualOverrideActive && id.length() > 0 && id.equals(mManualOverrideId)) {
      return;
    }
    long now = System.currentTimeMillis();
    long expiresAt = parseIsoTimeMs(command.optString("expiresAt", ""));
    if (expiresAt <= now) {
      clearManualOverride("stale command");
      return;
    }
    JSONObject zone1 = command.optJSONObject("zone1");
    JSONObject zone2 = command.optJSONObject("zone2");
    if (zone1 == null || zone2 == null) {
      return;
    }
    mManualOverrideId = id;
    mManualZone1Enabled = zone1.optBoolean("enabled", true);
    mManualZone2Enabled = zone2.optBoolean("enabled", true);
    mManualZone1Red = colorValue(zone1, 0, 255);
    mManualZone1Green = colorValue(zone1, 1, 255);
    mManualZone1Blue = colorValue(zone1, 2, 255);
    mManualZone2Red = colorValue(zone2, 0, 255);
    mManualZone2Green = colorValue(zone2, 1, 255);
    mManualZone2Blue = colorValue(zone2, 2, 255);
    mManualZone1Brightness = zoneValue(zone1, "brightness", 20, 100);
    mManualZone2Brightness = zoneValue(zone2, "brightness", 40, 100);
    mManualOverrideExpiresAtMs = Math.min(expiresAt, now + MANUAL_OVERRIDE_MAX_MS);
    mManualOverrideActive = true;
    cancelOffroadTimers();
    mHandler.removeCallbacks(mManualOverrideExpiryRunnable);
    mHandler.postDelayed(mManualOverrideExpiryRunnable,
        Math.max(1L, mManualOverrideExpiresAtMs - now));
    Log.i(TAG, "manual ambient override id=" + id);
    if (!mReverseActive) {
      applyVehicleStateTargets();
    }
  }

  private void clearManualOverride(String reason) {
    if (!mManualOverrideActive && mManualOverrideId.length() == 0) {
      return;
    }
    Log.i(TAG, "manual ambient override cleared reason=" + reason);
    mManualOverrideActive = false;
    mManualOverrideExpiresAtMs = 0L;
    mManualOverrideId = "";
    mHandler.removeCallbacks(mManualOverrideExpiryRunnable);
    if (mReverseActive) {
      hardAmbientOff("reverse");
    } else if (!mOnroad && !mDoorOpen) {
      startAmbientFade(0, 0, profileFadeMs());
    } else {
      applyVehicleStateTargets();
    }
  }

  private void requestOverspeed(boolean overspeed) {
    if (!profileMasterEnabled() || !profileFeatureEnabled("overspeed", true)
        || !mVehicleStateKnown || mVehicleDataTimedOut || !mOnroad || mReverseActive) {
      overspeed = false;
    }
    if (mRequestedOverspeed == overspeed) {
      return;
    }
    mRequestedOverspeed = overspeed;
    mHandler.removeCallbacks(mOverspeedStateRunnable);
    if (mOverspeedActive == overspeed) {
      return;
    }

    long delayMs = overspeed ? OVERSPEED_ON_DELAY_MS : OVERSPEED_OFF_DELAY_MS;
    if (!overspeed && mOverspeedActivatedAtMs > 0L) {
      long activeForMs = SystemClock.elapsedRealtime() - mOverspeedActivatedAtMs;
      delayMs = Math.max(delayMs, OVERSPEED_MIN_ACTIVE_MS - activeForMs);
    }
    Log.i(TAG, "camera overspeed requested=" + overspeed + " delayMs=" + Math.max(0L, delayMs));
    mHandler.postDelayed(mOverspeedStateRunnable, Math.max(0L, delayMs));
  }

  private void setGearText(String gear) {
    String normalized = normalizeGear(gear);
    if (normalized.equals(mLastGear)) {
      return;
    }
    mLastGear = normalized;
    Log.i(TAG, "gear=" + normalized);

    if (isReverse(normalized)) {
      mReverseActive = profileFeatureEnabled("reverseOff", true);
      if (!mReverseActive) {
        return;
      }
      stopBlink();
      stopBrightnessSync();
      hardAmbientOff("reverse");
      return;
    }

    if (isDriveGear(normalized)) {
      boolean wasReverse = mReverseActive;
      mReverseActive = false;
      if (wasReverse) {
        if (mVehicleStateKnown && mOnroad) {
          startBrightnessSync();
        } else {
          applyVehicleStateTargets();
        }
      } else if (!mVehicleStateKnown) {
        mOnroad = true;
        mAmbientActive = true;
        startBrightnessSync();
        startAmbientFade(normalZone1Brightness(), normalZone2Brightness(), profileFadeMs());
      }
    }
  }

  private void noteVehicleDataReceived() {
    mLastVehicleDataAtMs = SystemClock.elapsedRealtime();
    mVehicleDataTimedOut = false;
    mHandler.removeCallbacks(mVehicleDataWatchdogRunnable);
    mHandler.postDelayed(mVehicleDataWatchdogRunnable, VEHICLE_DATA_TIMEOUT_MS);
  }

  private void setVehicleState(boolean onroad, boolean doorOpen) {
    boolean firstState = !mVehicleStateKnown;
    boolean onroadChanged = firstState || mOnroad != onroad;
    boolean doorChanged = firstState || mDoorOpen != doorOpen;
    mVehicleStateKnown = true;
    mVehicleDataTimedOut = false;
    mOnroad = onroad;
    mDoorOpen = doorOpen;
    updateCpuWakeLock();
    if (onroadChanged || doorChanged) {
      Log.i(TAG, "vehicle state onroad=" + onroad + " doorOpen=" + doorOpen);
    }

    if (!profileMasterEnabled() && !mManualOverrideActive) {
      cancelOffroadTimers();
      hardAmbientOff("profile disabled");
      return;
    }

    if (onroad) {
      mExitCourtesyActive = false;
      cancelOffroadTimers();
      mOffroadDoorMaxExpired = false;
      if (onroadChanged) {
        startBrightnessSync();
      } else if (doorChanged) {
        applyVehicleStateTargets();
      }
      return;
    }

    stopBrightnessSync();
    mRequestedOverspeed = false;
    mHandler.removeCallbacks(mOverspeedStateRunnable);
    if (mOverspeedActive) {
      setOverspeed(false);
    }

    if (doorOpen) {
      mExitCourtesyActive = false;
      mHandler.removeCallbacks(mOffroadDelayedOffRunnable);
      mHandler.removeCallbacks(mOffroadDoorCloseRunnable);
      if (!profileFeatureEnabled("offroadDoor", true) && !mManualOverrideActive) {
        hardAmbientOff("offroad door profile disabled");
        return;
      }
      if (doorChanged || onroadChanged) {
        mOffroadDoorMaxExpired = false;
        mHandler.removeCallbacks(mOffroadDoorMaxRunnable);
        mHandler.postDelayed(mOffroadDoorMaxRunnable, profileDoorMaxOnMs());
      }
      if (!mOffroadDoorMaxExpired && (doorChanged || onroadChanged)) {
        startAmbientFade(offroadDoorZone1Brightness(),
            offroadDoorZone2Brightness(), profileFadeMs());
      }
      return;
    }

    if (mManualOverrideActive) {
      cancelOffroadTimers();
      startAmbientFade(normalZone1Brightness(), normalZone2Brightness(), profileFadeMs());
      return;
    }

    mHandler.removeCallbacks(mOffroadDoorMaxRunnable);
    mOffroadDoorMaxExpired = false;
    if (doorChanged && !firstState) {
      mHandler.removeCallbacks(mOffroadDelayedOffRunnable);
      mHandler.removeCallbacks(mOffroadDoorCloseRunnable);
      mHandler.postDelayed(mOffroadDoorCloseRunnable, profileDoorCloseDelayMs());
    } else if (!firstState && onroadChanged) {
      mHandler.removeCallbacks(mOffroadDelayedOffRunnable);
      mHandler.removeCallbacks(mOffroadDoorCloseRunnable);
      if (profileFeatureEnabled("exitCourtesy", true) && profileExitCourtesyMs() > 0L) {
        mExitCourtesyActive = true;
        startAmbientFade(mCurrentZone1, exitCourtesyZone2Brightness(), profileFadeMs());
        mHandler.postDelayed(mOffroadDelayedOffRunnable, profileExitCourtesyMs());
      } else {
        mExitCourtesyActive = false;
        startAmbientFade(0, 0, profileFadeMs());
      }
    } else if (firstState) {
      mHandler.removeCallbacks(mOffroadDelayedOffRunnable);
      mHandler.removeCallbacks(mOffroadDoorCloseRunnable);
      mHandler.postDelayed(mOffroadDelayedOffRunnable, OFFROAD_DELAYED_OFF_MS);
    }
  }

  private void updateCpuWakeLock() {
    if (mCpuWakeLock == null) {
      return;
    }
    boolean shouldHold = mVehicleStateKnown && !mVehicleDataTimedOut && !mOnroad;
    if (shouldHold && !mCpuWakeLock.isHeld()) {
      mCpuWakeLock.acquire();
      Log.i(TAG, "offroad ambient CPU wake lock acquired");
    } else if (!shouldHold && mCpuWakeLock.isHeld()) {
      mCpuWakeLock.release();
      Log.i(TAG, "offroad ambient CPU wake lock released");
    }
  }

  private void applyVehicleStateTargets() {
    if (!profileMasterEnabled() && !mManualOverrideActive) {
      hardAmbientOff("profile disabled");
    } else if (mReverseActive || mVehicleDataTimedOut) {
      hardAmbientOff(mReverseActive ? "reverse" : "comma data timeout");
    } else if (mOnroad) {
      mExitCourtesyActive = false;
      startAmbientFade(activeOnroadZone1Brightness(),
          activeOnroadZone2Brightness(),
          profileFadeMs());
    } else if (mDoorOpen && !mOffroadDoorMaxExpired) {
      if (profileFeatureEnabled("offroadDoor", true) || mManualOverrideActive) {
        startAmbientFade(offroadDoorZone1Brightness(),
            offroadDoorZone2Brightness(), profileFadeMs());
      } else {
        hardAmbientOff("offroad door profile disabled");
      }
    } else if (mManualOverrideActive) {
      startAmbientFade(normalZone1Brightness(), normalZone2Brightness(), profileFadeMs());
    }
  }

  private void cancelOffroadTimers() {
    mHandler.removeCallbacks(mOffroadDelayedOffRunnable);
    mHandler.removeCallbacks(mOffroadDoorMaxRunnable);
    mHandler.removeCallbacks(mOffroadDoorCloseRunnable);
  }

  private void setOverspeed(boolean overspeed) {
    if (mOverspeedActive == overspeed) {
      return;
    }
    mOverspeedActive = overspeed;
    mOverspeedActivatedAtMs = overspeed ? SystemClock.elapsedRealtime() : 0L;
    Log.i(TAG, "camera overspeed=" + overspeed);
    if (overspeed) {
      if (mOnroad && !mReverseActive && !mVehicleDataTimedOut) {
        startBlink();
      }
    } else {
      if (!mReverseActive) {
        beginRestoreFade();
      } else {
        stopBlink();
      }
    }
  }

  private void startBlink() {
    if (!mOnroad || mReverseActive || mVehicleDataTimedOut) {
      return;
    }
    stopBlink();
    mAmbientActive = true;
    startBrightnessSync();
    mHandler.post(mBlinkRunnable);
  }

  private void stopBlink() {
    mHandler.removeCallbacks(mBlinkRunnable);
    mWarningAnimationStarted = false;
    mLowLightWarning = false;
    mDayWarningDimmed = false;
  }

  private void beginRestoreFade() {
    mHandler.removeCallbacks(mBlinkRunnable);
    if (!mOnroad || mReverseActive || mVehicleDataTimedOut) {
      stopBlink();
      return;
    }
    stopBlink();
    startAmbientFade(activeOnroadZone1Brightness(),
        activeOnroadZone2Brightness(),
        profileFadeMs());
  }

  private void startBrightnessSync() {
    mHandler.removeCallbacks(mBrightnessSyncRunnable);
    syncAmbientBrightness(true);
    mHandler.postDelayed(mBrightnessSyncRunnable, BRIGHTNESS_SYNC_INTERVAL_MS);
  }

  private void stopBrightnessSync() {
    mHandler.removeCallbacks(mBrightnessSyncRunnable);
    mLastAmbientBrightness = -1;
  }

  private void syncAmbientBrightness(boolean force) {
    if (!mOnroad || mReverseActive || mVehicleDataTimedOut) {
      return;
    }
    int brightness = activeOnroadZone1Brightness();
    if (mWarningAnimationStarted) {
      mLastAmbientBrightness = brightness;
      return;
    }
    if (!force && mLastAmbientBrightness >= 0
        && Math.abs(brightness - mLastAmbientBrightness) < BRIGHTNESS_UPDATE_DELTA) {
      return;
    }
    mLastAmbientBrightness = brightness;
    Log.i(TAG, "ambient brightness=" + brightness + " screen=" + readScreenBrightness());
    int zone2Brightness = activeOnroadZone2Brightness();
    if (force || brightness != mAmbientTargetZone1 || zone2Brightness != mAmbientTargetZone2) {
      startAmbientFade(brightness, zone2Brightness, AMBIENT_NORMAL_FADE_MS);
    }
  }

  private void startAmbientFade(int zone1, int zone2, long durationMs) {
    mHandler.removeCallbacks(mAmbientFadeRunnable);
    removePendingAmbientStatePackets();
    mAmbientFadeStartZone1 = mCurrentZone1;
    mAmbientFadeStartZone2 = mCurrentZone2;
    mAmbientFadeStartZone1Red = mCurrentZone1Red;
    mAmbientFadeStartZone1Green = mCurrentZone1Green;
    mAmbientFadeStartZone1Blue = mCurrentZone1Blue;
    mAmbientFadeStartZone2Red = mCurrentZone2Red;
    mAmbientFadeStartZone2Green = mCurrentZone2Green;
    mAmbientFadeStartZone2Blue = mCurrentZone2Blue;
    mAmbientTargetZone1 = clamp(zone1, 0, 100);
    mAmbientTargetZone2 = clamp(zone2, 0, 100);
    byte[] targetColor = activeStateColorPacket();
    mAmbientTargetZone1Red = colorPacketValue(targetColor, 5, 255);
    mAmbientTargetZone1Green = colorPacketValue(targetColor, 6, 255);
    mAmbientTargetZone1Blue = colorPacketValue(targetColor, 7, 255);
    mAmbientTargetZone2Red = colorPacketValue(targetColor, 8, 255);
    mAmbientTargetZone2Green = colorPacketValue(targetColor, 9, 255);
    mAmbientTargetZone2Blue = colorPacketValue(targetColor, 10, 255);
    mAmbientFadeStartedAtMs = SystemClock.elapsedRealtime();
    mAmbientFadeDurationMs = Math.max(0L, durationMs);
    if (mAmbientTargetZone1 > 0 || mAmbientTargetZone2 > 0) {
      mAmbientActive = true;
    }
    long firstStepMs = Math.min(readAmbientFrameStepMs(), mAmbientFadeDurationMs);
    mHandler.postDelayed(mAmbientFadeRunnable, Math.max(0L, firstStepMs));
  }

  private void applyAmbientFrame(int zone1, int zone2,
                                 int zone1Red, int zone1Green, int zone1Blue,
                                 int zone2Red, int zone2Green, int zone2Blue,
                                 boolean finished) {
    mCurrentZone1 = clamp(zone1, 0, 100);
    mCurrentZone2 = clamp(zone2, 0, 100);
    mCurrentZone1Red = clamp(zone1Red, 0, 255);
    mCurrentZone1Green = clamp(zone1Green, 0, 255);
    mCurrentZone1Blue = clamp(zone1Blue, 0, 255);
    mCurrentZone2Red = clamp(zone2Red, 0, 255);
    mCurrentZone2Green = clamp(zone2Green, 0, 255);
    mCurrentZone2Blue = clamp(zone2Blue, 0, 255);
    if (finished && mCurrentZone1 == 0 && mCurrentZone2 == 0) {
      mAmbientActive = false;
      sendPacket(PACKET_OFF);
    } else {
      mAmbientActive = true;
      sendAmbientFrame(
          buildColorPacket(
              mCurrentZone1Red, mCurrentZone1Green, mCurrentZone1Blue,
              mCurrentZone2Red, mCurrentZone2Green, mCurrentZone2Blue),
          buildBrightnessPacket(true, mCurrentZone1, mCurrentZone2));
    }
  }

  private void sendAmbientFrame(byte[] colorPacket, byte[] brightnessPacket) {
    removePendingAmbientStatePackets();
    if (mQueue.size() > 18) {
      mQueue.poll();
    }
    mQueue.offer(colorPacket.clone());
    mQueue.offer(brightnessPacket.clone());
    connectIfNeeded();
    flushNext();
  }

  private void hardAmbientOff(String reason) {
    Log.i(TAG, "ambient off reason=" + reason);
    mHandler.removeCallbacks(mAmbientFadeRunnable);
    mCurrentZone1 = 0;
    mCurrentZone2 = 0;
    mAmbientTargetZone1 = 0;
    mAmbientTargetZone2 = 0;
    mAmbientActive = false;
    sendPacket(PACKET_OFF);
  }

  private int warningZone2Brightness() {
    return mDoorOpen && profileFeatureEnabled("onroadDoor", true)
        ? onroadDoorZone2Brightness() : normalZone2Brightness();
  }

  private int normalZone1Brightness() {
    if (mManualOverrideActive) {
      return mManualZone1Enabled ? mManualZone1Brightness : 0;
    }
    JSONObject zone = profileZone("driving", "zone1");
    if (!zone.optBoolean("automaticBrightness", true)) {
      return profileBrightness("driving", "zone1", 20);
    }
    return readAmbientBrightness();
  }

  private int normalZone2Brightness() {
    if (mManualOverrideActive) {
      return mManualZone2Enabled ? mManualZone2Brightness : 0;
    }
    return profileBrightness("driving", "zone2", ZONE_2_AMBIENT_BRIGHTNESS);
  }

  private int onroadDoorZone1Brightness() {
    return mManualOverrideActive
        ? normalZone1Brightness() : profileBrightness("onroadDoor", "zone1", normalZone1Brightness());
  }

  private int onroadDoorZone2Brightness() {
    return mManualOverrideActive
        ? normalZone2Brightness() : profileBrightness("onroadDoor", "zone2", 100);
  }

  private int activeOnroadZone1Brightness() {
    return mDoorOpen && profileFeatureEnabled("onroadDoor", true)
        ? onroadDoorZone1Brightness() : normalZone1Brightness();
  }

  private int activeOnroadZone2Brightness() {
    return mDoorOpen && profileFeatureEnabled("onroadDoor", true)
        ? onroadDoorZone2Brightness() : normalZone2Brightness();
  }

  private int offroadDoorZone1Brightness() {
    return mManualOverrideActive
        ? normalZone1Brightness()
        : profileBrightness("offroadDoor", "zone1", OFFROAD_DOOR_ZONE_1_BRIGHTNESS);
  }

  private int offroadDoorZone2Brightness() {
    return mManualOverrideActive
        ? normalZone2Brightness()
        : profileBrightness("offroadDoor", "zone2", OFFROAD_DOOR_ZONE_2_BRIGHTNESS);
  }

  private int exitCourtesyZone2Brightness() {
    return mManualOverrideActive
        ? normalZone2Brightness()
        : profileBrightness("exitCourtesy", "zone2", OFFROAD_DOOR_ZONE_2_BRIGHTNESS);
  }

  private byte[] normalColorPacket() {
    if (!mManualOverrideActive) {
      return drivingColorPacket();
    }
    return buildColorPacket(
        mManualZone1Red, mManualZone1Green, mManualZone1Blue,
        mManualZone2Red, mManualZone2Green, mManualZone2Blue);
  }

  private byte[] warningColorPacket() {
    if (mManualOverrideActive) {
      return buildColorPacket(255, 0, 0,
          mManualZone2Red, mManualZone2Green, mManualZone2Blue);
    }
    JSONObject zone1 = profileZone("overspeed", "zone1");
    JSONObject zone2 = mDoorOpen && profileFeatureEnabled("onroadDoor", true)
        ? profileZone("onroadDoor", "zone2") : profileZone("driving", "zone2");
    return buildColorPacket(
        colorValue(zone1, 0, 255), colorValue(zone1, 1, 0), colorValue(zone1, 2, 0),
        colorValue(zone2, 0, 255), colorValue(zone2, 1, 255), colorValue(zone2, 2, 255));
  }

  private void sendPacket(byte[] packet) {
    if (isColorPacket(packet)) {
      rememberColorPacket(packet);
    }
    if (isBrightnessPacket(packet)) {
      coalescePendingBrightnessPackets();
    }
    if (mQueue.size() > 20) {
      mQueue.poll();
    }
    mQueue.offer(packet.clone());
    connectIfNeeded();
    flushNext();
  }

  private void flushNext() {
    if (mWriting || !mNotifyReady || mWriteCharacteristic == null || mGatt == null || mQueue.isEmpty()) {
      return;
    }
    byte[] packet = mQueue.poll();
    mWriteCharacteristic.setValue(packet);
    configureWriteCharacteristic(mWriteCharacteristic);
    mWriting = true;
    mHandler.removeCallbacks(mWriteTimeoutRunnable);
    mHandler.removeCallbacks(mWritePaceRunnable);
    mHandler.postDelayed(mWriteTimeoutRunnable, 1200);
    if (mWriteCharacteristic.getWriteType() == BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE
        && usesPacedWrite(packet)) {
      mHandler.postDelayed(mWritePaceRunnable, START_PACKET_PACE_INTERVAL_MS);
    }
    boolean queued = mGatt.writeCharacteristic(mWriteCharacteristic);
    Log.i(TAG, "ambient write queued ok=" + queued);
    if (!queued) {
      mHandler.removeCallbacks(mWriteTimeoutRunnable);
      mHandler.removeCallbacks(mWritePaceRunnable);
      mWriting = false;
      mQueue.offerFirst(packet);
      mConnected = false;
      mNotifyReady = false;
      mStartQueued = false;
      mWriteCharacteristic = null;
      mNotifyCharacteristic = null;
      closeGatt();
      scheduleReconnect(CONNECT_RETRY_MS);
    }
  }

  private void connectIfNeeded() {
    if (mConnected || mConnecting || mScanning || mReconnectScheduled) {
      return;
    }
    if (mAdapter == null) {
      mAdapter = BluetoothAdapter.getDefaultAdapter();
    }
    if (mAdapter == null || !mAdapter.isEnabled()) {
      Log.w(TAG, "bluetooth disabled");
      scheduleReconnect(CONNECT_RETRY_MS);
      return;
    }
    if (!mSkipRememberedOnce && connectRememberedCandidate()) {
      return;
    }
    mSkipRememberedOnce = false;
    if (connectBondedCandidate()) {
      return;
    }
    mSeenScanDevices.clear();
    mScanning = mAdapter.startLeScan(mScanCallback);
    Log.i(TAG, "ambient scan start=" + mScanning);
    if (mScanning) {
      mHandler.removeCallbacks(mStopScanRunnable);
      mHandler.postDelayed(mStopScanRunnable, 10000);
    } else {
      scheduleReconnect(CONNECT_RETRY_MS);
    }
  }

  private void scheduleReconnect() {
    scheduleReconnect(CONNECT_RETRY_MS);
  }

  private void scheduleReconnect(long delayMs) {
    if (!needsConnection() || mConnected || mConnecting || mScanning) {
      return;
    }
    mHandler.removeCallbacks(mReconnectRunnable);
    mReconnectScheduled = true;
    Log.i(TAG, "ambient reconnect scheduled delayMs=" + delayMs);
    mHandler.postDelayed(mReconnectRunnable, Math.max(0L, delayMs));
  }

  private boolean connectRememberedCandidate() {
    String address = Settings.System.getString(
        mContext.getContentResolver(), AMBIENT_DEVICE_ADDRESS_SETTING);
    if (address == null || !BluetoothAdapter.checkBluetoothAddress(address)) {
      return false;
    }
    try {
      connectDevice(mAdapter.getRemoteDevice(address));
      mSkipRememberedOnce = true;
      return true;
    } catch (IllegalArgumentException e) {
      Log.w(TAG, "bad remembered ambient address", e);
      return false;
    }
  }

  private boolean connectBondedCandidate() {
    Set<BluetoothDevice> devices = mAdapter.getBondedDevices();
    if (devices == null) {
      return false;
    }
    for (BluetoothDevice device : devices) {
      if (device != null && matchesAmbientDevice(device, null)) {
        connectDevice(device);
        return true;
      }
    }
    return false;
  }

  private void connectDevice(BluetoothDevice device) {
    closeGatt();
    mConnecting = true;
    mReconnectScheduled = false;
    mHandler.removeCallbacks(mReconnectRunnable);
    Settings.System.putString(
        mContext.getContentResolver(), AMBIENT_DEVICE_ADDRESS_SETTING, device.getAddress());
    Log.i(TAG, "ambient connect " + safeName(device) + " " + device.getAddress());
    mGatt = device.connectGatt(mContext, false, mGattCallback);
    if (mGatt == null) {
      mConnecting = false;
      scheduleReconnect(CONNECT_RETRY_MS);
    } else {
      mHandler.removeCallbacks(mConnectTimeoutRunnable);
      mHandler.postDelayed(mConnectTimeoutRunnable, CONNECT_ATTEMPT_TIMEOUT_MS);
    }
  }

  private void stopScan() {
    if (!mScanning || mAdapter == null) {
      return;
    }
    mAdapter.stopLeScan(mScanCallback);
    mScanning = false;
    mHandler.removeCallbacks(mStopScanRunnable);
    Log.i(TAG, "ambient scan stop");
  }

  private void closeGatt() {
    mConnecting = false;
    mHandler.removeCallbacks(mConnectTimeoutRunnable);
    if (mGatt != null) {
      try {
        mGatt.close();
      } catch (Exception ignored) {
      }
      mGatt = null;
    }
  }

  private void logSeenScanDevice(BluetoothDevice device, int rssi) {
    String name = safeName(device);
    if (name.length() == 0) {
      return;
    }
    String key = name + "|" + device.getAddress();
    if (mSeenScanDevices.add(key)) {
      Log.i(TAG, "ambient seen " + name + " " + device.getAddress() + " rssi=" + rssi);
    }
  }

  private boolean needsConnection() {
    return mAmbientActive || !mQueue.isEmpty() || mOverspeedActive || mReverseActive;
  }

  private void queueStartPacket() {
    if (mStartQueued) {
      return;
    }
    mQueue.offerFirst(PACKET_START.clone());
    mStartQueued = true;
  }

  private void restoreActiveStateAfterConnect() {
    removePendingAmbientStatePackets();
    if (mReverseActive) {
      mQueue.offer(PACKET_OFF.clone());
      return;
    }
    if (mOverspeedActive) {
      startBlink();
      return;
    }
    if (mAmbientActive) {
      byte[] color = activeStateColorPacket();
      rememberColorPacket(color);
      mQueue.offer(color.clone());
      if (mOnroad) {
        startBrightnessSync();
      } else {
        mQueue.offer(buildBrightnessPacket(true, mAmbientTargetZone1, mAmbientTargetZone2));
      }
      return;
    }
    mQueue.offer(PACKET_OFF.clone());
  }

  private void removePendingAmbientStatePackets() {
    if (mQueue.isEmpty()) {
      return;
    }
    ArrayDeque<byte[]> retained = new ArrayDeque<byte[]>();
    while (!mQueue.isEmpty()) {
      byte[] packet = mQueue.poll();
      if (packet != null && (packet.length < 2 || packet[1] != (byte) 0x8d)) {
        retained.offer(packet);
      }
    }
    mQueue.addAll(retained);
  }

  private void writeAck() {
    if (mGatt == null || mWriteCharacteristic == null) {
      return;
    }
    mWriteCharacteristic.setValue(PACKET_ACK);
    configureWriteCharacteristic(mWriteCharacteristic);
    boolean queued = mGatt.writeCharacteristic(mWriteCharacteristic);
    Log.i(TAG, "ambient ack queued ok=" + queued);
  }

  private int readAmbientBrightness() {
    int screenBrightness = readScreenBrightness();
    if (screenBrightness <= SCREEN_BRIGHTNESS_ONE_PERCENT) {
      return MIN_AMBIENT_BRIGHTNESS;
    }
    if (screenBrightness <= SCREEN_BRIGHTNESS_EIGHT_PERCENT) {
      int lowScreenRange = SCREEN_BRIGHTNESS_EIGHT_PERCENT - SCREEN_BRIGHTNESS_ONE_PERCENT;
      int lowAmbientRange = MID_AMBIENT_BRIGHTNESS - MIN_AMBIENT_BRIGHTNESS;
      int lowBrightness = MIN_AMBIENT_BRIGHTNESS
          + (((screenBrightness - SCREEN_BRIGHTNESS_ONE_PERCENT) * lowAmbientRange)
          + (lowScreenRange / 2)) / lowScreenRange;
      return clamp(lowBrightness, MIN_AMBIENT_BRIGHTNESS, MID_AMBIENT_BRIGHTNESS);
    }
    if (screenBrightness <= SCREEN_BRIGHTNESS_FIFTY_PERCENT) {
      int midScreenRange = SCREEN_BRIGHTNESS_FIFTY_PERCENT - SCREEN_BRIGHTNESS_EIGHT_PERCENT;
      int midAmbientRange = OUTDOOR_AMBIENT_BRIGHTNESS - MID_AMBIENT_BRIGHTNESS;
      int midBrightness = MID_AMBIENT_BRIGHTNESS
          + (((screenBrightness - SCREEN_BRIGHTNESS_EIGHT_PERCENT) * midAmbientRange)
          + (midScreenRange / 2)) / midScreenRange;
      return clamp(midBrightness, MID_AMBIENT_BRIGHTNESS, OUTDOOR_AMBIENT_BRIGHTNESS);
    }
    return MAX_AMBIENT_BRIGHTNESS;
  }

  private int readScreenBrightness() {
    return clamp(Settings.System.getInt(mContext.getContentResolver(), "screen_brightness", 255), 0, 255);
  }

  private int readAmbientTransitionStepMs() {
    JSONObject timing = profileSection("timing");
    if (timing.has("transitionUpdatesPerSecond")) {
      int updatesPerSecond = clamp(timing.optInt("transitionUpdatesPerSecond", 30), 5, 30);
      return Math.max(MIN_AMBIENT_TRANSITION_STEP_MS,
          Math.min(MAX_AMBIENT_TRANSITION_STEP_MS, 1000 / updatesPerSecond));
    }
    return clamp(Settings.System.getInt(mContext.getContentResolver(),
        AMBIENT_TRANSITION_STEP_SETTING, DEFAULT_AMBIENT_TRANSITION_STEP_MS),
        MIN_AMBIENT_TRANSITION_STEP_MS, MAX_AMBIENT_TRANSITION_STEP_MS);
  }

  private int readAmbientFrameStepMs() {
    // A color fade frame writes one RGB packet and one brightness packet. Keep
    // their combined BLE rate within the configured transition update limit.
    return Math.min(MAX_AMBIENT_TRANSITION_STEP_MS, readAmbientTransitionStepMs() * 2);
  }

  private int readAckSettleIntervalMs() {
    return clamp(Settings.System.getInt(mContext.getContentResolver(),
        ACK_SETTLE_INTERVAL_SETTING, DEFAULT_ACK_SETTLE_INTERVAL_MS),
        MIN_ACK_SETTLE_INTERVAL_MS, MAX_ACK_SETTLE_INTERVAL_MS);
  }

  private void coalescePendingBrightnessPackets() {
    if (mQueue.isEmpty()) {
      return;
    }
    ArrayDeque<byte[]> retained = new ArrayDeque<byte[]>();
    while (!mQueue.isEmpty()) {
      byte[] packet = mQueue.poll();
      if (!isBrightnessPacket(packet)) {
        retained.offer(packet);
      }
    }
    mQueue.addAll(retained);
  }

  private static boolean isStartPacket(byte[] packet) {
    return packet != null && packet.length > 1
        && packet[0] == 0x2e && packet[1] == (byte) 0x81;
  }

  private static boolean usesPacedWrite(byte[] packet) {
    return isStartPacket(packet) || (packet != null && packet.length == 12);
  }

  private static boolean isBrightnessPacket(byte[] packet) {
    return packet != null && packet.length == 8
        && packet[0] == 0x2e && packet[1] == (byte) 0x8d
        && packet[2] == 0x04 && packet[4] == 0x48;
  }

  private static boolean isColorPacket(byte[] packet) {
    return packet != null && packet.length == 12
        && packet[0] == 0x2e && packet[1] == (byte) 0x8d
        && packet[2] == 0x08 && packet[3] == 0x01;
  }

  private void rememberColorPacket(byte[] packet) {
    mCurrentZone1Red = colorPacketValue(packet, 5, mCurrentZone1Red);
    mCurrentZone1Green = colorPacketValue(packet, 6, mCurrentZone1Green);
    mCurrentZone1Blue = colorPacketValue(packet, 7, mCurrentZone1Blue);
    mCurrentZone2Red = colorPacketValue(packet, 8, mCurrentZone2Red);
    mCurrentZone2Green = colorPacketValue(packet, 9, mCurrentZone2Green);
    mCurrentZone2Blue = colorPacketValue(packet, 10, mCurrentZone2Blue);
  }

  private static byte[] buildBrightnessPacket(boolean powerOn, int brightness) {
    return buildBrightnessPacket(powerOn, brightness, ZONE_2_AMBIENT_BRIGHTNESS);
  }

  private static byte[] buildBrightnessPacket(boolean powerOn, int brightness, int zone2Brightness) {
    int zone1Level = powerOn ? clamp(brightness, 0, 100) : 0;
    int zone2Level = powerOn ? clamp(zone2Brightness, 0, 100) : 0;
    int switchType = powerOn ? 0x48 : 0x00;
    return buildPacket(0x8d, new int[] { 0x00, switchType, zone1Level, zone2Level });
  }

  private static byte[] buildColorPacket(int zone1Red, int zone1Green, int zone1Blue,
                                         int zone2Red, int zone2Green, int zone2Blue) {
    return buildPacket(0x8d, new int[] {
        0x01, 0x08,
        clamp(zone1Red, 0, 255), clamp(zone1Green, 0, 255), clamp(zone1Blue, 0, 255),
        clamp(zone2Red, 0, 255), clamp(zone2Green, 0, 255), clamp(zone2Blue, 0, 255)
    });
  }

  private static int colorPacketValue(byte[] packet, int index, int fallback) {
    return packet != null && index >= 0 && index < packet.length - 1
        ? packet[index] & 0xff : fallback;
  }

  private static int interpolate(int start, int target, float progress) {
    return Math.round(start + ((target - start) * progress));
  }

  private static byte[] buildPacket(int dataType, int[] payload) {
    int length = payload.length;
    byte[] packet = new byte[length + 4];
    packet[0] = 0x2e;
    packet[1] = (byte) dataType;
    packet[2] = (byte) length;
    int sum = dataType + length;
    for (int i = 0; i < length; i++) {
      int value = payload[i] & 0xff;
      packet[i + 3] = (byte) value;
      sum += value;
    }
    packet[packet.length - 1] = (byte) ((~sum) & 0xff);
    return packet;
  }

  private static int clamp(int value, int min, int max) {
    return Math.max(min, Math.min(max, value));
  }

  private static void configureWriteCharacteristic(BluetoothGattCharacteristic characteristic) {
    int props = characteristic.getProperties();
    if ((props & BluetoothGattCharacteristic.PROPERTY_WRITE_NO_RESPONSE) != 0) {
      characteristic.setWriteType(BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE);
    } else {
      characteristic.setWriteType(BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT);
    }
  }

  private static boolean enableNotifications(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic) {
    if (gatt == null || characteristic == null) {
      return false;
    }
    boolean local = gatt.setCharacteristicNotification(characteristic, true);
    BluetoothGattDescriptor descriptor = characteristic.getDescriptor(CLIENT_CONFIG_UUID);
    if (!local || descriptor == null) {
      Log.w(TAG, "ambient notify setup local=" + local + " descriptor=" + (descriptor != null));
      return false;
    }
    descriptor.setValue(BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE);
    boolean queued = gatt.writeDescriptor(descriptor);
    Log.i(TAG, "ambient notify setup queued ok=" + queued);
    return queued;
  }

  private static BluetoothGattCharacteristic findWriteCharacteristic(BluetoothGatt gatt) {
    BluetoothGattService service = gatt.getService(SERVICE_UUID);
    if (service == null) {
      service = gatt.getService(LEGACY_SERVICE_UUID);
    }
    if (service == null) {
      return null;
    }
    return service.getCharacteristic(WRITE_UUID);
  }

  private static BluetoothGattCharacteristic findNotifyCharacteristic(BluetoothGatt gatt) {
    BluetoothGattService service = gatt.getService(SERVICE_UUID);
    if (service == null) {
      service = gatt.getService(LEGACY_SERVICE_UUID);
    }
    if (service == null) {
      return null;
    }
    return service.getCharacteristic(NOTIFY_UUID);
  }

  private static boolean matchesAmbientDevice(BluetoothDevice device, byte[] scanRecord) {
    String name = safeName(device).toLowerCase(Locale.US);
    if (name.contains("rz-slave") || name.contains("rz_slave") || name.contains("rz slave")
        || name.contains("slave")) {
      return false;
    }
    return name.contains("lamp") || name.contains("frgn") || name.contains("ambient")
        || name.contains("carled") || name.contains("pocket")
        || scanRecordContainsAmbientUuid(scanRecord);
  }

  private static boolean scanRecordContainsAmbientUuid(byte[] scanRecord) {
    if (scanRecord == null) {
      return false;
    }
    for (int i = 0; i + 1 < scanRecord.length; i++) {
      int first = scanRecord[i] & 0xff;
      int second = scanRecord[i + 1] & 0xff;
      if ((first == 0x00 || first == 0x30) && (second == 0xae || second == 0xaf)) {
        return true;
      }
    }
    return false;
  }

  private static String bytesToHex(byte[] data) {
    StringBuilder builder = new StringBuilder(data.length * 2);
    for (byte b : data) {
      builder.append(String.format(Locale.US, "%02X", b & 0xff));
    }
    return builder.toString();
  }

  private static String safeName(BluetoothDevice device) {
    try {
      String name = device.getName();
      return name == null ? "" : name;
    } catch (Exception ignored) {
      return "";
    }
  }

  private static String normalizeGear(String gear) {
    String text = gear.trim().toLowerCase(Locale.US);
    if (text.endsWith(".reverse")) {
      return "reverse";
    }
    if (text.endsWith(".park")) {
      return "park";
    }
    if (text.endsWith(".neutral")) {
      return "neutral";
    }
    if (text.endsWith(".drive")) {
      return "drive";
    }
    return text;
  }

  private static boolean isReverse(String gear) {
    return "r".equals(gear) || "reverse".equals(gear);
  }

  private static boolean isDriveGear(String gear) {
    return "p".equals(gear) || "park".equals(gear)
        || "n".equals(gear) || "neutral".equals(gear)
        || "d".equals(gear) || "drive".equals(gear);
  }
}
