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
    .locals 9

    .line 257
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    const/4 v1, 0x4

    const/4 v2, 0x0

    const/4 v3, 0x1

    const/4 v4, 0x3

    if-eq v0, v4, :cond_1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 258
    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v1, :cond_0

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    goto :goto_1

    :cond_1
    :goto_0
    const/4 v0, 0x1

    .line 259
    :goto_1
    iget-object v5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v5

    if-nez v5, :cond_2

    if-eqz v0, :cond_3

    :cond_2
    iget-object v5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v5

    if-eqz v5, :cond_4

    .line 260
    :cond_3
    return-void

    .line 262
    :cond_4
    iget-object v5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4100(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v5

    .line 263
    const/4 v6, 0x2

    if-nez v0, :cond_9

    const/16 v0, 0x8

    if-ge v5, v0, :cond_9

    .line 264
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_7

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-nez v0, :cond_5

    goto :goto_2

    .line 272
    :cond_5
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5000(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ltz v0, :cond_6

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 273
    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5000(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    sub-int v0, v5, v0

    invoke-static {v0}, Ljava/lang/Math;->abs(I)I

    move-result v0

    if-lt v0, v6, :cond_8

    .line 274
    :cond_6
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4600(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v1

    invoke-static {v3, v5, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4700(ZII)[B

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4500(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    goto :goto_3

    .line 265
    :cond_7
    :goto_2
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4400()[B

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4500(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 266
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4600(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v1

    invoke-static {v3, v5, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4700(ZII)[B

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4500(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 267
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 268
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4302(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 269
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 270
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v6}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3902(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 271
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v6}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4902(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 276
    :cond_8
    :goto_3
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5002(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 277
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    const-wide/16 v1, 0x3e8

    invoke-virtual {v0, p0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 278
    return-void

    .line 281
    :cond_9
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-nez v0, :cond_a

    .line 282
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5100()[B

    move-result-object v7

    invoke-static {v0, v7}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4500(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 283
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 284
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4302(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 285
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 286
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3902(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 287
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v6}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4902(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    goto :goto_4

    .line 288
    :cond_a
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_b

    .line 290
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4302(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 291
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 292
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v6}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3902(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 293
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v6}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4902(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 296
    :cond_b
    :goto_4
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-eqz v0, :cond_d

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 297
    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-eq v0, v6, :cond_d

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 298
    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v4, :cond_c

    goto :goto_5

    .line 301
    :cond_c
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v7, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v7}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v7

    add-int/2addr v7, v3

    invoke-static {v6, v7}, Ljava/lang/Math;->min(II)I

    move-result v7

    invoke-static {v0, v7}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4902(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    goto :goto_6

    .line 299
    :cond_d
    :goto_5
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v7, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v7}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v7

    sub-int/2addr v7, v3

    invoke-static {v2, v7}, Ljava/lang/Math;->max(II)I

    move-result v7

    invoke-static {v0, v7}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4902(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 304
    :goto_6
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    mul-int v0, v0, v5

    add-int/2addr v0, v3

    div-int/2addr v0, v6

    .line 305
    iget-object v7, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v8, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4600(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v8

    invoke-static {v3, v0, v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4700(ZII)[B

    move-result-object v0

    invoke-static {v7, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4500(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 306
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5002(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 308
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-nez v0, :cond_e

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-nez v0, :cond_e

    .line 309
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3902(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 310
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 311
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4400()[B

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4500(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    goto :goto_7

    .line 312
    :cond_e
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v3, :cond_f

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v6, :cond_f

    .line 313
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v6}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3902(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    goto :goto_7

    .line 314
    :cond_f
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v6, :cond_10

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-nez v0, :cond_10

    .line 316
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3902(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    goto :goto_7

    .line 317
    :cond_10
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v4, :cond_11

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-nez v0, :cond_11

    .line 318
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3902(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 319
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 320
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5100()[B

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4500(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    goto :goto_7

    .line 321
    :cond_11
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v1, :cond_12

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v6, :cond_12

    .line 322
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5200(Lcom/navdy/hud/app/ambient/AmbientLightController;I)V

    .line 323
    return-void

    .line 325
    :cond_12
    :goto_7
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    const-wide/16 v1, 0x15e

    invoke-virtual {v0, p0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 326
    return-void
.end method
