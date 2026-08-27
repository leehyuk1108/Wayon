.class Lcom/navdy/hud/app/ambient/AmbientLightController$10;
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

    .line 316
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$10;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 3

    .line 319
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$10;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$10;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3500(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_0

    goto :goto_0

    .line 322
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$10;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v1, 0x0

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4800(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V

    .line 323
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$10;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    const-wide/16 v1, 0x1388

    invoke-virtual {v0, p0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 324
    return-void

    .line 320
    :cond_1
    :goto_0
    return-void
.end method
