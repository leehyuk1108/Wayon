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

    .line 208
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 8

    .line 211
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_e

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3400(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_0

    goto/16 :goto_5

    .line 214
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3500(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    .line 215
    const/16 v1, 0x8

    const/16 v2, 0x28

    const/4 v3, 0x2

    const/4 v4, 0x0

    const/4 v5, 0x1

    if-ge v0, v1, :cond_5

    .line 216
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v1

    if-eqz v1, :cond_3

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v1

    if-nez v1, :cond_1

    goto :goto_0

    .line 223
    :cond_1
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v1

    if-ltz v1, :cond_2

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 224
    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v1

    sub-int v1, v0, v1

    invoke-static {v1}, Ljava/lang/Math;->abs(I)I

    move-result v1

    if-lt v1, v3, :cond_4

    .line 225
    :cond_2
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v5, v0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4000(ZII)[B

    move-result-object v2

    invoke-static {v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    goto :goto_1

    .line 217
    :cond_3
    :goto_0
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3800()[B

    move-result-object v3

    invoke-static {v1, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 218
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v5, v0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4000(ZII)[B

    move-result-object v2

    invoke-static {v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 219
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 220
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3702(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 221
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4102(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 222
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4202(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 227
    :cond_4
    :goto_1
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4302(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 228
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    const-wide/16 v1, 0x3e8

    invoke-virtual {v0, p0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 229
    return-void

    .line 232
    :cond_5
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v1

    if-eqz v1, :cond_6

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v1

    if-eqz v1, :cond_7

    .line 233
    :cond_6
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4400()[B

    move-result-object v6

    invoke-static {v1, v6}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 234
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 235
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3702(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 236
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4102(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 237
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4202(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 240
    :cond_7
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4100(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v1

    const/4 v6, 0x5

    if-eqz v1, :cond_9

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4100(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v1

    if-ne v1, v3, :cond_8

    goto :goto_2

    .line 241
    :cond_8
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4200(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v1

    goto :goto_3

    :cond_9
    :goto_2
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4200(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v1

    rsub-int/lit8 v1, v1, 0x5

    .line 242
    :goto_3
    mul-int v1, v1, v0

    add-int/2addr v1, v3

    div-int/2addr v1, v6

    .line 243
    iget-object v7, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v5, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4000(ZII)[B

    move-result-object v1

    invoke-static {v7, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 244
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4302(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 246
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4208(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    .line 247
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4200(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-le v0, v6, :cond_d

    .line 248
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4202(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 249
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4100(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-nez v0, :cond_a

    .line 250
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4102(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 251
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3800()[B

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    goto :goto_4

    .line 252
    :cond_a
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4100(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v5, :cond_b

    .line 253
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4102(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    goto :goto_4

    .line 254
    :cond_b
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4100(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    if-ne v0, v3, :cond_c

    .line 255
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v1, 0x3

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4102(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 256
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4400()[B

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    goto :goto_4

    .line 258
    :cond_c
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4102(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I

    .line 261
    :cond_d
    :goto_4
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    const-wide/16 v1, 0x1c2

    invoke-virtual {v0, p0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 262
    return-void

    .line 212
    :cond_e
    :goto_5
    return-void
.end method
