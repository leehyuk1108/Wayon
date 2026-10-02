package com.navdy.hud.app.ambient;

import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCallback;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattDescriptor;
import android.bluetooth.BluetoothProfile;
import android.content.Context;
import android.os.Handler;
import android.os.SystemClock;
import android.util.Log;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.UUID;
import java.util.Arrays;

/** Keeps BLE callbacks on the same queue as fades and rejects retired sessions. */
public final class AmbientGattSession extends BluetoothGattCallback {
  private static final String TAG = "NavdyAmbient";
  private static final UUID CCCD = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb");
  private final BluetoothGattCallback delegate;
  private final Handler handler;
  private final File journal;
  private BluetoothGatt current;
  private Runnable setupTimeout;
  private long reconnectNotBefore;
  private AmbientWriteLane writes;
  // A fresh HUD process cannot assume the separately powered strips are off.
  private boolean deliveryPending = true;
  private byte[] lastCommand;
  private int attemptsWithoutResponse;
  private final Runnable offResponseTimeout = new Runnable() { public void run() {
    if (isOff(lastCommand)) deliveryTimeout();
  }};

  public AmbientGattSession(BluetoothGattCallback delegate, Handler handler, Context context) {
    this.delegate = delegate;
    this.handler = handler;
    this.journal = new File(context.getFilesDir(), "ambient-ble-events.log");
  }

  public void attach(BluetoothGatt gatt) {
    cancelTimeout();
    handler.removeCallbacks(offResponseTimeout);
    lastCommand = null;
    if (writes != null) writes.close();
    current = gatt;
    attemptsWithoutResponse++;
    final BluetoothGatt attached = gatt;
    writes = new AmbientWriteLane(handler, new AmbientWriteLane.Failure() {
      public void failed(String reason) { fail(attached, 133, reason); }
      public void submitted(byte[] value) {
        if (value.length > 1) {
          handler.removeCallbacks(offResponseTimeout);
          deliveryPending = true;
          lastCommand = value;
          if (isOff(value)) {
            record("off submitted; awaiting module response");
            // A successful ATT callback alone must not retire the final OFF.
            handler.postDelayed(offResponseTimeout, 1500L);
          }
        }
      }
    });
    record(gatt == null ? "connect returned null" : "connect attempt");
  }

  public void detach() {
    cancelTimeout();
    handler.removeCallbacks(offResponseTimeout);
    if (current != null) deliveryPending = true;
    if (writes != null) writes.close();
    writes = null;
    lastCommand = null;
    current = null;
  }

  public boolean write(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic) {
    if (gatt != current || writes == null) return false;
    if (characteristic.getValue() != null && characteristic.getValue().length > 1) deliveryPending = true;
    return writes.offer(gatt, characteristic);
  }

  public boolean needsDelivery() { return deliveryPending; }

  public void deliveryTimeout() {
    if (current != null) fail(current, 133, "module response timeout");
  }

  private static boolean isOff(byte[] value) {
    return value != null && value.length == 8 && value[1] == (byte) 0x8d
        && value[3] == 0 && value[4] == 0 && value[5] == 0 && value[6] == 0;
  }

  static byte[] normalizedResponse(byte[] value) {
    if (value == null || value.length == 0) return null;
    if (value.length == 1 && value[0] == (byte) 0xff) return value;
    if (value.length > 1 && value[0] == (byte) 0xff) value = Arrays.copyOfRange(value, 1, value.length);
    if (value.length < 4 || value[0] != 0x2e || value.length != (value[2] & 255) + 4) return null;
    int sum = 0;
    for (int i = 1; i < value.length; i++) sum += value[i] & 255;
    return (sum & 255) == 255 ? value : null;
  }

  public long deferReconnect(long delayMs) {
    long now = SystemClock.elapsedRealtime();
    // After repeated unanswered connections, stop hammering the radio all night.
    if (attemptsWithoutResponse > 1) {
      delayMs = Math.max(delayMs, Math.min(60000L, 5000L << Math.min(4, attemptsWithoutResponse - 2)));
    }
    reconnectNotBefore = Math.max(reconnectNotBefore,
        now + Math.max(0L, delayMs));
    long remaining = reconnectNotBefore - now;
    record("reconnect deferred ms=" + remaining);
    return remaining;
  }

  public boolean canConnect() {
    return SystemClock.elapsedRealtime() >= reconnectNotBefore;
  }

  private void cancelTimeout() {
    if (setupTimeout != null) handler.removeCallbacks(setupTimeout);
    setupTimeout = null;
  }

  private void record(String event) {
    Log.i(TAG, "session " + event);
    try {
      if (journal.length() > 1048576L) {
        File previous = new File(journal.getParentFile(), "ambient-ble-events.previous.log");
        if ((!previous.exists() || previous.delete()) && !journal.renameTo(previous)) {
          Log.w(TAG, "cannot rotate ambient BLE journal");
        }
      }
      try (FileWriter writer = new FileWriter(journal, true)) {
        writer.write(System.currentTimeMillis() + " " + event + "\n");
      }
    } catch (IOException e) {
      Log.w(TAG, "cannot write ambient BLE journal", e);
    }
  }

  private void fail(BluetoothGatt gatt, int status, String stage) {
    if (gatt == null || gatt != current) return;
    cancelTimeout();
    deliveryPending = true;
    record(stage + " failed status=" + status);
    // The existing disconnect handler clears transport state and owns backoff.
    delegate.onConnectionStateChange(gatt, status, BluetoothProfile.STATE_DISCONNECTED);
  }

  @Override public void onConnectionStateChange(final BluetoothGatt gatt, final int status,
                                                final int state) {
    handler.post(new Runnable() { public void run() {
      if (gatt != current) return;
      record("connection status=" + status + " state=" + state);
      if (status != BluetoothGatt.GATT_SUCCESS) {
        fail(gatt, status, "connection");
        return;
      }
      if (state == BluetoothProfile.STATE_CONNECTED) {
        cancelTimeout();
        setupTimeout = new Runnable() { public void run() {
          fail(gatt, 133, "service/notification setup timeout");
        }};
        handler.postDelayed(setupTimeout, 10000L);
      } else if (state == BluetoothProfile.STATE_DISCONNECTED) {
        cancelTimeout();
      }
      delegate.onConnectionStateChange(gatt, status, state);
    }});
  }

  @Override public void onServicesDiscovered(final BluetoothGatt gatt, final int status) {
    handler.post(new Runnable() { public void run() {
      if (gatt != current) return;
      record("services status=" + status);
      if (status != BluetoothGatt.GATT_SUCCESS) {
        fail(gatt, status, "services");
        return;
      }
      delegate.onServicesDiscovered(gatt, status);
    }});
  }

  @Override public void onDescriptorWrite(final BluetoothGatt gatt,
      final BluetoothGattDescriptor descriptor, final int status) {
    handler.post(new Runnable() { public void run() {
      if (gatt != current || descriptor == null || !CCCD.equals(descriptor.getUuid())) return;
      record("notifications status=" + status);
      if (status != BluetoothGatt.GATT_SUCCESS) {
        fail(gatt, status, "notifications");
        return;
      }
      cancelTimeout();
      delegate.onDescriptorWrite(gatt, descriptor, status);
    }});
  }

  @Override public void onCharacteristicWrite(final BluetoothGatt gatt,
      final BluetoothGattCharacteristic characteristic, final int status) {
    handler.post(new Runnable() { public void run() {
      if (gatt != current) return;
      if (writes != null) writes.completed(gatt, characteristic, status);
      if (gatt != current) return;
      if (status != BluetoothGatt.GATT_SUCCESS) {
        fail(gatt, status, "write");
        return;
      }
      delegate.onCharacteristicWrite(gatt, characteristic, status);
    }});
  }

  @Override public void onCharacteristicChanged(final BluetoothGatt gatt,
      final BluetoothGattCharacteristic characteristic) {
    if (characteristic == null) return;
    byte[] bytes = characteristic.getValue();
    final byte[] value = bytes == null ? null : bytes.clone();
    handler.post(new Runnable() { public void run() {
      if (gatt != current || value == null || value.length == 0) return;
      int first = value[0] & 255;
      if (value.length == 1 && (first == 0xfc || first == 0xf0 || first == 0xf3)) {
        fail(gatt, 133, "module NACK=" + first);
        return;
      }
      byte[] response = normalizedResponse(value);
      if (response == null) { record("invalid module response len=" + value.length); return; }
      attemptsWithoutResponse = 0;
      // Stock CarLED matches 0x8d responses by the first payload byte (or 0xbc).
      boolean matches = lastCommand != null && (response.length == 1
          || (response.length > 4 && lastCommand.length > 4
              && (response[3] == lastCommand[3] || response[1] == (byte) 0xbc)));
      if (matches) {
        if (isOff(lastCommand)) record("off protocol response received");
        handler.removeCallbacks(offResponseTimeout);
        deliveryPending = false;
        lastCommand = null;
      }
      // Android reuses the characteristic object across notification callbacks.
      characteristic.setValue(response);
      delegate.onCharacteristicChanged(gatt, characteristic);
    }});
  }
}
