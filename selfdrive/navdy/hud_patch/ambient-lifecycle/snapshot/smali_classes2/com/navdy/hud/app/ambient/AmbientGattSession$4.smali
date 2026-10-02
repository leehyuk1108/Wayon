.class Lcom/navdy/hud/app/ambient/AmbientGattSession$4;
.super Ljava/lang/Object;
.source "AmbientGattSession.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/navdy/hud/app/ambient/AmbientGattSession;->onServicesDiscovered(Landroid/bluetooth/BluetoothGatt;I)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

.field final synthetic val$gatt:Landroid/bluetooth/BluetoothGatt;

.field final synthetic val$status:I


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;I)V
    .locals 0
    .annotation system Ldalvik/annotation/MethodParameters;
        accessFlags = {
            0x8010,
            0x1010,
            0x1010
        }
        names = {
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

    .line 213
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$4;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    iput-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$4;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iput p3, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$4;->val$status:I

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 4

    .line 214
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$4;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$4;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$700(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/bluetooth/BluetoothGatt;

    move-result-object v1

    if-eq v0, v1, :cond_0

    return-void

    .line 215
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$4;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "services status="

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$4;->val$status:I

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$600(Lcom/navdy/hud/app/ambient/AmbientGattSession;Ljava/lang/String;)V

    .line 216
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$4;->val$status:I

    if-eqz v0, :cond_1

    .line 217
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$4;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$4;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$4;->val$status:I

    const-string v3, "services"

    invoke-static {v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$200(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;ILjava/lang/String;)V

    .line 218
    return-void

    .line 220
    :cond_1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$4;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$1000(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/bluetooth/BluetoothGattCallback;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$4;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$4;->val$status:I

    invoke-virtual {v0, v1, v2}, Landroid/bluetooth/BluetoothGattCallback;->onServicesDiscovered(Landroid/bluetooth/BluetoothGatt;I)V

    .line 221
    return-void
.end method
