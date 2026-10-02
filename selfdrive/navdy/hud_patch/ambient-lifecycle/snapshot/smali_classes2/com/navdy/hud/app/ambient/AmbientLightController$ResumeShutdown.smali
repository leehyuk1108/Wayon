.class final Lcom/navdy/hud/app/ambient/AmbientLightController$ResumeShutdown;
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;
.field private final continuation:Ljava/lang/Runnable;
.method public constructor <init>(Ljava/lang/Runnable;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$ResumeShutdown;->continuation:Ljava/lang/Runnable;
    return-void
.end method
.method public run()V
    .locals 3
    invoke-static {}, Lcom/navdy/service/library/task/TaskManager;->getInstance()Lcom/navdy/service/library/task/TaskManager;
    move-result-object v0
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$ResumeShutdown;->continuation:Ljava/lang/Runnable;
    const/4 v2, 0x1
    invoke-virtual {v0, v1, v2}, Lcom/navdy/service/library/task/TaskManager;->execute(Ljava/lang/Runnable;I)Ljava/util/concurrent/Future;
    return-void
.end method
