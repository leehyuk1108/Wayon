.class Lcom/navdy/hud/app/ambient/AmbientLightController$18;
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

    .line 431
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 5

    .line 434
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$8700(Lcom/navdy/hud/app/ambient/AmbientLightController;)J

    move-result-wide v2

    sub-long/2addr v0, v2

    .line 435
    const-wide/16 v2, 0xbb8

    cmp-long v4, v0, v2

    if-gez v4, :cond_0

    .line 436
    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v4

    sub-long/2addr v2, v0

    invoke-virtual {v4, p0, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 437
    return-void

    .line 439
    :cond_0
    const-string v0, "NavdyAmbient"

    const-string v1, "comma vehicle data timeout; fading ambient off"

    invoke-static {v0, v1}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 440
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v1, 0x1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5002(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 441
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v1, 0x0

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$8802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 442
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4902(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 443
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 444
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 445
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$8900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object v2

    invoke-virtual {v0, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 446
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3702(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 447
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const-wide/16 v2, 0x0

    invoke-static {v0, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$9002(Lcom/navdy/hud/app/ambient/AmbientLightController;J)J

    .line 448
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$9100(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 449
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$9200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 450
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$9300(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 451
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$9400(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 452
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_1

    .line 453
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const-string v1, "comma data timeout in reverse"

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$8400(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V

    goto :goto_0

    .line 455
    :cond_1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const-wide/16 v2, 0x3e8

    invoke-static {v0, v1, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$8200(Lcom/navdy/hud/app/ambient/AmbientLightController;IIJ)V

    .line 457
    :goto_0
    return-void
.end method
