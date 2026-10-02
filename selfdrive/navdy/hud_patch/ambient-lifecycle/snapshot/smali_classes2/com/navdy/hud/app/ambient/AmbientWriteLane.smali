.class public final Lcom/navdy/hud/app/ambient/AmbientWriteLane;
.super Ljava/lang/Object;
.source "AmbientWriteLane.java"


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        Lcom/navdy/hud/app/ambient/AmbientWriteLane$Failure;,
        Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;
    }
.end annotation


# instance fields
.field private active:Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;

.field private closed:Z

.field private final deadline:Ljava/lang/Runnable;

.field private final failure:Lcom/navdy/hud/app/ambient/AmbientWriteLane$Failure;

.field private final handler:Landroid/os/Handler;

.field private final pump:Ljava/lang/Runnable;

.field private final queue:Ljava/util/ArrayDeque;
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "Ljava/util/ArrayDeque<",
            "Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;",
            ">;"
        }
    .end annotation
.end field

.field private rejected:I


# direct methods
.method public constructor <init>(Landroid/os/Handler;Lcom/navdy/hud/app/ambient/AmbientWriteLane$Failure;)V
    .locals 1

    .line 41
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 17
    new-instance v0, Ljava/util/ArrayDeque;

    invoke-direct {v0}, Ljava/util/ArrayDeque;-><init>()V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->queue:Ljava/util/ArrayDeque;

    .line 21
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$1;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientWriteLane$1;-><init>(Lcom/navdy/hud/app/ambient/AmbientWriteLane;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->pump:Ljava/lang/Runnable;

    .line 22
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$2;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientWriteLane$2;-><init>(Lcom/navdy/hud/app/ambient/AmbientWriteLane;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->deadline:Ljava/lang/Runnable;

    .line 42
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->handler:Landroid/os/Handler;

    iput-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->failure:Lcom/navdy/hud/app/ambient/AmbientWriteLane$Failure;

    .line 43
    return-void
.end method

.method static synthetic access$000(Lcom/navdy/hud/app/ambient/AmbientWriteLane;)V
    .locals 0

    .line 10
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->drain()V

    return-void
.end method

.method static synthetic access$100(Lcom/navdy/hud/app/ambient/AmbientWriteLane;Ljava/lang/String;)V
    .locals 0

    .line 10
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->stop(Ljava/lang/String;)V

    return-void
.end method

.method private drain()V
    .locals 4

    .line 80
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->closed:Z

    if-nez v0, :cond_3

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->active:Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;

    if-nez v0, :cond_3

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->queue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->isEmpty()Z

    move-result v0

    if-eqz v0, :cond_0

    goto :goto_0

    .line 81
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->queue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->peekFirst()Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;

    .line 82
    iget-object v1, v0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->characteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    iget v2, v0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->type:I

    invoke-virtual {v1, v2}, Landroid/bluetooth/BluetoothGattCharacteristic;->setWriteType(I)V

    .line 83
    iget-object v1, v0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->characteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    iget-object v2, v0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->value:[B

    invoke-virtual {v2}, [B->clone()Ljava/lang/Object;

    move-result-object v2

    check-cast v2, [B

    invoke-virtual {v1, v2}, Landroid/bluetooth/BluetoothGattCharacteristic;->setValue([B)Z

    .line 85
    :try_start_0
    iget-object v1, v0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->gatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v0, v0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->characteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v1, v0}, Landroid/bluetooth/BluetoothGatt;->writeCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result v0
    :try_end_0
    .catch Ljava/lang/RuntimeException; {:try_start_0 .. :try_end_0} :catch_0

    .line 86
    nop

    .line 87
    if-nez v0, :cond_2

    .line 89
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->rejected:I

    add-int/lit8 v0, v0, 0x1

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->rejected:I

    const/16 v1, 0xa

    if-lt v0, v1, :cond_1

    const-string v0, "ATT busy retry exhausted"

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->stop(Ljava/lang/String;)V

    return-void

    .line 90
    :cond_1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->handler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->pump:Ljava/lang/Runnable;

    const-wide/16 v2, 0x1e

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 91
    return-void

    .line 93
    :cond_2
    const/4 v0, 0x0

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->rejected:I

    .line 94
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->queue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->removeFirst()Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->active:Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;

    .line 95
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->failure:Lcom/navdy/hud/app/ambient/AmbientWriteLane$Failure;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->active:Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;

    iget-object v1, v1, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->value:[B

    invoke-virtual {v1}, [B->clone()Ljava/lang/Object;

    move-result-object v1

    check-cast v1, [B

    invoke-interface {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Failure;->submitted([B)V

    .line 96
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->handler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->deadline:Ljava/lang/Runnable;

    const-wide/16 v2, 0x3e8

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 97
    return-void

    .line 86
    :catch_0
    move-exception v0

    const-string v0, "ATT write exception"

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->stop(Ljava/lang/String;)V

    return-void

    .line 80
    :cond_3
    :goto_0
    return-void
.end method

.method public static isOff([B)Z
    .locals 2

    .line 50
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->isState([B)Z

    move-result v0

    if-eqz v0, :cond_0

    array-length v0, p0

    const/16 v1, 0x8

    if-ne v0, v1, :cond_0

    const/4 v0, 0x2

    aget-byte v0, p0, v0

    const/4 v1, 0x4

    if-ne v0, v1, :cond_0

    const/4 v0, 0x3

    aget-byte v0, p0, v0

    if-nez v0, :cond_0

    aget-byte v0, p0, v1

    if-nez v0, :cond_0

    const/4 v0, 0x5

    aget-byte v0, p0, v0

    if-nez v0, :cond_0

    const/4 v0, 0x6

    aget-byte p0, p0, v0

    if-nez p0, :cond_0

    const/4 p0, 0x1

    goto :goto_0

    :cond_0
    const/4 p0, 0x0

    :goto_0
    return p0
.end method

.method public static isState([B)Z
    .locals 3

    .line 46
    const/4 v0, 0x0

    if-eqz p0, :cond_0

    array-length v1, p0

    const/16 v2, 0x8

    if-lt v1, v2, :cond_0

    aget-byte v1, p0, v0

    const/16 v2, 0x2e

    if-ne v1, v2, :cond_0

    const/4 v1, 0x1

    aget-byte p0, p0, v1

    const/16 v2, -0x73

    if-ne p0, v2, :cond_0

    const/4 v0, 0x1

    :cond_0
    return v0
.end method

.method private stop(Ljava/lang/String;)V
    .locals 1

    .line 109
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->closed:Z

    if-eqz v0, :cond_0

    return-void

    .line 110
    :cond_0
    invoke-virtual {p0}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->close()V

    .line 111
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->failure:Lcom/navdy/hud/app/ambient/AmbientWriteLane$Failure;

    invoke-interface {v0, p1}, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Failure;->failed(Ljava/lang/String;)V

    .line 112
    return-void
.end method


# virtual methods
.method public close()V
    .locals 2

    .line 115
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->closed:Z

    .line 116
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->handler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->pump:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 117
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->handler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->deadline:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 118
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->queue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->clear()V

    .line 119
    const/4 v0, 0x0

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->active:Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;

    .line 120
    return-void
.end method

.method public completed(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V
    .locals 1

    .line 100
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->closed:Z

    if-nez v0, :cond_2

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->active:Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;

    if-eqz v0, :cond_2

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->active:Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;

    iget-object v0, v0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->gatt:Landroid/bluetooth/BluetoothGatt;

    if-ne v0, p1, :cond_2

    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->active:Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;

    iget-object p1, p1, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->characteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    if-eq p1, p2, :cond_0

    goto :goto_0

    .line 101
    :cond_0
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->handler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->deadline:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 102
    if-eqz p3, :cond_1

    new-instance p1, Ljava/lang/StringBuilder;

    invoke-direct {p1}, Ljava/lang/StringBuilder;-><init>()V

    const-string p2, "ATT status="

    invoke-virtual {p1, p2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, p3}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->stop(Ljava/lang/String;)V

    return-void

    .line 103
    :cond_1
    const/4 p1, 0x0

    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->active:Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;

    .line 104
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->handler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->pump:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 105
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->handler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->pump:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 106
    return-void

    .line 100
    :cond_2
    :goto_0
    return-void
.end method

.method public discardQueuedState()V
    .locals 2

    .line 55
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->queue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->iterator()Ljava/util/Iterator;

    move-result-object v0

    :cond_0
    :goto_0
    invoke-interface {v0}, Ljava/util/Iterator;->hasNext()Z

    move-result v1

    if-eqz v1, :cond_1

    .line 56
    invoke-interface {v0}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v1

    check-cast v1, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;

    iget-object v1, v1, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->value:[B

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->isState([B)Z

    move-result v1

    if-eqz v1, :cond_0

    invoke-interface {v0}, Ljava/util/Iterator;->remove()V

    goto :goto_0

    .line 58
    :cond_1
    return-void
.end method

.method public offer(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z
    .locals 3

    .line 61
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->closed:Z

    const/4 v1, 0x0

    if-nez v0, :cond_7

    if-eqz p1, :cond_7

    if-eqz p2, :cond_7

    invoke-virtual {p2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getValue()[B

    move-result-object v0

    if-nez v0, :cond_0

    goto :goto_2

    .line 62
    :cond_0
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;

    invoke-direct {v0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;-><init>(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V

    .line 63
    iget-object p1, v0, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->value:[B

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->isOff([B)Z

    move-result p1

    if-eqz p1, :cond_1

    invoke-virtual {p0}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->discardQueuedState()V

    .line 65
    :cond_1
    invoke-virtual {v0}, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->stateKey()I

    move-result p1

    if-ltz p1, :cond_3

    .line 66
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->queue:Ljava/util/ArrayDeque;

    invoke-virtual {p1}, Ljava/util/ArrayDeque;->iterator()Ljava/util/Iterator;

    move-result-object p1

    :cond_2
    :goto_0
    invoke-interface {p1}, Ljava/util/Iterator;->hasNext()Z

    move-result p2

    if-eqz p2, :cond_3

    .line 67
    invoke-interface {p1}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object p2

    check-cast p2, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;

    invoke-virtual {p2}, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->stateKey()I

    move-result p2

    invoke-virtual {v0}, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->stateKey()I

    move-result v2

    if-ne p2, v2, :cond_2

    invoke-interface {p1}, Ljava/util/Iterator;->remove()V

    goto :goto_0

    .line 70
    :cond_3
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->queue:Ljava/util/ArrayDeque;

    invoke-virtual {p1}, Ljava/util/ArrayDeque;->size()I

    move-result p1

    const/16 p2, 0x8

    if-lt p1, p2, :cond_4

    const-string p1, "ATT queue overflow"

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->stop(Ljava/lang/String;)V

    return v1

    .line 71
    :cond_4
    invoke-virtual {v0}, Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;->ack()Z

    move-result p1

    if-eqz p1, :cond_5

    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->queue:Ljava/util/ArrayDeque;

    invoke-virtual {p1, v0}, Ljava/util/ArrayDeque;->addFirst(Ljava/lang/Object;)V

    goto :goto_1

    :cond_5
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->queue:Ljava/util/ArrayDeque;

    invoke-virtual {p1, v0}, Ljava/util/ArrayDeque;->addLast(Ljava/lang/Object;)V

    .line 72
    :goto_1
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->active:Lcom/navdy/hud/app/ambient/AmbientWriteLane$Item;

    if-nez p1, :cond_6

    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->rejected:I

    if-nez p1, :cond_6

    .line 73
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->handler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->pump:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 74
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->handler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->pump:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 76
    :cond_6
    const/4 p1, 0x1

    return p1

    .line 61
    :cond_7
    :goto_2
    return v1
.end method
