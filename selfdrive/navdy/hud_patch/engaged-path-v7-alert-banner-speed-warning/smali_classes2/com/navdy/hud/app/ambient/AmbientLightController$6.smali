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

    .line 203
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 3

    .line 206
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_4

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3400(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_0

    goto :goto_2

    .line 209
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3500(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    const/4 v1, 0x3

    const/4 v2, 0x1

    if-gt v0, v1, :cond_1

    .line 210
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-nez v0, :cond_3

    .line 211
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3700()[B

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3800(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 212
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    goto :goto_1

    .line 215
    :cond_1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v1

    if-eqz v1, :cond_2

    invoke-static {}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3900()[B

    move-result-object v1

    goto :goto_0

    :cond_2
    invoke-static {}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3700()[B

    move-result-object v1

    :goto_0
    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3800(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V

    .line 216
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v1

    xor-int/2addr v1, v2

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 218
    :cond_3
    :goto_1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    const-wide/16 v1, 0xbb8

    invoke-virtual {v0, p0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 219
    return-void

    .line 207
    :cond_4
    :goto_2
    return-void
.end method
