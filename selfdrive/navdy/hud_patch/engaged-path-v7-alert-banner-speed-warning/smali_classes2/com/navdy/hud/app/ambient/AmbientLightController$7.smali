.class Lcom/navdy/hud/app/ambient/AmbientLightController$7;
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

    .line 254
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 5

    .line 257
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_9

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_0

    goto/16 :goto_4

    .line 260
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4000(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    .line 261
    const/16 v1, 0x8

    const/4 v2, 0x0

    const/4 v3, 0x1

    if-ge v0, v1, :cond_5

    .line 262
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v1

    if-eqz v1, :cond_3

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v1

    if-nez v1, :cond_1

    goto :goto_0

    .line 268
    :cond_1
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4800(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v1

    if-ltz v1, :cond_2

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 269
    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4800(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v1

    sub-int v1, v0, v1

    invoke-static {v1}, Ljava/lang/Math;->abs(I)I

    move-result v1

    const/4 v2, 0x2

    if-lt v1, v2, :cond_4

    .line 270
    :cond_2
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4500(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v2

    invoke-static {v3, v0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4600(ZII)[B

    move-result-object v2

    invoke-static {v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4400(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    goto :goto_1

    .line 263
    :cond_3
    :goto_0
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)[B

    move-result-object v4

    invoke-static {v1, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4400(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 264
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4500(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v4

    invoke-static {v3, v0, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4600(ZII)[B

    move-result-object v4

    invoke-static {v1, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4400(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 265
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4102(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 266
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 267
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4702(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 272
    :cond_4
    :goto_1
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4802(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 273
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    const-wide/16 v1, 0x3e8

    invoke-virtual {v0, p0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 274
    return-void

    .line 277
    :cond_5
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v1

    if-nez v1, :cond_6

    .line 278
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)[B

    move-result-object v4

    invoke-static {v1, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4400(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 279
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4102(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 280
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 281
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4702(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    goto :goto_2

    .line 282
    :cond_6
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v1

    if-eqz v1, :cond_7

    .line 283
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 284
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4702(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 287
    :cond_7
    :goto_2
    mul-int/lit8 v1, v0, 0x2d

    add-int/lit8 v1, v1, 0x32

    div-int/lit8 v1, v1, 0x64

    invoke-static {v3, v1}, Ljava/lang/Math;->max(II)I

    move-result v1

    .line 289
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v2

    if-eqz v2, :cond_8

    goto :goto_3

    :cond_8
    move v1, v0

    .line 290
    :goto_3
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4500(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v4

    invoke-static {v3, v1, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4600(ZII)[B

    move-result-object v1

    invoke-static {v2, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4400(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 291
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4802(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 292
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v1

    xor-int/2addr v1, v3

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4702(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 293
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    const-wide/16 v1, 0x2bc

    invoke-virtual {v0, p0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 294
    return-void

    .line 258
    :cond_9
    :goto_4
    return-void
.end method
