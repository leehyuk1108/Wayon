.class Lcom/navdy/hud/app/ambient/AmbientLightController$17;
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

    .line 422
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$17;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 5

    .line 425
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$17;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_0

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v0

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$17;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$8500(Lcom/navdy/hud/app/ambient/AmbientLightController;)J

    move-result-wide v2

    cmp-long v4, v0, v2

    if-ltz v4, :cond_0

    .line 426
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$17;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const-string v1, "expired"

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$8600(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V

    .line 428
    :cond_0
    return-void
.end method
