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

    .line 383
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 5

    .line 386
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-nez v0, :cond_1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-nez v0, :cond_1

    .line 387
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v1, 0x0

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7702(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 388
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 389
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v1

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$8000(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v2

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$8100(Lcom/navdy/hud/app/ambient/AmbientLightController;)J

    move-result-wide v3

    invoke-static {v0, v1, v2, v3, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$8200(Lcom/navdy/hud/app/ambient/AmbientLightController;IIJ)V

    goto :goto_0

    .line 391
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$8100(Lcom/navdy/hud/app/ambient/AmbientLightController;)J

    move-result-wide v2

    invoke-static {v0, v1, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$8200(Lcom/navdy/hud/app/ambient/AmbientLightController;IIJ)V

    .line 394
    :cond_1
    :goto_0
    return-void
.end method
