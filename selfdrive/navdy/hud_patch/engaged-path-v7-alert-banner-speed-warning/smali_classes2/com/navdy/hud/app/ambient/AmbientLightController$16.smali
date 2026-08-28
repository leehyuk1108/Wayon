.class Lcom/navdy/hud/app/ambient/AmbientLightController$16;
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

    .line 385
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 5

    .line 388
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6400(Lcom/navdy/hud/app/ambient/AmbientLightController;)J

    move-result-wide v2

    sub-long/2addr v0, v2

    .line 389
    const-wide/16 v2, 0xbb8

    cmp-long v4, v0, v2

    if-gez v4, :cond_0

    .line 390
    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v4

    sub-long/2addr v2, v0

    invoke-virtual {v4, p0, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 391
    return-void

    .line 393
    :cond_0
    const-string v0, "NavdyAmbient"

    const-string v1, "comma vehicle data timeout; fading ambient off"

    invoke-static {v0, v1}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 394
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v1, 0x1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 395
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v1, 0x0

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 396
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5902(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 397
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6002(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 398
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 399
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object v2

    invoke-virtual {v0, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 400
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3702(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 401
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const-wide/16 v2, 0x0

    invoke-static {v0, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6802(Lcom/navdy/hud/app/ambient/AmbientLightController;J)J

    .line 402
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6900(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 403
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7000(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 404
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7100(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 405
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 406
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_1

    .line 407
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const-string v1, "comma data timeout in reverse"

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6300(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V

    goto :goto_0

    .line 409
    :cond_1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const-wide/16 v2, 0x3e8

    invoke-static {v0, v1, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6100(Lcom/navdy/hud/app/ambient/AmbientLightController;IIJ)V

    .line 411
    :goto_0
    return-void
.end method
