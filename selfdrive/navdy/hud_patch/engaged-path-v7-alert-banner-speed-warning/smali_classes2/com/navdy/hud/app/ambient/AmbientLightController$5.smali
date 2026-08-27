.class Lcom/navdy/hud/app/ambient/AmbientLightController$5;
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

    .line 231
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$5;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 2

    .line 234
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$5;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3500(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$5;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v1

    if-eq v0, v1, :cond_0

    .line 235
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$5;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$5;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3500(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3700(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V

    .line 237
    :cond_0
    return-void
.end method
