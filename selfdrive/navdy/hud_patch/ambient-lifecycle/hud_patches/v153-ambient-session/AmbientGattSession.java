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

  public AmbientGattSession(BluetoothGattCallback delegate, Handler handler, Context context) {
    this.delegate = delegate;
    this.handler = handler;
    this.journal = new File(context.getFilesDir(), "ambient-ble-events.log");
  }

  public void attach(BluetoothGatt gatt) {
    cancelTimeout();
    current = gatt;
    record(gatt == null ? "connect returned null" : "connect attempt");
  }

  public void detach() {
    cancelTimeout();
    current = null;
  }

  public long deferReconnect(long delayMs) {
    long now = SystemClock.elapsedRealtime();
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
      if (journal.length() > 65536L) {
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
    if (gatt != current) return;
    cancelTimeout();
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
      // Android reuses the characteristic object across notification callbacks.
      characteristic.setValue(value);
      delegate.onCharacteristicChanged(gatt, characteristic);
    }});
  }
}
