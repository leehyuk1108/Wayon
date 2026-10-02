.class Lcom/navdy/hud/app/ambient/AmbientGattSession$1;
.super Ljava/lang/Object;
.source "AmbientGattSession.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Lcom/navdy/hud/app/ambient/AmbientGattSession;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/ambient/AmbientGattSession;)V
    .locals 0
    .annotation system Ldalvik/annotation/MethodParameters;
        accessFlags = {
            0x8010
        }
        names = {
            null
        }
    .end annotation

    .line 35
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 1

    .line 36
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$000(Lcom/navdy/hud/app/ambient/AmbientGattSession;)[B

    move-result-object v0

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$100([B)Z

    move-result v0

    if-eqz v0, :cond_0

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-virtual {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->deliveryTimeout()V

    .line 37
    :cond_0
    return-void
.end method
