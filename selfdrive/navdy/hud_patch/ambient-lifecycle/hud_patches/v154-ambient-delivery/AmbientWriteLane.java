package com.navdy.hud.app.ambient;

import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCharacteristic;
import android.os.Handler;
import java.util.ArrayDeque;
import java.util.Iterator;

/** Serializes ATT writes, including response ACKs, without changing light policy. */
public final class AmbientWriteLane {
  public interface Failure {
    void failed(String reason);
    void submitted(byte[] value);
  }
  private final Handler handler;
  private final Failure failure;
  private final ArrayDeque<Item> queue = new ArrayDeque<Item>();
  private Item active;
  private int rejected;
  private boolean closed;
  private final Runnable pump = new Runnable() { public void run() { drain(); } };
  private final Runnable deadline = new Runnable() { public void run() {
    stop("ATT write callback timeout");
  }};

  private static final class Item {
    final BluetoothGatt gatt;
    final BluetoothGattCharacteristic characteristic;
    final byte[] value;
    final int type;
    Item(BluetoothGatt g, BluetoothGattCharacteristic c) {
      gatt = g; characteristic = c; value = c.getValue().clone(); type = c.getWriteType();
    }
    boolean ack() { return value.length == 1 && value[0] == (byte) 0xff; }
    int stateKey() {
      return value.length >= 8 && value[0] == 0x2e && value[1] == (byte) 0x8d
          ? value[3] & 255 : -1;
    }
  }

  public AmbientWriteLane(Handler handler, Failure failure) {
    this.handler = handler; this.failure = failure;
  }

  public boolean offer(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic) {
    if (closed || gatt == null || characteristic == null || characteristic.getValue() == null) return false;
    Item item = new Item(gatt, characteristic);
    // Only unsent state frames are superseded. Never discard handshake or ACK.
    if (item.stateKey() >= 0) {
      for (Iterator<Item> it = queue.iterator(); it.hasNext();) {
        if (it.next().stateKey() == item.stateKey()) it.remove();
      }
    }
    if (queue.size() >= 8) { stop("ATT queue overflow"); return false; }
    if (item.ack()) queue.addFirst(item); else queue.addLast(item);
    if (active == null && rejected == 0) {
      handler.removeCallbacks(pump);
      handler.post(pump);
    }
    return true;
  }

  private void drain() {
    if (closed || active != null || queue.isEmpty()) return;
    Item item = queue.peekFirst();
    item.characteristic.setWriteType(item.type);
    item.characteristic.setValue(item.value.clone());
    boolean accepted;
    try { accepted = item.gatt.writeCharacteristic(item.characteristic); }
    catch (RuntimeException e) { stop("ATT write exception"); return; }
    if (!accepted) {
      // Android 5 can reject a write while the previous callback is in transit.
      if (++rejected >= 10) { stop("ATT busy retry exhausted"); return; }
      handler.postDelayed(pump, 30L);
      return;
    }
    rejected = 0;
    active = queue.removeFirst();
    failure.submitted(active.value.clone());
    handler.postDelayed(deadline, 1000L);
  }

  public void completed(BluetoothGatt gatt, BluetoothGattCharacteristic characteristic, int status) {
    if (closed || active == null || active.gatt != gatt || active.characteristic != characteristic) return;
    handler.removeCallbacks(deadline);
    if (status != BluetoothGatt.GATT_SUCCESS) { stop("ATT status=" + status); return; }
    active = null;
    handler.removeCallbacks(pump);
    handler.post(pump);
  }

  private void stop(String reason) {
    if (closed) return;
    close();
    failure.failed(reason);
  }

  public void close() {
    closed = true;
    handler.removeCallbacks(pump);
    handler.removeCallbacks(deadline);
    queue.clear();
    active = null;
  }
}
