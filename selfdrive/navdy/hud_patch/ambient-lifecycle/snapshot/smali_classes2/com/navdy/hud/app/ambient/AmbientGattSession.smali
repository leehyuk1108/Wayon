.class public final Lcom/navdy/hud/app/ambient/AmbientGattSession;
.super Landroid/bluetooth/BluetoothGattCallback;
.source "AmbientGattSession.java"


# static fields
.field private static final CCCD:Ljava/util/UUID;

.field private static final TAG:Ljava/lang/String; = "NavdyAmbient"


# instance fields
.field private attemptsWithoutResponse:I

.field private current:Landroid/bluetooth/BluetoothGatt;

.field private final delegate:Landroid/bluetooth/BluetoothGattCallback;

.field private deliveryPending:Z

.field private final handler:Landroid/os/Handler;

.field private final journal:Ljava/io/File;

.field private lastCommand:[B

.field private lastOffReason:Ljava/lang/String;

.field private lastOffRecordMs:J

.field private final offResponseTimeout:Ljava/lang/Runnable;

.field private reconnectNotBefore:J

.field private setupTimeout:Ljava/lang/Runnable;

.field private writes:Lcom/navdy/hud/app/ambient/AmbientWriteLane;


# direct methods
.method static constructor <clinit>()V
    .locals 1

    .line 21
    const-string v0, "00002902-0000-1000-8000-00805f9b34fb"

    invoke-static {v0}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;

    move-result-object v0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->CCCD:Ljava/util/UUID;

    return-void
.end method

.method public constructor <init>(Landroid/bluetooth/BluetoothGattCallback;Landroid/os/Handler;Landroid/content/Context;)V
    .locals 1

    .line 39
    invoke-direct {p0}, Landroid/bluetooth/BluetoothGattCallback;-><init>()V

    .line 30
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->deliveryPending:Z

    .line 35
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientGattSession$1;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientGattSession$1;-><init>(Lcom/navdy/hud/app/ambient/AmbientGattSession;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->offResponseTimeout:Ljava/lang/Runnable;

    .line 40
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->delegate:Landroid/bluetooth/BluetoothGattCallback;

    .line 41
    iput-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->handler:Landroid/os/Handler;

    .line 42
    new-instance p1, Ljava/io/File;

    invoke-virtual {p3}, Landroid/content/Context;->getFilesDir()Ljava/io/File;

    move-result-object p2

    const-string p3, "ambient-ble-events.log"

    invoke-direct {p1, p2, p3}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->journal:Ljava/io/File;

    .line 43
    return-void
.end method

.method static synthetic access$000(Lcom/navdy/hud/app/ambient/AmbientGattSession;)[B
    .locals 0

    .line 19
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->lastCommand:[B

    return-object p0
.end method

.method static synthetic access$002(Lcom/navdy/hud/app/ambient/AmbientGattSession;[B)[B
    .locals 0

    .line 19
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->lastCommand:[B

    return-object p1
.end method

.method static synthetic access$100([B)Z
    .locals 0

    .line 19
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->isOff([B)Z

    move-result p0

    return p0
.end method

.method static synthetic access$1000(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/bluetooth/BluetoothGattCallback;
    .locals 0

    .line 19
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->delegate:Landroid/bluetooth/BluetoothGattCallback;

    return-object p0
.end method

.method static synthetic access$1100()Ljava/util/UUID;
    .locals 1

    .line 19
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->CCCD:Ljava/util/UUID;

    return-object v0
.end method

.method static synthetic access$1200(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Lcom/navdy/hud/app/ambient/AmbientWriteLane;
    .locals 0

    .line 19
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->writes:Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    return-object p0
.end method

.method static synthetic access$1302(Lcom/navdy/hud/app/ambient/AmbientGattSession;I)I
    .locals 0

    .line 19
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->attemptsWithoutResponse:I

    return p1
.end method

.method static synthetic access$200(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;ILjava/lang/String;)V
    .locals 0

    .line 19
    invoke-direct {p0, p1, p2, p3}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->fail(Landroid/bluetooth/BluetoothGatt;ILjava/lang/String;)V

    return-void
.end method

.method static synthetic access$300(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Ljava/lang/Runnable;
    .locals 0

    .line 19
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->offResponseTimeout:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$400(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/os/Handler;
    .locals 0

    .line 19
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->handler:Landroid/os/Handler;

    return-object p0
.end method

.method static synthetic access$502(Lcom/navdy/hud/app/ambient/AmbientGattSession;Z)Z
    .locals 0

    .line 19
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->deliveryPending:Z

    return p1
.end method

.method static synthetic access$600(Lcom/navdy/hud/app/ambient/AmbientGattSession;Ljava/lang/String;)V
    .locals 0

    .line 19
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->record(Ljava/lang/String;)V

    return-void
.end method

.method static synthetic access$700(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Landroid/bluetooth/BluetoothGatt;
    .locals 0

    .line 19
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->current:Landroid/bluetooth/BluetoothGatt;

    return-object p0
.end method

.method static synthetic access$800(Lcom/navdy/hud/app/ambient/AmbientGattSession;)V
    .locals 0

    .line 19
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->cancelTimeout()V

    return-void
.end method

.method static synthetic access$900(Lcom/navdy/hud/app/ambient/AmbientGattSession;)Ljava/lang/Runnable;
    .locals 0

    .line 19
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->setupTimeout:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$902(Lcom/navdy/hud/app/ambient/AmbientGattSession;Ljava/lang/Runnable;)Ljava/lang/Runnable;
    .locals 0

    .line 19
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->setupTimeout:Ljava/lang/Runnable;

    return-object p1
.end method

.method private cancelTimeout()V
    .locals 2

    .line 160
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->setupTimeout:Ljava/lang/Runnable;

    if-eqz v0, :cond_0

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->handler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->setupTimeout:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 161
    :cond_0
    const/4 v0, 0x0

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->setupTimeout:Ljava/lang/Runnable;

    .line 162
    return-void
.end method

.method private fail(Landroid/bluetooth/BluetoothGatt;ILjava/lang/String;)V
    .locals 1

    .line 182
    if-eqz p1, :cond_1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->current:Landroid/bluetooth/BluetoothGatt;

    if-eq p1, v0, :cond_0

    goto :goto_0

    .line 183
    :cond_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->cancelTimeout()V

    .line 184
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->deliveryPending:Z

    .line 185
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v0, p3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p3

    const-string v0, " failed status="

    invoke-virtual {p3, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p3

    invoke-virtual {p3, p2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object p3

    invoke-virtual {p3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p3

    invoke-direct {p0, p3}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->record(Ljava/lang/String;)V

    .line 187
    iget-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->delegate:Landroid/bluetooth/BluetoothGattCallback;

    const/4 v0, 0x0

    invoke-virtual {p3, p1, p2, v0}, Landroid/bluetooth/BluetoothGattCallback;->onConnectionStateChange(Landroid/bluetooth/BluetoothGatt;II)V

    .line 188
    return-void

    .line 182
    :cond_1
    :goto_0
    return-void
.end method

.method private static isOff([B)Z
    .locals 3

    .line 128
    if-eqz p0, :cond_0

    array-length v0, p0

    const/16 v1, 0x8

    if-ne v0, v1, :cond_0

    const/4 v0, 0x1

    aget-byte v1, p0, v0

    const/16 v2, -0x73

    if-ne v1, v2, :cond_0

    const/4 v1, 0x3

    aget-byte v1, p0, v1

    if-nez v1, :cond_0

    const/4 v1, 0x4

    aget-byte v1, p0, v1

    if-nez v1, :cond_0

    const/4 v1, 0x5

    aget-byte v1, p0, v1

    if-nez v1, :cond_0

    const/4 v1, 0x6

    aget-byte p0, p0, v1

    if-nez p0, :cond_0

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    :goto_0
    return v0
.end method

.method static normalizedResponse([B)[B
    .locals 7

    .line 133
    const/4 v0, 0x0

    if-eqz p0, :cond_7

    array-length v1, p0

    if-nez v1, :cond_0

    goto :goto_2

    .line 134
    :cond_0
    array-length v1, p0

    const/4 v2, -0x1

    const/4 v3, 0x0

    const/4 v4, 0x1

    if-ne v1, v4, :cond_1

    aget-byte v1, p0, v3

    if-ne v1, v2, :cond_1

    return-object p0

    .line 135
    :cond_1
    array-length v1, p0

    if-le v1, v4, :cond_2

    aget-byte v1, p0, v3

    if-ne v1, v2, :cond_2

    array-length v1, p0

    invoke-static {p0, v4, v1}, Ljava/util/Arrays;->copyOfRange([BII)[B

    move-result-object p0

    .line 136
    :cond_2
    array-length v1, p0

    const/4 v2, 0x4

    if-lt v1, v2, :cond_6

    aget-byte v1, p0, v3

    const/16 v5, 0x2e

    if-ne v1, v5, :cond_6

    array-length v1, p0

    const/4 v5, 0x2

    aget-byte v5, p0, v5

    const/16 v6, 0xff

    and-int/2addr v5, v6

    add-int/2addr v5, v2

    if-eq v1, v5, :cond_3

    goto :goto_1

    .line 137
    :cond_3
    nop

    .line 138
    nop

    :goto_0
    array-length v1, p0

    if-ge v4, v1, :cond_4

    aget-byte v1, p0, v4

    and-int/2addr v1, v6

    add-int/2addr v3, v1

    add-int/lit8 v4, v4, 0x1

    goto :goto_0

    .line 139
    :cond_4
    and-int/lit16 v1, v3, 0xff

    if-ne v1, v6, :cond_5

    move-object v0, p0

    :cond_5
    return-object v0

    .line 136
    :cond_6
    :goto_1
    return-object v0

    .line 133
    :cond_7
    :goto_2
    return-object v0
.end method

.method private record(Ljava/lang/String;)V
    .locals 6

    .line 165
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "session "

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    const-string v1, "NavdyAmbient"

    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 167
    :try_start_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->journal:Ljava/io/File;

    invoke-virtual {v0}, Ljava/io/File;->length()J

    move-result-wide v2

    const-wide/32 v4, 0x100000

    cmp-long v0, v2, v4

    if-lez v0, :cond_1

    .line 168
    new-instance v0, Ljava/io/File;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->journal:Ljava/io/File;

    invoke-virtual {v2}, Ljava/io/File;->getParentFile()Ljava/io/File;

    move-result-object v2

    const-string v3, "ambient-ble-events.previous.log"

    invoke-direct {v0, v2, v3}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    .line 169
    invoke-virtual {v0}, Ljava/io/File;->exists()Z

    move-result v2

    if-eqz v2, :cond_0

    invoke-virtual {v0}, Ljava/io/File;->delete()Z

    move-result v2

    if-eqz v2, :cond_1

    :cond_0
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->journal:Ljava/io/File;

    invoke-virtual {v2, v0}, Ljava/io/File;->renameTo(Ljava/io/File;)Z

    move-result v0

    if-nez v0, :cond_1

    .line 170
    const-string v0, "cannot rotate ambient BLE journal"

    invoke-static {v1, v0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 173
    :cond_1
    new-instance v0, Ljava/io/FileWriter;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->journal:Ljava/io/File;

    const/4 v3, 0x1

    invoke-direct {v0, v2, v3}, Ljava/io/FileWriter;-><init>(Ljava/io/File;Z)V
    :try_end_0
    .catch Ljava/io/IOException; {:try_start_0 .. :try_end_0} :catch_0

    .line 174
    :try_start_1
    new-instance v2, Ljava/lang/StringBuilder;

    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V

    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v3

    invoke-virtual {v2, v3, v4}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    move-result-object v2

    const-string v3, " "

    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    invoke-virtual {v2, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    const-string v2, "\n"

    invoke-virtual {p1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-virtual {v0, p1}, Ljava/io/FileWriter;->write(Ljava/lang/String;)V
    :try_end_1
    .catchall {:try_start_1 .. :try_end_1} :catchall_0

    .line 175
    :try_start_2
    invoke-virtual {v0}, Ljava/io/FileWriter;->close()V
    :try_end_2
    .catch Ljava/io/IOException; {:try_start_2 .. :try_end_2} :catch_0

    .line 178
    goto :goto_1

    .line 173
    :catchall_0
    move-exception p1

    :try_start_3
    invoke-virtual {v0}, Ljava/io/FileWriter;->close()V
    :try_end_3
    .catchall {:try_start_3 .. :try_end_3} :catchall_1

    goto :goto_0

    :catchall_1
    move-exception v0

    :try_start_4
    invoke-virtual {p1, v0}, Ljava/lang/Throwable;->addSuppressed(Ljava/lang/Throwable;)V

    :goto_0
    throw p1
    :try_end_4
    .catch Ljava/io/IOException; {:try_start_4 .. :try_end_4} :catch_0

    .line 176
    :catch_0
    move-exception p1

    .line 177
    const-string v0, "cannot write ambient BLE journal"

    invoke-static {v1, v0, p1}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 179
    :goto_1
    return-void
.end method


# virtual methods
.method public attach(Landroid/bluetooth/BluetoothGatt;)V
    .locals 3

    .line 67
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->cancelTimeout()V

    .line 68
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->handler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->offResponseTimeout:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 69
    const/4 v0, 0x0

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->lastCommand:[B

    .line 70
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->writes:Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    if-eqz v0, :cond_0

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->writes:Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    invoke-virtual {v0}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->close()V

    .line 71
    :cond_0
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->current:Landroid/bluetooth/BluetoothGatt;

    .line 72
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->attemptsWithoutResponse:I

    add-int/lit8 v0, v0, 0x1

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->attemptsWithoutResponse:I

    .line 73
    nop

    .line 74
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->handler:Landroid/os/Handler;

    new-instance v2, Lcom/navdy/hud/app/ambient/AmbientGattSession$2;

    invoke-direct {v2, p0, p1}, Lcom/navdy/hud/app/ambient/AmbientGattSession$2;-><init>(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;)V

    invoke-direct {v0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;-><init>(Landroid/os/Handler;Lcom/navdy/hud/app/ambient/AmbientWriteLane$Failure;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->writes:Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    .line 89
    if-nez p1, :cond_1

    const-string p1, "connect returned null"

    goto :goto_0

    :cond_1
    const-string p1, "connect attempt"

    :goto_0
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->record(Ljava/lang/String;)V

    .line 90
    return-void
.end method

.method public canConnect()Z
    .locals 5

    .line 156
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    iget-wide v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->reconnectNotBefore:J

    cmp-long v4, v0, v2

    if-ltz v4, :cond_0

    const/4 v0, 0x1

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    :goto_0
    return v0
.end method

.method public connect(Landroid/bluetooth/BluetoothDevice;Landroid/content/Context;)Landroid/bluetooth/BluetoothGatt;
    .locals 11

    .line 52
    const-string v0, "connect exception="

    const/4 v1, 0x0

    const/4 v2, 0x0

    :try_start_0
    const-class v3, Landroid/bluetooth/BluetoothDevice;

    const-string v4, "connectGatt"

    const/4 v5, 0x4

    new-array v6, v5, [Ljava/lang/Class;

    const-class v7, Landroid/content/Context;

    aput-object v7, v6, v2

    sget-object v7, Ljava/lang/Boolean;->TYPE:Ljava/lang/Class;

    const/4 v8, 0x1

    aput-object v7, v6, v8

    const-class v7, Landroid/bluetooth/BluetoothGattCallback;

    const/4 v9, 0x2

    aput-object v7, v6, v9

    sget-object v7, Ljava/lang/Integer;->TYPE:Ljava/lang/Class;

    const/4 v10, 0x3

    aput-object v7, v6, v10

    invoke-virtual {v3, v4, v6}, Ljava/lang/Class;->getMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    move-result-object v3

    .line 54
    new-instance v4, Ljava/lang/StringBuilder;

    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    const-string v6, "connect transport=LE freshScan="

    invoke-virtual {v4, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    invoke-virtual {p0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->requiresFreshScan()Z

    move-result v6

    invoke-virtual {v4, v6}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v4

    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v4

    invoke-direct {p0, v4}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->record(Ljava/lang/String;)V

    .line 55
    invoke-static {v2}, Ljava/lang/Boolean;->valueOf(Z)Ljava/lang/Boolean;

    move-result-object v4

    invoke-static {v9}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;

    move-result-object v6

    new-array v5, v5, [Ljava/lang/Object;

    aput-object p2, v5, v2

    aput-object v4, v5, v8

    aput-object p0, v5, v9

    aput-object v6, v5, v10

    invoke-virtual {v3, p1, v5}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v3

    check-cast v3, Landroid/bluetooth/BluetoothGatt;
    :try_end_0
    .catch Ljava/lang/NoSuchMethodException; {:try_start_0 .. :try_end_0} :catch_1
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    return-object v3

    .line 60
    :catch_0
    move-exception p1

    .line 61
    new-instance p2, Ljava/lang/StringBuilder;

    invoke-direct {p2}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {p2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p2

    invoke-virtual {p1}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/Class;->getSimpleName()Ljava/lang/String;

    move-result-object p1

    invoke-virtual {p2, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->record(Ljava/lang/String;)V

    .line 62
    return-object v1

    .line 56
    :catch_1
    move-exception v3

    .line 57
    const-string v3, "connect transport=AUTO compatibility fallback"

    invoke-direct {p0, v3}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->record(Ljava/lang/String;)V

    .line 58
    :try_start_1
    invoke-virtual {p1, p2, v2, p0}, Landroid/bluetooth/BluetoothDevice;->connectGatt(Landroid/content/Context;ZLandroid/bluetooth/BluetoothGattCallback;)Landroid/bluetooth/BluetoothGatt;

    move-result-object p1
    :try_end_1
    .catch Ljava/lang/RuntimeException; {:try_start_1 .. :try_end_1} :catch_2

    return-object p1

    .line 59
    :catch_2
    move-exception p1

    new-instance p2, Ljava/lang/StringBuilder;

    invoke-direct {p2}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {p2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p2

    invoke-virtual {p1}, Ljava/lang/Object;->getClass()Ljava/lang/Class;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/Class;->getSimpleName()Ljava/lang/String;

    move-result-object p1

    invoke-virtual {p2, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->record(Ljava/lang/String;)V

    return-object v1
.end method

.method public deferReconnect(J)J
    .locals 6

    .line 143
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    .line 145
    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->attemptsWithoutResponse:I

    const/4 v3, 0x1

    if-le v2, v3, :cond_0

    .line 146
    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->attemptsWithoutResponse:I

    add-int/lit8 v2, v2, -0x2

    const/4 v3, 0x4

    invoke-static {v3, v2}, Ljava/lang/Math;->min(II)I

    move-result v2

    const-wide/16 v3, 0x1388

    shl-long v2, v3, v2

    const-wide/32 v4, 0xea60

    invoke-static {v4, v5, v2, v3}, Ljava/lang/Math;->min(JJ)J

    move-result-wide v2

    invoke-static {p1, p2, v2, v3}, Ljava/lang/Math;->max(JJ)J

    move-result-wide p1

    .line 148
    :cond_0
    iget-wide v2, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->reconnectNotBefore:J

    .line 149
    const-wide/16 v4, 0x0

    invoke-static {v4, v5, p1, p2}, Ljava/lang/Math;->max(JJ)J

    move-result-wide p1

    add-long/2addr p1, v0

    .line 148
    invoke-static {v2, v3, p1, p2}, Ljava/lang/Math;->max(JJ)J

    move-result-wide p1

    iput-wide p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->reconnectNotBefore:J

    .line 150
    iget-wide p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->reconnectNotBefore:J

    sub-long/2addr p1, v0

    .line 151
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "reconnect deferred ms="

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p1, p2}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->record(Ljava/lang/String;)V

    .line 152
    return-wide p1
.end method

.method public deliveryTimeout()V
    .locals 3

    .line 124
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->current:Landroid/bluetooth/BluetoothGatt;

    if-eqz v0, :cond_0

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->current:Landroid/bluetooth/BluetoothGatt;

    const/16 v1, 0x85

    const-string v2, "module response timeout"

    invoke-direct {p0, v0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->fail(Landroid/bluetooth/BluetoothGatt;ILjava/lang/String;)V

    .line 125
    :cond_0
    return-void
.end method

.method public detach()V
    .locals 2

    .line 93
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->cancelTimeout()V

    .line 94
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->handler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->offResponseTimeout:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 95
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->current:Landroid/bluetooth/BluetoothGatt;

    if-eqz v0, :cond_0

    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->deliveryPending:Z

    .line 96
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->writes:Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    if-eqz v0, :cond_1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->writes:Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    invoke-virtual {v0}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->close()V

    .line 97
    :cond_1
    const/4 v0, 0x0

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->writes:Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    .line 98
    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->lastCommand:[B

    .line 99
    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->current:Landroid/bluetooth/BluetoothGatt;

    .line 100
    return-void
.end method

.method public gearReceived(Ljava/lang/String;)V
    .locals 2

    .line 119
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "gear received="

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->record(Ljava/lang/String;)V

    return-void
.end method

.method public needsDelivery()Z
    .locals 1

    .line 121
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->deliveryPending:Z

    return v0
.end method

.method public offRequested(Ljava/lang/String;)V
    .locals 8

    .line 109
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->deliveryPending:Z

    .line 110
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->writes:Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    if-eqz v1, :cond_0

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->writes:Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    invoke-virtual {v1}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->discardQueuedState()V

    .line 111
    :cond_0
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v1

    .line 112
    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->lastOffReason:Ljava/lang/String;

    invoke-virtual {p1, v3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v3

    if-eqz v3, :cond_1

    iget-wide v3, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->lastOffRecordMs:J

    sub-long v3, v1, v3

    const-wide/32 v5, 0xea60

    cmp-long v7, v3, v5

    if-ltz v7, :cond_3

    .line 113
    :cond_1
    new-instance v3, Ljava/lang/StringBuilder;

    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V

    const-string v4, "off requested reason="

    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    invoke-virtual {v3, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    const-string v4, " sessionPresent="

    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->current:Landroid/bluetooth/BluetoothGatt;

    if-eqz v4, :cond_2

    goto :goto_0

    :cond_2
    const/4 v0, 0x0

    :goto_0
    invoke-virtual {v3, v0}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->record(Ljava/lang/String;)V

    .line 114
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->lastOffReason:Ljava/lang/String;

    .line 115
    iput-wide v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->lastOffRecordMs:J

    .line 117
    :cond_3
    return-void
.end method

.method public onCharacteristicChanged(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V
    .locals 3

    .line 254
    if-nez p2, :cond_0

    return-void

    .line 255
    :cond_0
    invoke-virtual {p2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getValue()[B

    move-result-object v0

    .line 256
    if-nez v0, :cond_1

    const/4 v0, 0x0

    goto :goto_0

    :cond_1
    invoke-virtual {v0}, [B->clone()Ljava/lang/Object;

    move-result-object v0

    check-cast v0, [B

    .line 257
    :goto_0
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->handler:Landroid/os/Handler;

    new-instance v2, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;

    invoke-direct {v2, p0, p1, v0, p2}, Lcom/navdy/hud/app/ambient/AmbientGattSession$7;-><init>(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;[BLandroid/bluetooth/BluetoothGattCharacteristic;)V

    invoke-virtual {v1, v2}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 281
    return-void
.end method

.method public onCharacteristicWrite(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V
    .locals 2

    .line 240
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->handler:Landroid/os/Handler;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;

    invoke-direct {v1, p0, p1, p2, p3}, Lcom/navdy/hud/app/ambient/AmbientGattSession$6;-><init>(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 250
    return-void
.end method

.method public onConnectionStateChange(Landroid/bluetooth/BluetoothGatt;II)V
    .locals 2

    .line 192
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->handler:Landroid/os/Handler;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;

    invoke-direct {v1, p0, p1, p2, p3}, Lcom/navdy/hud/app/ambient/AmbientGattSession$3;-><init>(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;II)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 210
    return-void
.end method

.method public onDescriptorWrite(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattDescriptor;I)V
    .locals 2

    .line 226
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->handler:Landroid/os/Handler;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;

    invoke-direct {v1, p0, p1, p2, p3}, Lcom/navdy/hud/app/ambient/AmbientGattSession$5;-><init>(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattDescriptor;I)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 236
    return-void
.end method

.method public onServicesDiscovered(Landroid/bluetooth/BluetoothGatt;I)V
    .locals 2

    .line 213
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->handler:Landroid/os/Handler;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientGattSession$4;

    invoke-direct {v1, p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientGattSession$4;-><init>(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;I)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 222
    return-void
.end method

.method public recordPowerEvent(Ljava/lang/String;)V
    .locals 0

    .line 47
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->record(Ljava/lang/String;)V

    return-void
.end method

.method public requiresFreshScan()Z
    .locals 2

    .line 45
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->attemptsWithoutResponse:I

    const/4 v1, 0x2

    if-lt v0, v1, :cond_0

    const/4 v0, 0x1

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    :goto_0
    return v0
.end method

.method public write(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z
    .locals 2

    .line 103
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->current:Landroid/bluetooth/BluetoothGatt;

    if-ne p1, v0, :cond_2

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->writes:Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    if-nez v0, :cond_0

    goto :goto_0

    .line 104
    :cond_0
    invoke-virtual {p2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getValue()[B

    move-result-object v0

    if-eqz v0, :cond_1

    invoke-virtual {p2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getValue()[B

    move-result-object v0

    array-length v0, v0

    const/4 v1, 0x1

    if-le v0, v1, :cond_1

    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->deliveryPending:Z

    .line 105
    :cond_1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession;->writes:Lcom/navdy/hud/app/ambient/AmbientWriteLane;

    invoke-virtual {v0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientWriteLane;->offer(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result p1

    return p1

    .line 103
    :cond_2
    :goto_0
    const/4 p1, 0x0

    return p1
.end method
