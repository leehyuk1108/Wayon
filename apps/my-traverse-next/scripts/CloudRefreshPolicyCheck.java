package com.example.carcontroller;

public final class CloudRefreshPolicyCheck {
    private static void check(boolean value) {
        if (!value) throw new AssertionError("Cloud refresh policy regression");
    }

    public static void main(String[] args) {
        CloudRefreshPolicy policy = new CloudRefreshPolicy();
        check(policy.begin(0, true));
        check(!policy.begin(5_000, true));
        check(policy.begin(30_000, true));
        policy.failure(30_000);
        check(!policy.begin(60_000, true));
        check(policy.begin(90_000, true));
        policy.failure(90_000);
        check(!policy.begin(120_000, true));
        // Explicit refresh / vehicle command completion bypasses passive backoff.
        check(policy.begin(121_000, false));
        policy.success();
        check(policy.begin(151_000, true));
        for (int i = 0; i < 100; i++) policy.failure(200_000);
        check(!policy.begin(499_999, true));
        check(policy.begin(500_000, true));
        CloudRefreshPolicy normal = new CloudRefreshPolicy();
        int requests = 0;
        for (long now = 0; now < 3_600_000; now += 1_000) {
            if (normal.begin(now, true)) { requests++; normal.success(); }
        }
        check(requests == 120); // Previously 720 hourly passive reads at 5 s.
        System.out.println("My Traverse New passive refresh: PASS");
    }
}
