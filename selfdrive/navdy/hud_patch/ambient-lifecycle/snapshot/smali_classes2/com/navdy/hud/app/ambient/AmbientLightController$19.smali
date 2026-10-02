.class Lcom/navdy/hud/app/ambient/AmbientLightController$19;
.super Ljava/lang/Object;
.source "AmbientLightController.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/navdy/hud/app/ambient/AmbientLightController;->onOpenpilotPayload(Landroid/content/Context;Ljava/lang/String;)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic val$ambientOverride:Lorg/json/JSONObject;

.field final synthetic val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

.field final synthetic val$doorOpen:Z

.field final synthetic val$gear:Ljava/lang/String;

.field final synthetic val$hasDoorOpen:Z

.field final synthetic val$hasOnroad:Z

.field final synthetic val$onroad:Z


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;ZZZZLorg/json/JSONObject;)V
    .locals 0
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 578
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iput-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$gear:Ljava/lang/String;

    iput-boolean p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$hasOnroad:Z

    iput-boolean p4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$hasDoorOpen:Z

    iput-boolean p5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$onroad:Z

    iput-boolean p6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$doorOpen:Z

    iput-object p7, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$ambientOverride:Lorg/json/JSONObject;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 3

    .line 581
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$9600(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 582
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$gear:Ljava/lang/String;

    if-eqz v0, :cond_0

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$gear:Ljava/lang/String;

    invoke-virtual {v0}, Ljava/lang/String;->length()I

    move-result v0

    if-lez v0, :cond_0

    .line 583
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$gear:Ljava/lang/String;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$9700(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V

    .line 585
    :cond_0
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$hasOnroad:Z

    if-nez v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$hasDoorOpen:Z

    if-eqz v0, :cond_6

    .line 586
    :cond_1
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$hasOnroad:Z

    if-eqz v0, :cond_2

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$onroad:Z

    goto :goto_0

    .line 587
    :cond_2
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$8900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    if-eqz v0, :cond_3

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$4900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v0

    goto :goto_0

    :cond_3
    const/4 v0, 0x1

    .line 588
    :goto_0
    iget-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$hasDoorOpen:Z

    if-eqz v1, :cond_4

    iget-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$doorOpen:Z

    goto :goto_1

    .line 589
    :cond_4
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$8900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v1

    if-eqz v1, :cond_5

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$7700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z

    move-result v1

    goto :goto_1

    :cond_5
    const/4 v1, 0x0

    .line 590
    :goto_1
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$9800(Lcom/navdy/hud/app/ambient/AmbientLightController;ZZ)V

    .line 592
    :cond_6
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$ambientOverride:Lorg/json/JSONObject;

    if-eqz v0, :cond_7

    .line 593
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$controller:Lcom/navdy/hud/app/ambient/AmbientLightController;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$19;->val$ambientOverride:Lorg/json/JSONObject;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$9900(Lcom/navdy/hud/app/ambient/AmbientLightController;Lorg/json/JSONObject;)V

    .line 595
    :cond_7
    return-void
.end method
