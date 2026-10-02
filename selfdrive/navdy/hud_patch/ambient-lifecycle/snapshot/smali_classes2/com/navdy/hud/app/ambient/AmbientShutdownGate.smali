.class public final Lcom/navdy/hud/app/ambient/AmbientShutdownGate;
.super Ljava/lang/Object;
.source "AmbientShutdownGate.java"


# direct methods
.method public constructor <init>()V
    .locals 0

    .line 7
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static awaitOff(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/os/Handler;Ljava/lang/Runnable;)V
    .locals 10

    .line 10
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    const-wide/16 v2, 0x5dc

    add-long v6, v0, v2

    .line 11
    new-instance v4, Lcom/navdy/hud/app/ambient/AmbientShutdownGate$1;

    move-object v5, p0

    move-object v9, p1

    move-object v8, p2

    invoke-direct/range {v4 .. v9}, Lcom/navdy/hud/app/ambient/AmbientShutdownGate$1;-><init>(Lcom/navdy/hud/app/ambient/AmbientGattSession;JLjava/lang/Runnable;Landroid/os/Handler;)V

    invoke-virtual {v9, v4}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 23
    return-void
.end method
