.class Lcom/navdy/hud/app/ambient/AmbientLightController$12;
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

    .line 336
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 8

    .line 339
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 340
    return-void

    .line 342
    :cond_0
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5100(Lcom/navdy/hud/app/ambient/AmbientLightController;)J

    move-result-wide v2

    sub-long/2addr v0, v2

    .line 343
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5200(Lcom/navdy/hud/app/ambient/AmbientLightController;)J

    move-result-wide v2

    const-wide/16 v4, 0x0

    const/high16 v6, 0x3f800000    # 1.0f

    cmp-long v7, v2, v4

    if-lez v7, :cond_1

    .line 344
    long-to-float v0, v0

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5200(Lcom/navdy/hud/app/ambient/AmbientLightController;)J

    move-result-wide v1

    long-to-float v1, v1

    div-float/2addr v0, v1

    invoke-static {v6, v0}, Ljava/lang/Math;->min(FF)F

    move-result v0

    goto :goto_0

    :cond_1
    const/high16 v0, 0x3f800000    # 1.0f

    .line 345
    :goto_0
    mul-float v1, v0, v0

    const/high16 v2, 0x40000000    # 2.0f

    mul-float v2, v2, v0

    const/high16 v3, 0x40400000    # 3.0f

    sub-float/2addr v3, v2

    mul-float v1, v1, v3

    .line 346
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v2

    int-to-float v2, v2

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 347
    invoke-static {v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v3

    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v4

    sub-int/2addr v3, v4

    int-to-float v3, v3

    mul-float v3, v3, v1

    add-float/2addr v2, v3

    .line 346
    invoke-static {v2}, Ljava/lang/Math;->round(F)I

    move-result v2

    .line 348
    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5500(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v3

    int-to-float v3, v3

    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 349
    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5600(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v4

    iget-object v5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5500(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v5

    sub-int/2addr v4, v5

    int-to-float v4, v4

    mul-float v4, v4, v1

    add-float/2addr v3, v4

    .line 348
    invoke-static {v3}, Ljava/lang/Math;->round(F)I

    move-result v1

    .line 350
    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    cmpl-float v4, v0, v6

    if-ltz v4, :cond_2

    const/4 v4, 0x1

    goto :goto_1

    :cond_2
    const/4 v4, 0x0

    :goto_1
    invoke-static {v3, v2, v1, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5700(Lcom/navdy/hud/app/ambient/AmbientLightController;IIZ)V

    .line 351
    cmpg-float v0, v0, v6

    if-gez v0, :cond_3

    .line 352
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5800(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v1

    int-to-long v1, v1

    invoke-virtual {v0, p0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 354
    :cond_3
    return-void
.end method
