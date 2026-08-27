.class Lcom/navdy/hud/app/ambient/AmbientLightController$9;
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

    .line 342
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$9;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 2

    .line 345
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$9;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-nez v0, :cond_0

    .line 346
    return-void

    .line 348
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$9;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$9;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object v1

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 349
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$9;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v1, 0x0

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 350
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$9;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 351
    return-void
.end method
