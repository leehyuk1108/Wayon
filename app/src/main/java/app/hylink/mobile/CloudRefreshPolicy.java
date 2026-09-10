package app.hylink.mobile;

import java.util.HashMap;
import java.util.Map;

/** In-memory, per-key history freshness; manual refresh never uses stale lists. */
public final class CloudRefreshPolicy {
    private static final long HISTORY_INTERVAL_MS = 300_000L;
    private final Map<String, Long> refreshed = new HashMap<>();
    private String scope = "";
    private long retryAt;
    private int failures;

    public synchronized boolean selectScope(String key) {
        if (scope.equals(key)) return false;
        scope = key;
        refreshed.clear();
        retryAt = 0;
        failures = 0;
        return true;
    }

    public synchronized boolean canRefresh(long now, boolean force) {
        return force || now >= retryAt;
    }

    public synchronized boolean due(String endpoint, long now, boolean force) {
        Long previous = refreshed.get(endpoint);
        return force || endpoint.equals("feed") || previous == null || now - previous >= HISTORY_INTERVAL_MS;
    }

    public synchronized void completed(String endpoint, long now) {
        refreshed.put(endpoint, now);
    }

    public synchronized void result(boolean success, long now) {
        if (success) {
            failures = 0;
            retryAt = 0;
        } else {
            failures = Math.min(failures + 1, 4);
            retryAt = now + Math.min(300_000L, 30_000L * (1L << failures));
        }
    }
}
