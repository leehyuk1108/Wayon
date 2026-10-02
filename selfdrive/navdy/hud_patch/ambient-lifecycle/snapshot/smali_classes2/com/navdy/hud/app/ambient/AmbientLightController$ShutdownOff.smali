.class final Lcom/navdy/hud/app/ambient/AmbientLightController$ShutdownOff;
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;
.field private final owner:Lcom/navdy/hud/app/ambient/AmbientLightController;
.field private final continuation:Ljava/lang/Runnable;
.method public constructor <init>(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/Runnable;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$ShutdownOff;->owner:Lcom/navdy/hud/app/ambient/AmbientLightController;
    iput-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$ShutdownOff;->continuation:Ljava/lang/Runnable;
    return-void
.end method
.method public run()V
    .locals 2
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$ShutdownOff;->owner:Lcom/navdy/hud/app/ambient/AmbientLightController;
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$ShutdownOff;->continuation:Ljava/lang/Runnable;
    invoke-virtual {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->shutdownOff(Ljava/lang/Runnable;)V
    return-void
.end method
