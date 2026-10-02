.class Lcom/navdy/hud/app/ambient/AmbientGattSession$3;
.super Ljava/lang/Object;
.source "AmbientGattSession.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/navdy/hud/app/ambient/AmbientGattSession;->onConnectionStateChange(Landroid/bluetooth/BluetoothGatt;II)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

.field final synthetic val$gatt:Landroid/bluetooth/BluetoothGatt;

.field final synthetic val$state:I

.field final synthetic val$status:I


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;II)V
    .locals 0
    .annotation system Ldalvik/annotation/MethodParameters;
        accessFlags = {
            0x8010,
            0x1010,
            0x1010,
            0x1010
        }
        names = {
            null,
            null,
            null,
            null
        }
    .end annotation

    .annotation system Ldalvik/annotation/Signature;
        value = {
            "()V"
        }
    .end annotation

    .line 192
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    iput-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iput p3, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->val$status:I

    iput p4, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->val$state:I

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 4

    .line 193
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$700(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/bluetooth/BluetoothGatt;

    move-result-object v1

    if-eq v0, v1, :cond_0

    return-void

    .line 194
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "connection status="

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->val$status:I

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v1

    const-string v2, " state="

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->val$state:I

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$600(Lcom/navdy/hud/app/ambient/AmbientGattSession;Ljava/lang/String;)V

    .line 195
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->val$status:I

    if-eqz v0, :cond_1

    .line 196
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->val$status:I

    const-string v3, "connection"

    invoke-static {v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$200(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;ILjava/lang/String;)V

    .line 197
    return-void

    .line 199
    :cond_1
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->val$state:I

    const/4 v1, 0x2

    if-ne v0, v1, :cond_2

    .line 200
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$800(Lcom/navdy/hud/app/ambient/AmbientGattSession;)V

    .line 201
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientGattSession$3$1;

    invoke-direct {v1, p0}, Lcom/navdy/hud/app/ambient/AmbientGattSession$3$1;-><init>(Lcom/navdy/hud/app/ambient/AmbientGattSession$3;)V

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$902(Lcom/navdy/hud/app/ambient/AmbientGattSession;Ljava/lang/Runnable;)Ljava/lang/Runnable;

    .line 204
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$400(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/os/Handler;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$900(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Ljava/lang/Runnable;

    move-result-object v1

    const-wide/16 v2, 0x2710

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    goto :goto_0

    .line 205
    :cond_2
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->val$state:I

    if-nez v0, :cond_3

    .line 206
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$800(Lcom/navdy/hud/app/ambient/AmbientGattSession;)V

    .line 208
    :cond_3
    :goto_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$1000(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/bluetooth/BluetoothGattCallback;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->val$status:I

    iget v3, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;->val$state:I

    invoke-virtual {v0, v1, v2, v3}, Landroid/bluetooth/BluetoothGattCallback;->onConnectionStateChange(Landroid/bluetooth/BluetoothGatt;II)V

    .line 209
    return-void
.end method
