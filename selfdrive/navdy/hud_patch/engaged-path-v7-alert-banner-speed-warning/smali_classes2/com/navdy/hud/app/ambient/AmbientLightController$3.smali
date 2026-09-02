.class Lcom/navdy/hud/app/ambient/AmbientLightController$3;
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

    .line 217
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$3;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 1

    .line 220
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$3;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 221
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$3;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$3400(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 222
    return-void
.end method
