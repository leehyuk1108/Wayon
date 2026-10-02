.class public final Lcom/navdy/hud/app/ambient/LowVoltagePolicy;
.super Ljava/lang/Object;
.source "LowVoltagePolicy.java"


# static fields
.field private static lastReport:J


# direct methods
.method static constructor <clinit>()V
    .locals 2

    .line 8
    const-wide/32 v0, -0xea60

    sput-wide v0, Lcom/navdy/hud/app/ambient/LowVoltagePolicy;->lastReport:J

    return-void
.end method

.method public constructor <init>()V
    .locals 0

    .line 7
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static canWaitForOff(Ljava/lang/String;)Z
    .locals 1

    .line 15
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/LowVoltagePolicy;->suppress(Ljava/lang/String;)Z

    move-result v0

    if-nez v0, :cond_0

    const-string v0, "HIGH_TEMPERATURE"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_0

    .line 16
    const-string v0, "POWER_LOSS"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_0

    const-string v0, "ACCELERATE_SHUTDOWN"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p0

    if-nez p0, :cond_0

    const/4 p0, 0x1

    goto :goto_0

    :cond_0
    const/4 p0, 0x0

    .line 15
    :goto_0
    return p0
.end method

.method public static declared-synchronized report(D)V
    .locals 8

    const-class v0, Lcom/navdy/hud/app/ambient/LowVoltagePolicy;

    monitor-enter v0

    .line 20
    :try_start_0
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v1

    .line 21
    sget-wide v3, Lcom/navdy/hud/app/ambient/LowVoltagePolicy;->lastReport:J
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    sub-long v3, v1, v3

    const-wide/32 v5, 0xea60

    cmp-long v7, v3, v5

    if-gez v7, :cond_0

    monitor-exit v0

    return-void

    .line 22
    :cond_0
    :try_start_1
    sput-wide v1, Lcom/navdy/hud/app/ambient/LowVoltagePolicy;->lastReport:J

    .line 23
    const-string v1, "NavdyAmbientPower"

    new-instance v2, Ljava/lang/StringBuilder;

    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V

    const-string v3, "low voltage="

    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    invoke-virtual {v2, p0, p1}, Ljava/lang/StringBuilder;->append(D)Ljava/lang/StringBuilder;

    move-result-object p0

    const-string p1, "; automatic low-voltage shutdown disabled by user policy"

    invoke-virtual {p0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p0

    invoke-virtual {p0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    invoke-static {v1, p0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I
    :try_end_1
    .catchall {:try_start_1 .. :try_end_1} :catchall_0

    .line 25
    monitor-exit v0

    return-void

    .line 19
    :catchall_0
    move-exception p0

    :try_start_2
    monitor-exit v0
    :try_end_2
    .catchall {:try_start_2 .. :try_end_2} :catchall_0

    throw p0
.end method

.method public static suppress(Ljava/lang/String;)Z
    .locals 1

    .line 11
    const-string v0, "LOW_VOLTAGE"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "CRITICAL_VOLTAGE"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p0

    if-eqz p0, :cond_0

    goto :goto_0

    :cond_0
    const/4 p0, 0x0

    goto :goto_1

    :cond_1
    :goto_0
    const/4 p0, 0x1

    :goto_1
    return p0
.end method
