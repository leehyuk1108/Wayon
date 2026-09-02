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

    .line 341
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 18

    .line 344
    move-object/from16 v0, p0

    iget-object v1, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v1

    if-eqz v1, :cond_0

    .line 345
    return-void

    .line 347
    :cond_0
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v1

    iget-object v3, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5100(Lcom/navdy/hud/app/ambient/AmbientLightController;)J

    move-result-wide v3

    sub-long/2addr v1, v3

    .line 348
    iget-object v3, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5200(Lcom/navdy/hud/app/ambient/AmbientLightController;)J

    move-result-wide v3

    const-wide/16 v5, 0x0

    const/high16 v7, 0x3f800000    # 1.0f

    cmp-long v8, v3, v5

    if-lez v8, :cond_1

    .line 349
    long-to-float v1, v1

    iget-object v2, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5200(Lcom/navdy/hud/app/ambient/AmbientLightController;)J

    move-result-wide v2

    long-to-float v2, v2

    div-float/2addr v1, v2

    invoke-static {v7, v1}, Ljava/lang/Math;->min(FF)F

    move-result v1

    goto :goto_0

    :cond_1
    const/high16 v1, 0x3f800000    # 1.0f

    .line 350
    :goto_0
    mul-float v2, v1, v1

    const/high16 v3, 0x40000000    # 2.0f

    mul-float v3, v3, v1

    const/high16 v4, 0x40400000    # 3.0f

    sub-float/2addr v4, v3

    mul-float v2, v2, v4

    .line 351
    iget-object v3, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v3

    int-to-float v3, v3

    iget-object v4, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 352
    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v4

    iget-object v5, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v5

    sub-int/2addr v4, v5

    int-to-float v4, v4

    mul-float v4, v4, v2

    add-float/2addr v3, v4

    .line 351
    invoke-static {v3}, Ljava/lang/Math;->round(F)I

    move-result v9

    .line 353
    iget-object v3, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5500(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v3

    int-to-float v3, v3

    iget-object v4, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 354
    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5600(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v4

    iget-object v5, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5500(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v5

    sub-int/2addr v4, v5

    int-to-float v4, v4

    mul-float v4, v4, v2

    add-float/2addr v3, v4

    .line 353
    invoke-static {v3}, Ljava/lang/Math;->round(F)I

    move-result v10

    .line 355
    iget-object v3, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5700(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v3

    iget-object v4, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5800(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v4

    invoke-static {v3, v4, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5900(IIF)I

    move-result v11

    .line 356
    iget-object v3, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6000(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v3

    iget-object v4, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6100(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v4

    invoke-static {v3, v4, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5900(IIF)I

    move-result v12

    .line 357
    iget-object v3, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6200(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v3

    iget-object v4, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v4

    invoke-static {v3, v4, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5900(IIF)I

    move-result v13

    .line 358
    iget-object v3, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v3

    iget-object v4, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6500(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v4

    invoke-static {v3, v4, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5900(IIF)I

    move-result v14

    .line 359
    iget-object v3, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6600(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v3

    iget-object v4, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6700(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v4

    invoke-static {v3, v4, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5900(IIF)I

    move-result v15

    .line 360
    iget-object v3, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6800(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v3

    iget-object v4, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v4

    invoke-static {v3, v4, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5900(IIF)I

    move-result v16

    .line 361
    iget-object v8, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    cmpl-float v2, v1, v7

    if-ltz v2, :cond_2

    const/4 v2, 0x1

    const/16 v17, 0x1

    goto :goto_1

    :cond_2
    const/4 v2, 0x0

    const/16 v17, 0x0

    :goto_1
    invoke-static/range {v8 .. v17}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7000(Lcom/navdy/hud/app/ambient/AmbientLightController;IIIIIIIIZ)V

    .line 365
    cmpg-float v1, v1, v7

    if-gez v1, :cond_3

    .line 366
    iget-object v1, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v1

    iget-object v2, v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7100(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v2

    int-to-long v2, v2

    invoke-virtual {v1, v0, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 368
    :cond_3
    return-void
.end method
