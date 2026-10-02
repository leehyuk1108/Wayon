.class Lcom/navdy/hud/app/ambient/AmbientGattSession$6;
.super Ljava/lang/Object;
.source "AmbientGattSession.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/navdy/hud/app/ambient/AmbientGattSession;->onCharacteristicWrite(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

.field final synthetic val$characteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

.field final synthetic val$gatt:Landroid/bluetooth/BluetoothGatt;

.field final synthetic val$status:I


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V
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

    .line 240
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    iput-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iput-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->val$characteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    iput p4, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->val$status:I

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 4

    .line 241
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$700(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/bluetooth/BluetoothGatt;

    move-result-object v1

    if-eq v0, v1, :cond_0

    return-void

    .line 242
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$1200(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    move-result-object v0

    if-eqz v0, :cond_1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$1200(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->val$characteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    iget v3, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->val$status:I

    invoke-virtual {v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->completed(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V

    .line 243
    :cond_1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$700(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/bluetooth/BluetoothGatt;

    move-result-object v1

    if-eq v0, v1, :cond_2

    return-void

    .line 244
    :cond_2
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->val$status:I

    if-eqz v0, :cond_3

    .line 245
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->val$status:I

    const-string v3, "write"

    invoke-static {v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$200(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;ILjava/lang/String;)V

    .line 246
    return-void

    .line 248
    :cond_3
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$1000(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/bluetooth/BluetoothGattCallback;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->val$characteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    iget v3, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;->val$status:I

    invoke-virtual {v0, v1, v2, v3}, Landroid/bluetooth/BluetoothGattCallback;->onCharacteristicWrite(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V

    .line 249
    return-void
.end method
