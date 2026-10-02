.class Lcom/navdy/hud/app/ambient/AmbientWriteLane$1;
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

    .line 21
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 1

    .line 21
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->access$000(Lcom/navdy/hud/app/ambient/AmbientWriteLane;)V

    return-void
.end method
