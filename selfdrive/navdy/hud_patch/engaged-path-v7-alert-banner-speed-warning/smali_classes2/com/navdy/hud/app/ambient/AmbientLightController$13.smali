.class Lcom/navdy/hud/app/ambient/AmbientLightController$13;
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

    .line 357
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$13;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 4

    .line 360
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$13;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$5900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-nez v0, :cond_0

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$13;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-nez v0, :cond_0

    .line 361
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$13;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const-wide/16 v1, 0x3e8

    const/4 v3, 0x0

    invoke-static {v0, v3, v3, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$6100(Lcom/navdy/hud/app/ambient/AmbientLightController;IIJ)V

    .line 363
    :cond_0
    return-void
.end method
