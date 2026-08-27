.class Lcom/navdy/hud/app/ambient/AmbientLightController$15;
.super Ljava/lang/Object;
.source "AmbientLightController.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Lcom/navdy/hud/app/ambient/AmbientLightController;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 408
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 5

    .line 411
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6700(Lcom/navdy/hud/app/ambient/AmbientLightController;)J

    move-result-wide v2

    sub-long/2addr v0, v2

    .line 412
    const-wide/16 v2, 0xbb8

    cmp-long v4, v0, v2

    if-gez v4, :cond_0

    .line 413
    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v4

    sub-long/2addr v2, v0

    invoke-virtual {v4, p0, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 414
    return-void

    .line 416
    :cond_0
    const-string v0, "NavdyAmbient"

    const-string v1, "comma vehicle data timeout; fading ambient off"

    invoke-static {v0, v1}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 417
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v1, 0x1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 418
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v1, 0x0

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6902(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 419
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 420
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6302(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 421
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 422
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object v2

    invoke-virtual {v0, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 423
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 424
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const-wide/16 v2, 0x0

    invoke-static {v0, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7102(Lcom/navdy/hud/app/ambient/AmbientLightController;J)J

    .line 425
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 426
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7300(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 427
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7400(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 428
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 429
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_1

    .line 430
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const-string v1, "comma data timeout in reverse"

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6600(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V

    goto :goto_0

    .line 432
    :cond_1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const-wide/16 v2, 0x3e8

    invoke-static {v0, v1, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6400(Lcom/navdy/hud/app/ambient/AmbientLightController;IIJ)V

    .line 434
    :goto_0
    return-void
.end method
