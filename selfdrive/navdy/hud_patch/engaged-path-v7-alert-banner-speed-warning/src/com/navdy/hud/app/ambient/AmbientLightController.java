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
import android.os.SystemClock;
import android.provider.Settings;
import android.util.Log;

import org.json.JSONObject;

import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;
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
  private static final int FADE_PHASE_WHITE_DOWN = 0;
  private static final int FADE_PHASE_RED_UP = 1;
  private static final int FADE_PHASE_RED_DOWN = 2;
  private static final int FADE_PHASE_WHITE_UP = 3;
  private static final int FADE_STEPS = 5;
  private static final int BRIGHTNESS_UPDATE_DELTA = 2;
  private static final long BRIGHTNESS_SYNC_INTERVAL_MS = 5000;
  private static final long CONNECT_RETRY_MS = 5000;
  private static final long FADE_STEP_INTERVAL_MS = 450;
  private static final long LOW_LIGHT_CHECK_INTERVAL_MS = 1000;
  private static final long OVERSPEED_ON_DELAY_MS = 1000;
  private static final long OVERSPEED_OFF_DELAY_MS = 2000;
  private static final long OVERSPEED_MIN_ACTIVE_MS = 3000;

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
  private final Handler mHandler = new Handler(Looper.getMainLooper());
  private final ArrayDeque<byte[]> mQueue = new ArrayDeque<byte[]>();
  private final Set<String> mSeenScanDevices = new HashSet<String>();

  private final BluetoothGattCallback mGattCallback = new BluetoothGattCallback() {
    @Override
    public void onConnectionStateChange(BluetoothGatt gatt, int status, int newState) {
      if (newState == BluetoothProfile.STATE_CONNECTED) {
        Log.i(TAG, "ambient gatt connected");
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
        scheduleReconnect();
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
        mWriting = false;
        writeAck();
        mHandler.removeCallbacks(mFlushAfterAckRunnable);
        mHandler.postDelayed(mFlushAfterAckRunnable, 120);
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
          sendPacket(PACKET_RED);
          sendPacket(buildBrightnessPacket(true, brightness, ZONE_2_AMBIENT_BRIGHTNESS));
          mWarningAnimationStarted = true;
          mLowLightWarning = true;
          mFadePhase = FADE_PHASE_WHITE_DOWN;
          mFadeStep = 0;
        } else if (mLastAmbientBrightness < 0
            || Math.abs(brightness - mLastAmbientBrightness) >= BRIGHTNESS_UPDATE_DELTA) {
          sendPacket(buildBrightnessPacket(true, brightness, ZONE_2_AMBIENT_BRIGHTNESS));
        }
        mLastAmbientBrightness = brightness;
        mHandler.postDelayed(this, LOW_LIGHT_CHECK_INTERVAL_MS);
        return;
      }

      if (!mWarningAnimationStarted || mLowLightWarning) {
        sendPacket(PACKET_RESTORE);
        mWarningAnimationStarted = true;
        mLowLightWarning = false;
        mFadePhase = FADE_PHASE_WHITE_DOWN;
        mFadeStep = 0;
      }

      int directionStep = (mFadePhase == FADE_PHASE_WHITE_DOWN || mFadePhase == FADE_PHASE_RED_DOWN)
          ? FADE_STEPS - mFadeStep : mFadeStep;
      int zone1Level = (brightness * directionStep + (FADE_STEPS / 2)) / FADE_STEPS;
      sendPacket(buildBrightnessPacket(true, zone1Level, ZONE_2_AMBIENT_BRIGHTNESS));
      mLastAmbientBrightness = brightness;

      mFadeStep++;
      if (mFadeStep > FADE_STEPS) {
        mFadeStep = 0;
        if (mFadePhase == FADE_PHASE_WHITE_DOWN) {
          mFadePhase = FADE_PHASE_RED_UP;
          sendPacket(PACKET_RED);
        } else if (mFadePhase == FADE_PHASE_RED_UP) {
          mFadePhase = FADE_PHASE_RED_DOWN;
        } else if (mFadePhase == FADE_PHASE_RED_DOWN) {
          mFadePhase = FADE_PHASE_WHITE_UP;
          sendPacket(PACKET_RESTORE);
        } else {
          mFadePhase = FADE_PHASE_WHITE_DOWN;
        }
      }
      mHandler.postDelayed(this, FADE_STEP_INTERVAL_MS);
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

  private BluetoothAdapter mAdapter;
  private BluetoothGatt mGatt;
  private BluetoothGattCharacteristic mWriteCharacteristic;
  private BluetoothGattCharacteristic mNotifyCharacteristic;
  private boolean mConnected;
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
  private int mFadePhase;
  private int mFadeStep;
  private int mLastAmbientBrightness = -1;
  private String mLastGear = "";

  private AmbientLightController(Context context) {
    mContext = context.getApplicationContext();
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
      JSONObject json = new JSONObject(payload);
      String gear = json.optString("gear", json.optString("gearShifter", ""));
      if (gear != null && gear.length() > 0) {
        onGearText(context, gear);
      }
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

  private void requestOverspeed(boolean overspeed) {
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
      mReverseActive = true;
      mAmbientActive = false;
      stopBlink();
      stopBrightnessSync();
      sendPacket(PACKET_OFF);
      return;
    }

    if (isDriveGear(normalized)) {
      mReverseActive = false;
      mAmbientActive = true;
      startBrightnessSync();
      if (mOverspeedActive) {
        startBlink();
      } else {
        sendPacket(PACKET_RESTORE);
      }
    }
  }

  private void setOverspeed(boolean overspeed) {
    if (mOverspeedActive == overspeed) {
      return;
    }
    mOverspeedActive = overspeed;
    mOverspeedActivatedAtMs = overspeed ? SystemClock.elapsedRealtime() : 0L;
    Log.i(TAG, "camera overspeed=" + overspeed);
    if (overspeed) {
      if (!mReverseActive) {
        startBlink();
      }
    } else {
      stopBlink();
      if (!mReverseActive) {
        syncAmbientBrightness(true);
        sendPacket(PACKET_RESTORE);
      }
    }
  }

  private void startBlink() {
    stopBlink();
    mAmbientActive = true;
    startBrightnessSync();
    mHandler.post(mBlinkRunnable);
  }

  private void stopBlink() {
    mHandler.removeCallbacks(mBlinkRunnable);
    mWarningAnimationStarted = false;
    mLowLightWarning = false;
    mFadePhase = FADE_PHASE_WHITE_DOWN;
    mFadeStep = 0;
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
    int brightness = readAmbientBrightness();
    if (mOverspeedActive && mWarningAnimationStarted) {
      mLastAmbientBrightness = brightness;
      return;
    }
    if (!force && mLastAmbientBrightness >= 0
        && Math.abs(brightness - mLastAmbientBrightness) < BRIGHTNESS_UPDATE_DELTA) {
      return;
    }
    mLastAmbientBrightness = brightness;
    Log.i(TAG, "ambient brightness=" + brightness + " screen=" + readScreenBrightness());
    sendPacket(buildBrightnessPacket(true, brightness, ZONE_2_AMBIENT_BRIGHTNESS));
  }

  private void sendPacket(byte[] packet) {
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
    if (mWriteCharacteristic.getWriteType() == BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE) {
      mHandler.postDelayed(mWritePaceRunnable, 350);
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
      scheduleReconnect();
    }
  }

  private void connectIfNeeded() {
    if (mConnected || mScanning) {
      return;
    }
    if (mAdapter == null) {
      mAdapter = BluetoothAdapter.getDefaultAdapter();
    }
    if (mAdapter == null || !mAdapter.isEnabled()) {
      Log.w(TAG, "bluetooth disabled");
      scheduleReconnect();
      return;
    }
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
      scheduleReconnect();
    }
  }

  private void scheduleReconnect() {
    if (!needsConnection() || mConnected || mScanning || mReconnectScheduled) {
      return;
    }
    mReconnectScheduled = true;
    Log.i(TAG, "ambient reconnect scheduled");
    mHandler.postDelayed(mReconnectRunnable, CONNECT_RETRY_MS);
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
    Log.i(TAG, "ambient connect " + safeName(device) + " " + device.getAddress());
    mGatt = device.connectGatt(mContext, false, mGattCallback);
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
    if (mReverseActive) {
      mQueue.offer(PACKET_OFF.clone());
      return;
    }
    if (mOverspeedActive) {
      startBlink();
      return;
    }
    if (mAmbientActive) {
      startBrightnessSync();
    }
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

  private static byte[] buildBrightnessPacket(boolean powerOn, int brightness) {
    return buildBrightnessPacket(powerOn, brightness, ZONE_2_AMBIENT_BRIGHTNESS);
  }

  private static byte[] buildBrightnessPacket(boolean powerOn, int brightness, int zone2Brightness) {
    int zone1Level = powerOn ? clamp(brightness, 0, 100) : 0;
    int zone2Level = powerOn ? clamp(zone2Brightness, 0, 100) : 0;
    int switchType = powerOn ? 0x48 : 0x00;
    return buildPacket(0x8d, new int[] { 0x00, switchType, zone1Level, zone2Level });
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
        || name.contains("carled") || name.contains("pocket");
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
