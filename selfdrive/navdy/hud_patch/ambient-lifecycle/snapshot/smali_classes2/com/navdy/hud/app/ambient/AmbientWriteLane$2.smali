.class Lcom/navdy/hud/app/ambient/AmbientWriteLane$2;
.super Ljava/lang/Object;
.source "AmbientWriteLane.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Lcom/navdy/hud/app/ambient/AmbientWriteLane;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lcom/navdy/hud/app/ambient/AmbientWriteLane;


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/ambient/AmbientWriteLane;)V
    .locals 0
    .annotation system Ldalvik/annotation/MethodParameters;
        accessFlags = {
            0x8010
        }
        names = {
            null
        }
    .end annotation

    .line 22
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$2;->this$0:Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 2

    .line 23
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$2;->this$0:Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    const-string v1, "ATT write callback timeout"

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->access$100(Lcom/navdy/hud/app/ambient/AmbientWriteLane;Ljava/lang/String;)V

    .line 24
    return-void
.end method
