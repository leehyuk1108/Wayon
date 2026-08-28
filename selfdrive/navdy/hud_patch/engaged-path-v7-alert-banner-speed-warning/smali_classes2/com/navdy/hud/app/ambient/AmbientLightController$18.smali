.class Lcom/navdy/hud/app/ambient/AmbientLightController$18;
.super Ljava/lang/Object;
.source "AmbientLightController.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/navdy/hud/app/ambient/AmbientLightController;->onGearText(Landroid/content/Context;Ljava/lang/String;)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

.field final synthetic val$gear:Ljava/lang/String;


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V
    .locals 0
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 514
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iput-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->val$gear:Ljava/lang/String;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 2

    .line 517
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;->val$gear:Ljava/lang/String;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7400(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V

    .line 518
    return-void
.end method
