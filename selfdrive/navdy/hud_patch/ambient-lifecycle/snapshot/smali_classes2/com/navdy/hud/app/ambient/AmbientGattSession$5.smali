.class Lcom/navdy/hud/app/ambient/AmbientGattSession$5;
.super Ljava/lang/Object;
.source "AmbientGattSession.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/navdy/hud/app/ambient/AmbientGattSession;->onDescriptorWrite(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattDescriptor;I)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

.field final synthetic val$descriptor:Landroid/bluetooth/BluetoothGattDescriptor;

.field final synthetic val$gatt:Landroid/bluetooth/BluetoothGatt;

.field final synthetic val$status:I


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattDescriptor;I)V
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

    .line 226
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    iput-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iput-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->val$descriptor:Landroid/bluetooth/BluetoothGattDescriptor;

    iput p4, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->val$status:I

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 4

    .line 227
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$700(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/bluetooth/BluetoothGatt;

    move-result-object v1

    if-ne v0, v1, :cond_2

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->val$descriptor:Landroid/bluetooth/BluetoothGattDescriptor;

    if-eqz v0, :cond_2

    invoke-static {}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$1100()Ljava/util/UUID;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->val$descriptor:Landroid/bluetooth/BluetoothGattDescriptor;

    invoke-virtual {v1}, Landroid/bluetooth/BluetoothGattDescriptor;->getUuid()Ljava/util/UUID;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/util/UUID;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_0

    goto :goto_0

    .line 228
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "notifications status="

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->val$status:I

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$600(Lcom/navdy/hud/app/ambient/AmbientGattSession;Ljava/lang/String;)V

    .line 229
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->val$status:I

    if-eqz v0, :cond_1

    .line 230
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->val$status:I

    const-string v3, "notifications"

    invoke-static {v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$200(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;ILjava/lang/String;)V

    .line 231
    return-void

    .line 233
    :cond_1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$800(Lcom/navdy/hud/app/ambient/AmbientGattSession;)V

    .line 234
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$1000(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/bluetooth/BluetoothGattCallback;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->val$descriptor:Landroid/bluetooth/BluetoothGattDescriptor;

    iget v3, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;->val$status:I

    invoke-virtual {v0, v1, v2, v3}, Landroid/bluetooth/BluetoothGattCallback;->onDescriptorWrite(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattDescriptor;I)V

    .line 235
    return-void

    .line 227
    :cond_2
    :goto_0
    return-void
.end method
