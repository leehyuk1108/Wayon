.class Lcom/navdy/hud/app/ambient/AmbientGattSession$2;
.super Ljava/lang/Object;
.source "AmbientGattSession.java"

# interfaces
.implements Lcom/navdy/hud/app/ambient/AmbientWriteLane$Failure;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/navdy/hud/app/ambient/AmbientGattSession;->attach(Landroid/bluetooth/BluetoothGatt;)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

.field final synthetic val$attached:Landroid/bluetooth/BluetoothGatt;


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;)V
    .locals 0
    .annotation system Ldalvik/annotation/MethodParameters;
        accessFlags = {
            0x8010,
            0x1010
        }
        names = {
            null,
            null
        }
    .end annotation

    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 74
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$2;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    iput-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$2;->val$attached:Landroid/bluetooth/BluetoothGatt;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public failed(Ljava/lang/String;)V
    .locals 3

    .line 75
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$2;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$2;->val$attached:Landroid/bluetooth/BluetoothGatt;

    const/16 v2, 0x85

    invoke-static {v0, v1, v2, p1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$200(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;ILjava/lang/String;)V

    return-void
.end method

.method public submitted([B)V
    .locals 3

    .line 77
    array-length v0, p1

    const/4 v1, 0x1

    if-le v0, v1, :cond_0

    .line 78
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$2;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$400(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/os/Handler;

    move-result-object v0

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$2;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$300(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Ljava/lang/Runnable;

    move-result-object v2

    invoke-virtual {v0, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 79
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$2;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$502(Lcom/navdy/hud/app/ambient/AmbientGattSession;Z)Z

    .line 80
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$2;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v0, p1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$002(Lcom/navdy/hud/app/ambient/AmbientGattSession;[B)[B

    .line 81
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$100([B)Z

    move-result p1

    if-eqz p1, :cond_0

    .line 82
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$2;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    const-string v0, "off submitted; awaiting module response"

    invoke-static {p1, v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$600(Lcom/navdy/hud/app/ambient/AmbientGattSession;Ljava/lang/String;)V

    .line 84
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$2;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$400(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/os/Handler;

    move-result-object p1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$2;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$300(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Ljava/lang/Runnable;

    move-result-object v0

    const-wide/16 v1, 0x5dc

    invoke-virtual {p1, v0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 87
    :cond_0
    return-void
.end method
