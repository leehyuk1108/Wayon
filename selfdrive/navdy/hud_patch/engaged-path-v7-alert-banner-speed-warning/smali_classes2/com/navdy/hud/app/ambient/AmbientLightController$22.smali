.class Lcom/navdy/hud/app/ambient/AmbientLightController$22;
.super Ljava/lang/Object;
.source "AmbientLightController.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/navdy/hud/app/ambient/AmbientLightController;->onCameraSpeedChanged(Landroid/content/Context;II)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

.field final synthetic val$limit:I

.field final synthetic val$speed:I


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/ambient/AmbientLightController;II)V
    .locals 0
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 624
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$22;->val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iput p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$22;->val$speed:I

    iput p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$22;->val$limit:I

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 3

    .line 627
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$22;->val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$22;->val$speed:I

    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$22;->val$limit:I

    invoke-static {v0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$10000(Lcom/navdy/hud/app/ambient/AmbientLightController;II)V

    .line 628
    return-void
.end method
