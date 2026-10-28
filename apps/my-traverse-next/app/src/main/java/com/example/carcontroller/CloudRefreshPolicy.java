package com.example.carcontroller;

/** Passive cloud reads only; never used to schedule a vehicle command or push. */
public final class CloudRefreshPolicy {
    public static final long INTERVAL_MS = 30_000L;
    private long nextAllowedMs;
    private int failures;

    public synchronized boolean begin(long nowMs, boolean automatic) {
        if (automatic && nowMs < nextAllowedMs) return false;
        nextAllowedMs = nowMs + INTERVAL_MS;
        return true;
    }

    public synchronized void success() {
        failures = 0;
    }

    public synchronized void failure(long nowMs) {
        failures = Math.min(failures + 1, 4);
        nextAllowedMs = nowMs + Math.min(300_000L, INTERVAL_MS * (1L << failures));
    }
}
