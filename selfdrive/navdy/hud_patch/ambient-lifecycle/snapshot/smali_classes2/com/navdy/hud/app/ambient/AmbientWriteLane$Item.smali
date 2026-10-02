.class final Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;
.super Ljava/lang/Object;
.source "AmbientWriteLane.java"


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Lcom/navdy/hud/app/ambient/AmbientWriteLane;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x1a
    name = "Item"
.end annotation


# instance fields
.field final characteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

.field final gatt:Landroid/bluetooth/BluetoothGatt;

.field final type:I

.field final value:[B


# direct methods
.method constructor <init>(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V
    .locals 0

    .line 31
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 32
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->gatt:Landroid/bluetooth/BluetoothGatt;

    iput-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->characteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {p2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getValue()[B

    move-result-object p1

    invoke-virtual {p1}, [B->clone()Ljava/lang/Object;

    move-result-object p1

    check-cast p1, [B

    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->value:[B

    invoke-virtual {p2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getWriteType()I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->type:I

    .line 33
    return-void
.end method


# virtual methods
.method ack()Z
    .locals 4

    .line 34
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->value:[B

    array-length v0, v0

    const/4 v1, 0x0

    const/4 v2, 0x1

    if-ne v0, v2, :cond_0

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->value:[B

    aget-byte v0, v0, v1

    const/4 v3, -0x1

    if-ne v0, v3, :cond_0

    const/4 v1, 0x1

    :cond_0
    return v1
.end method

.method stateKey()I
    .locals 2

    .line 36
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->value:[B

    array-length v0, v0

    const/16 v1, 0x8

    if-lt v0, v1, :cond_0

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->value:[B

    const/4 v1, 0x0

    aget-byte v0, v0, v1

    const/16 v1, 0x2e

    if-ne v0, v1, :cond_0

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->value:[B

    const/4 v1, 0x1

    aget-byte v0, v0, v1

    const/16 v1, -0x73

    if-ne v0, v1, :cond_0

    .line 37
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->value:[B

    const/4 v1, 0x3

    aget-byte v0, v0, v1

    and-int/lit16 v0, v0, 0xff

    goto :goto_0

    :cond_0
    const/4 v0, -0x1

    .line 36
    :goto_0
    return v0
.end method
