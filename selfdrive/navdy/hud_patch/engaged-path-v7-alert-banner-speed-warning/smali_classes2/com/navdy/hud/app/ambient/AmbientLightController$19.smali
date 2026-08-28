.class Lcom/navdy/hud/app/ambient/AmbientLightController$19;
.super Ljava/lang/Object;
.source "AmbientLightController.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/navdy/hud/app/ambient/AmbientLightController;->onOverspeedChanged(Landroid/content/Context;Z)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

.field final synthetic val$overspeed:Z


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V
    .locals 0
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 527
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iput-boolean p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$overspeed:Z

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 2

    .line 530
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$overspeed:Z

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7600(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V

    .line 531
    return-void
.end method
