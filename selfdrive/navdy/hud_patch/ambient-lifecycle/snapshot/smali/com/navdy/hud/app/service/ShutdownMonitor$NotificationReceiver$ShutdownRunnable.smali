.class Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver$ShutdownRunnable;
.super Ljava/lang/Object;
.source "ShutdownMonitor.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x2
    name = "ShutdownRunnable"
.end annotation


# instance fields
.field private ambientPrepared:Z
.field private final event:Lcom/navdy/hud/app/event/Shutdown;

.field final synthetic this$Anon1:Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;Lcom/navdy/hud/app/event/Shutdown;)V
    .locals 0
    .param p2, "r"    # Lcom/navdy/hud/app/event/Shutdown;

    .prologue
    .line 356
    iput-object p1, p0, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver$ShutdownRunnable;->this$Anon1:Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 357
    iput-object p2, p0, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver$ShutdownRunnable;->event:Lcom/navdy/hud/app/event/Shutdown;

    .line 358
    return-void
.end method


# virtual methods
.method public run()V
    .locals 12

    .prologue
    const/4 v7, 0x1

    const/4 v8, 0x0

    .line 361
    iget-object v9, p0, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver$ShutdownRunnable;->event:Lcom/navdy/hud/app/event/Shutdown;

    iget-object v5, v9, Lcom/navdy/hud/app/event/Shutdown;->reason:Lcom/navdy/hud/app/event/Shutdown$Reason;
    invoke-virtual {v5}, Ljava/lang/Enum;->name()Ljava/lang/String;
    move-result-object v9
    invoke-static {v9}, Lcom/navdy/hud/app/ambient/LowVoltagePolicy;->suppress(Ljava/lang/String;)Z
    move-result v10
    if-eqz v10, :shutdown_reason_allowed
    return-void
    :shutdown_reason_allowed
    invoke-static {v9}, Lcom/navdy/hud/app/ambient/LowVoltagePolicy;->canWaitForOff(Ljava/lang/String;)Z
    move-result v10
    if-eqz v10, :ambient_done
    iget-boolean v10, p0, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver$ShutdownRunnable;->ambientPrepared:Z
    if-nez v10, :ambient_done
    const/4 v10, 0x1
    iput-boolean v10, p0, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver$ShutdownRunnable;->ambientPrepared:Z
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->prepareShutdown(Ljava/lang/Runnable;)Z
    move-result v10
    if-eqz v10, :ambient_done
    return-void
    :ambient_done


    .line 362
    .local v5, "reason":Lcom/navdy/hud/app/event/Shutdown$Reason;
    invoke-static {}, Lcom/navdy/hud/app/HudApplication;->getApplication()Lcom/navdy/hud/app/HudApplication;

    move-result-object v9

    invoke-virtual {v9, v5}, Lcom/navdy/hud/app/HudApplication;->setShutdownReason(Lcom/navdy/hud/app/event/Shutdown$Reason;)V

    .line 365
    iget-object v9, p0, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver$ShutdownRunnable;->this$Anon1:Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;

    iget-object v9, v9, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;->this$Anon0:Lcom/navdy/hud/app/service/ShutdownMonitor;

    iget-object v9, v9, Lcom/navdy/hud/app/service/ShutdownMonitor;->powerManager:Lcom/navdy/hud/app/device/PowerManager;

    invoke-virtual {v9}, Lcom/navdy/hud/app/device/PowerManager;->quietModeEnabled()Z

    move-result v9

    if-nez v9, :cond_1

    move v4, v7

    .line 366
    .local v4, "fullShutdown":Z
    :goto_0
    iget-object v9, p0, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver$ShutdownRunnable;->this$Anon1:Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;

    iget-object v9, v9, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;->this$Anon0:Lcom/navdy/hud/app/service/ShutdownMonitor;

    invoke-static {v9}, Lcom/navdy/hud/app/service/ShutdownMonitor;->access$Anon800(Lcom/navdy/hud/app/service/ShutdownMonitor;)Lcom/navdy/hud/app/obd/ObdManager;

    move-result-object v9

    invoke-virtual {v9}, Lcom/navdy/hud/app/obd/ObdManager;->getBatteryVoltage()D

    move-result-wide v2

    .line 367
    .local v2, "batteryVoltage":D
    iget-object v9, p0, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver$ShutdownRunnable;->this$Anon1:Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;

    iget-object v9, v9, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;->this$Anon0:Lcom/navdy/hud/app/service/ShutdownMonitor;

    invoke-static {v9}, Lcom/navdy/hud/app/service/ShutdownMonitor;->access$Anon800(Lcom/navdy/hud/app/service/ShutdownMonitor;)Lcom/navdy/hud/app/obd/ObdManager;

    move-result-object v9

    invoke-virtual {v9}, Lcom/navdy/hud/app/obd/ObdManager;->getObdDeviceConfigurationManager()Lcom/navdy/hud/app/obd/ObdDeviceConfigurationManager;

    move-result-object v9

    invoke-virtual {v9}, Lcom/navdy/hud/app/obd/ObdDeviceConfigurationManager;->isAutoOnEnabled()Z

    move-result v0

    .line 369
    .local v0, "autoOnEnabled":Z
    iget-object v9, p0, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver$ShutdownRunnable;->this$Anon1:Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;

    iget-object v9, v9, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;->this$Anon0:Lcom/navdy/hud/app/service/ShutdownMonitor;

    invoke-static {v9}, Lcom/navdy/hud/app/service/ShutdownMonitor;->access$Anon800(Lcom/navdy/hud/app/service/ShutdownMonitor;)Lcom/navdy/hud/app/obd/ObdManager;

    move-result-object v9

    invoke-virtual {v9}, Lcom/navdy/hud/app/obd/ObdManager;->getConnectionType()Lcom/navdy/hud/app/obd/ObdManager$ConnectionType;

    move-result-object v9

    sget-object v10, Lcom/navdy/hud/app/obd/ObdManager$ConnectionType;->POWER_ONLY:Lcom/navdy/hud/app/obd/ObdManager$ConnectionType;

    if-ne v9, v10, :cond_2

    move v6, v7

    .line 370
    .local v6, "usingCLA":Z
    :goto_1
    const-wide v10, 0x402a333340000000L    # 13.100000381469727

    cmpl-double v9, v2, v10

    if-ltz v9, :cond_3

    move v1, v7

    .line 372
    .local v1, "charging":Z
    :goto_2
    sget-object v7, Lcom/navdy/hud/app/service/ShutdownMonitor$Anon4;->$SwitchMap$com$navdy$hud$app$event$Shutdown$Reason:[I

    invoke-virtual {v5}, Lcom/navdy/hud/app/event/Shutdown$Reason;->ordinal()I

    move-result v8

    aget v7, v7, v8

    packed-switch v7, :pswitch_data_0

    .line 384
    :goto_3
    invoke-static {}, Lcom/navdy/hud/app/service/ShutdownMonitor;->access$Anon100()Lcom/navdy/service/library/log/Logger;

    move-result-object v7

    new-instance v8, Ljava/lang/StringBuilder;

    invoke-direct {v8}, Ljava/lang/StringBuilder;-><init>()V

    const-string v9, "Shutting down, auto-on:"

    invoke-virtual {v8, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v8

    invoke-virtual {v8, v0}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v8

    const-string v9, " voltage:"

    invoke-virtual {v8, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v8

    invoke-virtual {v8, v2, v3}, Ljava/lang/StringBuilder;->append(D)Ljava/lang/StringBuilder;

    move-result-object v8

    const-string v9, " usingCLA:"

    invoke-virtual {v8, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v8

    invoke-virtual {v8, v6}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v8

    const-string v9, " charging:"

    invoke-virtual {v8, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v8

    invoke-virtual {v8, v1}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v8

    invoke-virtual {v8}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v8

    invoke-virtual {v7, v8}, Lcom/navdy/service/library/log/Logger;->i(Ljava/lang/String;)V

    .line 386
    if-eqz v0, :cond_4

    if-nez v6, :cond_4

    .line 390
    iget-object v7, p0, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver$ShutdownRunnable;->this$Anon1:Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;

    iget-object v7, v7, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;->this$Anon0:Lcom/navdy/hud/app/service/ShutdownMonitor;

    invoke-static {v7}, Lcom/navdy/hud/app/service/ShutdownMonitor;->access$Anon800(Lcom/navdy/hud/app/service/ShutdownMonitor;)Lcom/navdy/hud/app/obd/ObdManager;

    move-result-object v7

    invoke-virtual {v7}, Lcom/navdy/hud/app/obd/ObdManager;->isSleeping()Z

    move-result v7

    if-eqz v7, :cond_0

    .line 391
    iget-object v7, p0, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver$ShutdownRunnable;->this$Anon1:Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;

    iget-object v7, v7, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;->this$Anon0:Lcom/navdy/hud/app/service/ShutdownMonitor;

    invoke-static {v7}, Lcom/navdy/hud/app/service/ShutdownMonitor;->access$Anon800(Lcom/navdy/hud/app/service/ShutdownMonitor;)Lcom/navdy/hud/app/obd/ObdManager;

    move-result-object v7

    invoke-virtual {v7}, Lcom/navdy/hud/app/obd/ObdManager;->wakeup()V

    .line 392
    const/16 v7, 0x3e8

    invoke-static {v7}, Lcom/navdy/hud/app/util/GenericUtil;->sleep(I)V

    .line 394
    :cond_0
    iget-object v7, p0, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver$ShutdownRunnable;->this$Anon1:Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;

    iget-object v7, v7, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;->this$Anon0:Lcom/navdy/hud/app/service/ShutdownMonitor;

    invoke-static {v7}, Lcom/navdy/hud/app/service/ShutdownMonitor;->access$Anon800(Lcom/navdy/hud/app/service/ShutdownMonitor;)Lcom/navdy/hud/app/obd/ObdManager;

    move-result-object v7

    invoke-virtual {v7, v4}, Lcom/navdy/hud/app/obd/ObdManager;->sleep(Z)V

    .line 399
    :goto_4
    iget-object v7, p0, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver$ShutdownRunnable;->this$Anon1:Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;

    iget-object v7, v7, Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver;->this$Anon0:Lcom/navdy/hud/app/service/ShutdownMonitor;

    iget-object v7, v7, Lcom/navdy/hud/app/service/ShutdownMonitor;->powerManager:Lcom/navdy/hud/app/device/PowerManager;

    invoke-virtual {v7, v5, v4}, Lcom/navdy/hud/app/device/PowerManager;->androidShutdown(Lcom/navdy/hud/app/event/Shutdown$Reason;Z)V

    .line 400
    return-void

    .end local v0    # "autoOnEnabled":Z
    .end local v1    # "charging":Z
    .end local v2    # "batteryVoltage":D
    .end local v4    # "fullShutdown":Z
    .end local v6    # "usingCLA":Z
    :cond_1
    move v4, v8

    .line 365
    goto/16 :goto_0

    .restart local v0    # "autoOnEnabled":Z
    .restart local v2    # "batteryVoltage":D
    .restart local v4    # "fullShutdown":Z
    :cond_2
    move v6, v8

    .line 369
    goto/16 :goto_1

    .restart local v6    # "usingCLA":Z
    :cond_3
    move v1, v8

    .line 370
    goto/16 :goto_2

    .line 380
    .restart local v1    # "charging":Z
    :pswitch_0
    const/4 v4, 0x1

    goto :goto_3

    .line 396
    :cond_4
    const/4 v4, 0x1

    goto :goto_4

    .line 372
    :pswitch_data_0
    .packed-switch 0x1
        :pswitch_0
        :pswitch_0
        :pswitch_0
        :pswitch_0
        :pswitch_0
    .end packed-switch
.end method
