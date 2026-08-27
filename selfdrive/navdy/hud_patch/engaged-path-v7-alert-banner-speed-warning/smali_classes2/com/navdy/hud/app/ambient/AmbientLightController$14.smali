.class Lcom/navdy/hud/app/ambient/AmbientLightController$14;
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

    .line 403
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 2

    .line 406
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-nez v0, :cond_0

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6400(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 407
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v1, 0x1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 408
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const-string v1, "offroad door max-on timeout"

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6700(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V

    .line 410
    :cond_0
    return-void
.end method
