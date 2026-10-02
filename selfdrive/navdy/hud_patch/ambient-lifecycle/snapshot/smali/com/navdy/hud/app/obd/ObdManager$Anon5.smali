.class Lcom/navdy/hud/app/obd/ObdManager$Anon5;
.super Ljava/lang/Object;
.source "ObdManager.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Lcom/navdy/hud/app/obd/ObdManager;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = "Anon5"
.end annotation


# instance fields
.field final synthetic this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/obd/ObdManager;)V
    .locals 0
    .param p1, "this$Anon0"    # Lcom/navdy/hud/app/obd/ObdManager;

    .prologue
    .line 384
    iput-object p1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 11

    .line 345
    iget-object v0, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v0}, Lcom/navdy/hud/app/obd/ObdManager;->access$200(Lcom/navdy/hud/app/obd/ObdManager;)D

    move-result-wide v1

    .line 346
    iget-object v0, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-virtual {v0}, Lcom/navdy/hud/app/obd/ObdManager;->getBatteryVoltage()D

    move-result-wide v3

    invoke-static {v0, v3, v4}, Lcom/navdy/hud/app/obd/ObdManager;->access$202(Lcom/navdy/hud/app/obd/ObdManager;D)D

    .line 348
    iget-object v0, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v0}, Lcom/navdy/hud/app/obd/ObdManager;->access$200(Lcom/navdy/hud/app/obd/ObdManager;)D

    move-result-wide v3

    const-wide/high16 v5, -0x4010000000000000L    # -1.0

    cmpl-double v0, v3, v5

    if-eqz v0, :cond_0

    cmpl-double v0, v1, v5

    if-nez v0, :cond_0

    .line 349
    iget-object v0, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v0}, Lcom/navdy/hud/app/obd/ObdManager;->access$200(Lcom/navdy/hud/app/obd/ObdManager;)D

    move-result-wide v1

    invoke-static {v0, v1, v2}, Lcom/navdy/hud/app/obd/ObdManager;->access$302(Lcom/navdy/hud/app/obd/ObdManager;D)D

    .line 352
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v0}, Lcom/navdy/hud/app/obd/ObdManager;->access$200(Lcom/navdy/hud/app/obd/ObdManager;)D

    move-result-wide v1

    const-wide/16 v3, 0x0

    const/4 v0, 0x0

    cmpl-double v7, v1, v3

    if-eqz v7, :cond_9

    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v1}, Lcom/navdy/hud/app/obd/ObdManager;->access$200(Lcom/navdy/hud/app/obd/ObdManager;)D

    move-result-wide v1

    cmpl-double v3, v1, v5

    if-nez v3, :cond_1

    goto/16 :goto_3

    .line 361
    :cond_1
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v1}, Lcom/navdy/hud/app/obd/ObdManager;->access$200(Lcom/navdy/hud/app/obd/ObdManager;)D

    move-result-wide v1

    iget-object v3, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v3}, Lcom/navdy/hud/app/obd/ObdManager;->access$300(Lcom/navdy/hud/app/obd/ObdManager;)D

    move-result-wide v3

    cmpg-double v5, v1, v3

    if-gez v5, :cond_2

    .line 362
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v1}, Lcom/navdy/hud/app/obd/ObdManager;->access$200(Lcom/navdy/hud/app/obd/ObdManager;)D

    move-result-wide v2

    invoke-static {v1, v2, v3}, Lcom/navdy/hud/app/obd/ObdManager;->access$302(Lcom/navdy/hud/app/obd/ObdManager;D)D

    .line 364
    :cond_2
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v1}, Lcom/navdy/hud/app/obd/ObdManager;->access$200(Lcom/navdy/hud/app/obd/ObdManager;)D

    move-result-wide v1

    iget-object v3, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v3}, Lcom/navdy/hud/app/obd/ObdManager;->access$700(Lcom/navdy/hud/app/obd/ObdManager;)D

    move-result-wide v3

    cmpl-double v5, v1, v3

    if-lez v5, :cond_3

    .line 365
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v1}, Lcom/navdy/hud/app/obd/ObdManager;->access$200(Lcom/navdy/hud/app/obd/ObdManager;)D

    move-result-wide v2

    invoke-static {v1, v2, v3}, Lcom/navdy/hud/app/obd/ObdManager;->access$702(Lcom/navdy/hud/app/obd/ObdManager;D)D

    .line 367
    :cond_3
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    iget-object v1, v1, Lcom/navdy/hud/app/obd/ObdManager;->powerManager:Lcom/navdy/hud/app/device/PowerManager;

    invoke-virtual {v1}, Lcom/navdy/hud/app/device/PowerManager;->inQuietMode()Z

    move-result v1

    if-eqz v1, :cond_4

    sget-wide v1, Lcom/navdy/hud/app/obd/ObdManager;->LOW_BATTERY_VOLTAGE:D

    goto :goto_0

    :cond_4
    sget-wide v1, Lcom/navdy/hud/app/obd/ObdManager;->CRITICAL_BATTERY_VOLTAGE:D

    .line 369
    :goto_0
    iget-object v3, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v3}, Lcom/navdy/hud/app/obd/ObdManager;->access$200(Lcom/navdy/hud/app/obd/ObdManager;)D

    move-result-wide v3

    const-wide v5, 0x402999999999999aL    # 12.8

    cmpl-double v7, v3, v5

    if-ltz v7, :cond_5

    iget-object v3, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    iget-object v3, v3, Lcom/navdy/hud/app/obd/ObdManager;->powerManager:Lcom/navdy/hud/app/device/PowerManager;

    invoke-virtual {v3}, Lcom/navdy/hud/app/device/PowerManager;->inQuietMode()Z

    move-result v3

    if-eqz v3, :cond_5

    .line 370
    invoke-static {}, Lcom/navdy/hud/app/obd/ObdManager;->access$500()Lcom/navdy/service/library/log/Logger;

    move-result-object v1

    const-string v2, "Battery seems to be charging, waking up"

    invoke-virtual {v1, v2}, Lcom/navdy/service/library/log/Logger;->v(Ljava/lang/String;)V

    .line 371
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    iget-object v1, v1, Lcom/navdy/hud/app/obd/ObdManager;->powerManager:Lcom/navdy/hud/app/device/PowerManager;

    sget-object v2, Lcom/navdy/hud/app/analytics/AnalyticsSupport$WakeupReason;->VOLTAGE_SPIKE:Lcom/navdy/hud/app/analytics/AnalyticsSupport$WakeupReason;

    invoke-virtual {v1, v2}, Lcom/navdy/hud/app/device/PowerManager;->wakeUp(Lcom/navdy/hud/app/analytics/AnalyticsSupport$WakeupReason;)V

    .line 372
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v1, v0}, Lcom/navdy/hud/app/obd/ObdManager;->access$602(Lcom/navdy/hud/app/obd/ObdManager;I)I

    goto/16 :goto_2

    .line 374
    :cond_5
    iget-object v3, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v3}, Lcom/navdy/hud/app/obd/ObdManager;->access$200(Lcom/navdy/hud/app/obd/ObdManager;)D

    move-result-wide v3

    const/4 v5, 0x1

    cmpg-double v6, v3, v1

    if-gez v6, :cond_7

    invoke-static {v3, v4}, Lcom/navdy/hud/app/ambient/LowVoltagePolicy;->report(D)V
    goto/16 :goto_2

    .line 389
    :cond_7
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v1, v0}, Lcom/navdy/hud/app/obd/ObdManager;->access$402(Lcom/navdy/hud/app/obd/ObdManager;I)I

    .line 390
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    iget-object v1, v1, Lcom/navdy/hud/app/obd/ObdManager;->powerManager:Lcom/navdy/hud/app/device/PowerManager;

    invoke-virtual {v1}, Lcom/navdy/hud/app/device/PowerManager;->inQuietMode()Z

    move-result v1

    if-eqz v1, :cond_8

    .line 391
    invoke-static {}, Lcom/navdy/hud/app/obd/ObdManager;->access$500()Lcom/navdy/service/library/log/Logger;

    move-result-object v1

    new-instance v2, Ljava/lang/StringBuilder;

    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V

    const-string v3, "In Quiet mode , Battery voltage : "

    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    iget-object v3, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v3}, Lcom/navdy/hud/app/obd/ObdManager;->access$200(Lcom/navdy/hud/app/obd/ObdManager;)D

    move-result-wide v3

    invoke-virtual {v2, v3, v4}, Ljava/lang/StringBuilder;->append(D)Ljava/lang/StringBuilder;

    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v1, v2}, Lcom/navdy/service/library/log/Logger;->d(Ljava/lang/String;)V

    .line 392
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v1}, Lcom/navdy/hud/app/obd/ObdManager;->access$600(Lcom/navdy/hud/app/obd/ObdManager;)I

    move-result v2

    add-int/2addr v2, v5

    invoke-static {v1, v2}, Lcom/navdy/hud/app/obd/ObdManager;->access$602(Lcom/navdy/hud/app/obd/ObdManager;I)I

    .line 393
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v1}, Lcom/navdy/hud/app/obd/ObdManager;->access$600(Lcom/navdy/hud/app/obd/ObdManager;)I

    move-result v1

    const v2, 0x7fffffff

    if-lt v1, v2, :cond_8

    .line 394
    invoke-static {}, Lcom/navdy/hud/app/obd/ObdManager;->access$500()Lcom/navdy/service/library/log/Logger;

    move-result-object v1

    const-string v2, "Safe to put obd chip to sleep, invoking sleep"

    invoke-virtual {v1, v2}, Lcom/navdy/service/library/log/Logger;->v(Ljava/lang/String;)V

    .line 395
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v1, v0}, Lcom/navdy/hud/app/obd/ObdManager;->access$602(Lcom/navdy/hud/app/obd/ObdManager;I)I

    .line 396
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v1}, Lcom/navdy/hud/app/obd/ObdManager;->access$000(Lcom/navdy/hud/app/obd/ObdManager;)Landroid/os/Handler;

    move-result-object v1

    iget-object v2, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v2}, Lcom/navdy/hud/app/obd/ObdManager;->access$900(Lcom/navdy/hud/app/obd/ObdManager;)Ljava/lang/Runnable;

    move-result-object v2

    invoke-virtual {v1, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 397
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-virtual {v1, v0}, Lcom/navdy/hud/app/obd/ObdManager;->sleep(Z)V

    .line 401
    :cond_8
    :goto_2
    new-instance v0, Lcom/navdy/obd/Pid;

    const/4 v3, 0x0

    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v1}, Lcom/navdy/hud/app/obd/ObdManager;->access$200(Lcom/navdy/hud/app/obd/ObdManager;)D

    move-result-wide v5

    sget-object v7, Lcom/navdy/obd/Pid$DataType;->FLOAT:Lcom/navdy/obd/Pid$DataType;

    sget-object v8, Lcom/navdy/obd/Units;->NONE:Lcom/navdy/obd/Units;

    const-wide/16 v9, 0x0

    const-string/jumbo v4, "voltage"

    move-object v2, v0

    invoke-direct/range {v2 .. v10}, Lcom/navdy/obd/Pid;-><init>(ILjava/lang/String;DLcom/navdy/obd/Pid$DataType;Lcom/navdy/obd/Units;J)V

    .line 403
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    iget-object v1, v1, Lcom/navdy/hud/app/obd/ObdManager;->bus:Lcom/squareup/otto/Bus;

    new-instance v2, Lcom/navdy/hud/app/obd/ObdManager$ObdPidChangeEvent;

    invoke-direct {v2, v0}, Lcom/navdy/hud/app/obd/ObdManager$ObdPidChangeEvent;-><init>(Lcom/navdy/obd/Pid;)V

    invoke-virtual {v1, v2}, Lcom/squareup/otto/Bus;->post(Ljava/lang/Object;)V

    return-void

    .line 353
    :cond_9
    :goto_3
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v1}, Lcom/navdy/hud/app/obd/ObdManager;->access$400(Lcom/navdy/hud/app/obd/ObdManager;)I

    move-result v1

    if-eqz v1, :cond_a

    .line 354
    invoke-static {}, Lcom/navdy/hud/app/obd/ObdManager;->access$500()Lcom/navdy/service/library/log/Logger;

    move-result-object v1

    const-string v2, "Battery level data is not available"

    invoke-virtual {v1, v2}, Lcom/navdy/service/library/log/Logger;->v(Ljava/lang/String;)V

    .line 356
    :cond_a
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v1, v0}, Lcom/navdy/hud/app/obd/ObdManager;->access$402(Lcom/navdy/hud/app/obd/ObdManager;I)I

    .line 357
    iget-object v1, p0, Lcom/navdy/hud/app/obd/ObdManager$Anon5;->this$Anon0:Lcom/navdy/hud/app/obd/ObdManager;

    invoke-static {v1, v0}, Lcom/navdy/hud/app/obd/ObdManager;->access$602(Lcom/navdy/hud/app/obd/ObdManager;I)I

    return-void
.end method
