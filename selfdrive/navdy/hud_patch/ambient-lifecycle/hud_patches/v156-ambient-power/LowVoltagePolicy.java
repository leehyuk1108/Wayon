package com.navdy.hud.app.ambient;

import android.os.SystemClock;
import android.util.Log;

/** User-selected always-on policy. Temperature/manual shutdowns are unchanged. */
public final class LowVoltagePolicy {
  private static long lastReport = -60000L;

  public static boolean suppress(String reason) {
    return "LOW_VOLTAGE".equals(reason) || "CRITICAL_VOLTAGE".equals(reason);
  }

  public static boolean canWaitForOff(String reason) {
    return !suppress(reason) && !"HIGH_TEMPERATURE".equals(reason)
        && !"POWER_LOSS".equals(reason) && !"ACCELERATE_SHUTDOWN".equals(reason);
  }

  public static synchronized void report(double volts) {
    long now = SystemClock.elapsedRealtime();
    if (now - lastReport < 60000L) return;
    lastReport = now;
    Log.w("NavdyAmbientPower", "low voltage=" + volts
        + "; automatic low-voltage shutdown disabled by user policy");
  }
}
