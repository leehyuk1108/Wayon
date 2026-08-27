.class Lcom/navdy/hud/app/ambient/AmbientLightController$6;
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

    .line 209
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 9

    .line 212
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    const/4 v1, 0x4

    const/4 v2, 0x0

    const/4 v3, 0x1

    const/4 v4, 0x3

    if-eq v0, v4, :cond_1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 213
    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v1, :cond_0

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    goto :goto_1

    :cond_1
    :goto_0
    const/4 v0, 0x1

    .line 214
    :goto_1
    iget-object v5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v5

    if-nez v5, :cond_2

    if-eqz v0, :cond_3

    :cond_2
    iget-object v5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3500(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v5

    if-eqz v5, :cond_4

    .line 215
    :cond_3
    return-void

    .line 217
    :cond_4
    iget-object v5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3600(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v5

    .line 218
    const/16 v6, 0x28

    const/4 v7, 0x2

    if-nez v0, :cond_9

    const/16 v0, 0x8

    if-ge v5, v0, :cond_9

    .line 219
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_7

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-nez v0, :cond_5

    goto :goto_2

    .line 227
    :cond_5
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ltz v0, :cond_6

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 228
    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    sub-int v0, v5, v0

    invoke-static {v0}, Ljava/lang/Math;->abs(I)I

    move-result v0

    if-lt v0, v7, :cond_8

    .line 229
    :cond_6
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3, v5, v6}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4100(ZII)[B

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4000(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    goto :goto_3

    .line 220
    :cond_7
    :goto_2
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900()[B

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4000(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 221
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3, v5, v6}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4100(ZII)[B

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4000(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 222
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3702(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 223
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 224
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 225
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v7}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3402(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 226
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v7}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4302(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 231
    :cond_8
    :goto_3
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4402(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 232
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    const-wide/16 v1, 0x3e8

    invoke-virtual {v0, p0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 233
    return-void

    .line 236
    :cond_9
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-nez v0, :cond_a

    .line 237
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4500()[B

    move-result-object v8

    invoke-static {v0, v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4000(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 238
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3702(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 239
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 240
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 241
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3402(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 242
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v7}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4302(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    goto :goto_4

    .line 243
    :cond_a
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_b

    .line 245
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 246
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 247
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v7}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3402(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 248
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v7}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4302(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 251
    :cond_b
    :goto_4
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-eqz v0, :cond_d

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 252
    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-eq v0, v7, :cond_d

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 253
    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v4, :cond_c

    goto :goto_5

    .line 256
    :cond_c
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v8, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v8

    add-int/2addr v8, v3

    invoke-static {v7, v8}, Ljava/lang/Math;->min(II)I

    move-result v8

    invoke-static {v0, v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4302(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    goto :goto_6

    .line 254
    :cond_d
    :goto_5
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v8, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v8

    sub-int/2addr v8, v3

    invoke-static {v2, v8}, Ljava/lang/Math;->max(II)I

    move-result v8

    invoke-static {v0, v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4302(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 259
    :goto_6
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    mul-int v0, v0, v5

    add-int/2addr v0, v3

    div-int/2addr v0, v7

    .line 260
    iget-object v8, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3, v0, v6}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4100(ZII)[B

    move-result-object v0

    invoke-static {v8, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4000(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 261
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4402(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 263
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-nez v0, :cond_e

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-nez v0, :cond_e

    .line 264
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3402(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 265
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 266
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900()[B

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4000(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    goto :goto_7

    .line 267
    :cond_e
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v3, :cond_f

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v7, :cond_f

    .line 268
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v7}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3402(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    goto :goto_7

    .line 269
    :cond_f
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v7, :cond_10

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-nez v0, :cond_10

    .line 271
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3402(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    goto :goto_7

    .line 272
    :cond_10
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v4, :cond_11

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-nez v0, :cond_11

    .line 273
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3402(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 274
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 275
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4500()[B

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4000(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    goto :goto_7

    .line 276
    :cond_11
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v1, :cond_12

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v7, :cond_12

    .line 277
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4600(Lcom/navdy/hud/app/ambient/AmbientLightController;I)V

    .line 278
    return-void

    .line 280
    :cond_12
    :goto_7
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    const-wide/16 v1, 0x15e

    invoke-virtual {v0, p0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 281
    return-void
.end method
