package app.hylink.mobile;

public final class CloudRefreshPolicyCheck {
    private static void check(boolean value) {
        if (!value) throw new AssertionError("Hylink refresh policy regression");
    }

    public static void main(String[] args) {
        CloudRefreshPolicy p = new CloudRefreshPolicy();
        check(p.selectScope("vehicle-a"));
        check(p.due("trips", 0, false));
        p.completed("trips", 0);
        check(!p.due("trips", 30_000, false));
        check(p.due("feed", 30_000, false));
        check(p.due("trips", 300_000, false));
        check(p.due("trips", 1, true));
        p.result(false, 0);
        check(!p.canRefresh(30_000, false));
        check(p.canRefresh(30_000, true));
        check(p.canRefresh(60_000, false));
        p.result(true, 0);
        check(p.canRefresh(1, false));
        check(!p.selectScope("vehicle-a"));
        check(p.selectScope("vehicle-b"));
        check(p.due("trips", 1, false));
        check(p.selectScope(""));
        check(p.selectScope("vehicle-a"));
        check(p.due("trips", 1, false));
        CloudRefreshPolicy normal = new CloudRefreshPolicy();
        normal.selectScope("vehicle-normal");
        int requests = 0;
        for (long now = 0; now < 3_600_000; now += 30_000) {
            for (String endpoint : new String[]{"feed", "trips", "snapshots", "impacts", "liveCaptures"}) {
                if (normal.due(endpoint, now, false)) {
                    requests++;
                    normal.completed(endpoint, now);
                }
            }
        }
        check(requests == 168); // Previously 600 hourly requests; no user actions.
        System.out.println("Hylink history cache, manual refresh, backoff and key isolation: PASS");
    }
}
