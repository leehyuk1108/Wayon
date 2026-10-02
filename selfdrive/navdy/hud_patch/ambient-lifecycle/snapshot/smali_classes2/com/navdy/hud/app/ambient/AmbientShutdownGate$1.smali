.class Lcom/navdy/hud/app/ambient/AmbientShutdownGate$1;
.super Ljava/lang/Object;
.source "AmbientShutdownGate.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/navdy/hud/app/ambient/AmbientShutdownGate;->awaitOff(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/os/Handler;Ljava/lang/Runnable;)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic val$continuation:Ljava/lang/Runnable;

.field final synthetic val$deadline:J

.field final synthetic val$handler:Landroid/os/Handler;

.field final synthetic val$session:Lcom/navdy/hud/app/ambient/AmbientGattSession;


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/ambient/AmbientGattSession;JLjava/lang/Runnable;Landroid/os/Handler;)V
    .locals 0
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 11
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientShutdownGate$1;->val$session:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    iput-wide p2, p0, Lcom/navdy/hud/app/ambient/AmbientShutdownGate$1;->val$deadline:J

    iput-object p4, p0, Lcom/navdy/hud/app/ambient/AmbientShutdownGate$1;->val$continuation:Ljava/lang/Runnable;

    iput-object p5, p0, Lcom/navdy/hud/app/ambient/AmbientShutdownGate$1;->val$handler:Landroid/os/Handler;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 6

    .line 13
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientShutdownGate$1;->val$session:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-virtual {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->needsDelivery()Z

    move-result v0

    .line 14
    if-eqz v0, :cond_1

    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v1

    iget-wide v3, p0, Lcom/navdy/hud/app/ambient/AmbientShutdownGate$1;->val$deadline:J

    cmp-long v5, v1, v3

    if-ltz v5, :cond_0

    goto :goto_0

    .line 19
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientShutdownGate$1;->val$handler:Landroid/os/Handler;

    const-wide/16 v1, 0x32

    invoke-virtual {v0, p0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    goto :goto_2

    .line 15
    :cond_1
    :goto_0
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientShutdownGate$1;->val$session:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    if-nez v0, :cond_2

    const-string v0, "shutdown OFF response confirmed"

    goto :goto_1

    .line 16
    :cond_2
    const-string v0, "shutdown OFF unconfirmed; bounded wait expired"

    .line 15
    :goto_1
    invoke-virtual {v1, v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->recordPowerEvent(Ljava/lang/String;)V

    .line 17
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientShutdownGate$1;->val$continuation:Ljava/lang/Runnable;

    invoke-interface {v0}, Ljava/lang/Runnable;->run()V

    .line 21
    :goto_2
    return-void
.end method
