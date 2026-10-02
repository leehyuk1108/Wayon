.class Lcom/navdy/hud/app/ambient/AmbientGattSession$7;
.super Ljava/lang/Object;
.source "AmbientGattSession.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/navdy/hud/app/ambient/AmbientGattSession;->onCharacteristicChanged(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

.field final synthetic val$characteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

.field final synthetic val$gatt:Landroid/bluetooth/BluetoothGatt;

.field final synthetic val$value:[B


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;[BLandroid/bluetooth/BluetoothGattCharacteristic;)V
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

    .line 257
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    iput-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iput-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->val$value:[B

    iput-object p4, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->val$characteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 6

    .line 258
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$700(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/bluetooth/BluetoothGatt;

    move-result-object v1

    if-ne v0, v1, :cond_8

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->val$value:[B

    if-eqz v0, :cond_8

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->val$value:[B

    array-length v0, v0

    if-nez v0, :cond_0

    goto/16 :goto_1

    .line 259
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->val$value:[B

    const/4 v1, 0x0

    aget-byte v0, v0, v1

    and-int/lit16 v0, v0, 0xff

    .line 260
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->val$value:[B

    array-length v2, v2

    const/4 v3, 0x1

    if-ne v2, v3, :cond_2

    const/16 v2, 0xfc

    if-eq v0, v2, :cond_1

    const/16 v2, 0xf0

    if-eq v0, v2, :cond_1

    const/16 v2, 0xf3

    if-ne v0, v2, :cond_2

    .line 261
    :cond_1
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    new-instance v3, Ljava/lang/StringBuilder;

    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V

    const-string v4, "module NACK="

    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    invoke-virtual {v3, v0}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    const/16 v3, 0x85

    invoke-static {v1, v2, v3, v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$200(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;ILjava/lang/String;)V

    .line 262
    return-void

    .line 264
    :cond_2
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->val$value:[B

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->normalizedResponse([B)[B

    move-result-object v0

    .line 265
    if-nez v0, :cond_3

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "invalid module response len="

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->val$value:[B

    array-length v2, v2

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$600(Lcom/navdy/hud/app/ambient/AmbientGattSession;Ljava/lang/String;)V

    return-void

    .line 266
    :cond_3
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v2, v1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$1302(Lcom/navdy/hud/app/ambient/AmbientGattSession;I)I

    .line 268
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$000(Lcom/navdy/hud/app/ambient/AmbientGattSession;)[B

    move-result-object v2

    if-eqz v2, :cond_5

    array-length v2, v0

    if-eq v2, v3, :cond_4

    array-length v2, v0

    const/4 v4, 0x4

    if-le v2, v4, :cond_5

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    .line 269
    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$000(Lcom/navdy/hud/app/ambient/AmbientGattSession;)[B

    move-result-object v2

    array-length v2, v2

    if-le v2, v4, :cond_5

    const/4 v2, 0x3

    aget-byte v4, v0, v2

    iget-object v5, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    .line 270
    invoke-static {v5}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$000(Lcom/navdy/hud/app/ambient/AmbientGattSession;)[B

    move-result-object v5

    aget-byte v2, v5, v2

    if-eq v4, v2, :cond_4

    aget-byte v2, v0, v3

    const/16 v4, -0x44

    if-ne v2, v4, :cond_5

    :cond_4
    goto :goto_0

    :cond_5
    const/4 v3, 0x0

    .line 271
    :goto_0
    if-eqz v3, :cond_7

    .line 272
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$000(Lcom/navdy/hud/app/ambient/AmbientGattSession;)[B

    move-result-object v2

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$100([B)Z

    move-result v2

    if-eqz v2, :cond_6

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    const-string v3, "off protocol response received"

    invoke-static {v2, v3}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$600(Lcom/navdy/hud/app/ambient/AmbientGattSession;Ljava/lang/String;)V

    .line 273
    :cond_6
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v2}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$400(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/os/Handler;

    move-result-object v2

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v3}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$300(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Ljava/lang/Runnable;

    move-result-object v3

    invoke-virtual {v2, v3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 274
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v2, v1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$502(Lcom/navdy/hud/app/ambient/AmbientGattSession;Z)Z

    .line 275
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    const/4 v2, 0x0

    invoke-static {v1, v2}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$002(Lcom/navdy/hud/app/ambient/AmbientGattSession;[B)[B

    .line 278
    :cond_7
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->val$characteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v1, v0}, Landroid/bluetooth/BluetoothGattCharacteristic;->setValue([B)Z

    .line 279
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$1000(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/bluetooth/BluetoothGattCallback;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;->val$characteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v0, v1, v2}, Landroid/bluetooth/BluetoothGattCallback;->onCharacteristicChanged(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V

    .line 280
    return-void

    .line 258
    :cond_8
    :goto_1
    return-void
.end method
