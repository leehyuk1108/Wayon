package com.navdy.hud.app.ambient;

import android.os.Handler;
import android.os.SystemClock;

/** Never block the BLE handler, and never wait indefinitely for a missing module. */
public final class AmbientShutdownGate {
  public static void awaitOff(final AmbientGattSession session, final Handler handler,
                              final Runnable continuation) {
    final long deadline = SystemClock.elapsedRealtime() + 1500L;
    handler.post(new Runnable() {
      public void run() {
        boolean delivered = !session.needsDelivery();
        if (delivered || SystemClock.elapsedRealtime() >= deadline) {
          session.recordPowerEvent(delivered ? "shutdown OFF response confirmed"
              : "shutdown OFF unconfirmed; bounded wait expired");
          continuation.run();
        } else {
          handler.postDelayed(this, 50L);
        }
      }
    });
  }
}
