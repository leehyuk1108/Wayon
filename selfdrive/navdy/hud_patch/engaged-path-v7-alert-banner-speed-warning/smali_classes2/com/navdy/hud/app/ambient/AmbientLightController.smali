.class public final Lcom/navdy/hud/app/ambient/AmbientLightController;
.super Ljava/lang/Object;
.source "AmbientLightController.java"


# static fields
.field private static final BRIGHTNESS_SYNC_INTERVAL_MS:J = 0x1388L

.field private static final BRIGHTNESS_UPDATE_DELTA:I = 0x2

.field private static final CLIENT_CONFIG_UUID:Ljava/util/UUID;

.field private static final CONNECT_RETRY_MS:J = 0x1388L

.field private static final FADE_PHASE_RED_DOWN:I = 0x2

.field private static final FADE_PHASE_RED_UP:I = 0x1

.field private static final FADE_PHASE_WHITE_DOWN:I = 0x0

.field private static final FADE_PHASE_WHITE_UP:I = 0x3

.field private static final FADE_STEPS:I = 0x5

.field private static final FADE_STEP_INTERVAL_MS:J = 0x1c2L

.field private static final LEGACY_SERVICE_UUID:Ljava/util/UUID;

.field private static final LOW_LIGHT_CHECK_INTERVAL_MS:J = 0x3e8L

.field private static final MAX_AMBIENT_BRIGHTNESS:I = 0x32

.field private static final MID_AMBIENT_BRIGHTNESS:I = 0x8

.field private static final MIN_AMBIENT_BRIGHTNESS:I = 0x1

.field private static final MIN_FADE_AMBIENT_BRIGHTNESS:I = 0x8

.field private static final NOTIFY_UUID:Ljava/util/UUID;

.field private static final OUTDOOR_AMBIENT_BRIGHTNESS:I = 0x32

.field private static final OVERSPEED_MIN_ACTIVE_MS:J = 0xbb8L

.field private static final OVERSPEED_OFF_DELAY_MS:J = 0x7d0L

.field private static final OVERSPEED_ON_DELAY_MS:J = 0x3e8L

.field private static final PACKET_ACK:[B

.field private static final PACKET_OFF:[B

.field private static final PACKET_RED:[B

.field private static final PACKET_RESTORE:[B

.field private static final PACKET_START:[B

.field private static final SCREEN_BRIGHTNESS_EIGHT_PERCENT:I = 0x29

.field private static final SCREEN_BRIGHTNESS_FIFTY_PERCENT:I = 0x64

.field private static final SCREEN_BRIGHTNESS_ONE_PERCENT:I = 0x10

.field private static final SERVICE_UUID:Ljava/util/UUID;

.field private static final TAG:Ljava/lang/String; = "NavdyAmbient"

.field private static final WRITE_UUID:Ljava/util/UUID;

.field private static final ZONE_2_AMBIENT_BRIGHTNESS:I = 0x28

.field private static sInstance:Lcom/navdy/hud/app/ambient/AmbientLightController;


# instance fields
.field private mAdapter:Landroid/bluetooth/BluetoothAdapter;

.field private mAmbientActive:Z

.field private final mBlinkRunnable:Ljava/lang/Runnable;

.field private final mBrightnessSyncRunnable:Ljava/lang/Runnable;

.field private mConnected:Z

.field private final mContext:Landroid/content/Context;

.field private mFadePhase:I

.field private mFadeStep:I

.field private final mFlushAfterAckRunnable:Ljava/lang/Runnable;

.field private mGatt:Landroid/bluetooth/BluetoothGatt;

.field private final mGattCallback:Landroid/bluetooth/BluetoothGattCallback;

.field private final mHandler:Landroid/os/Handler;

.field private mLastAmbientBrightness:I

.field private mLastGear:Ljava/lang/String;

.field private mLowLightWarning:Z

.field private mNotifyCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

.field private mNotifyReady:Z

.field private mOverspeedActivatedAtMs:J

.field private mOverspeedActive:Z

.field private final mOverspeedStateRunnable:Ljava/lang/Runnable;

.field private final mQueue:Ljava/util/ArrayDeque;
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "Ljava/util/ArrayDeque<",
            "[B>;"
        }
    .end annotation
.end field

.field private final mReconnectRunnable:Ljava/lang/Runnable;

.field private mReconnectScheduled:Z

.field private mRequestedOverspeed:Z

.field private mReverseActive:Z

.field private final mScanCallback:Landroid/bluetooth/BluetoothAdapter$LeScanCallback;

.field private mScanning:Z

.field private final mSeenScanDevices:Ljava/util/Set;
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "Ljava/util/Set<",
            "Ljava/lang/String;",
            ">;"
        }
    .end annotation
.end field

.field private mStartQueued:Z

.field private final mStopScanRunnable:Ljava/lang/Runnable;

.field private mWarningAnimationStarted:Z

.field private mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

.field private final mWritePaceRunnable:Ljava/lang/Runnable;

.field private final mWriteTimeoutRunnable:Ljava/lang/Runnable;

.field private mWriting:Z


# direct methods
.method static constructor <clinit>()V
    .locals 3

    .line 28
    const-string v0, "0000ae30-0000-1000-8000-00805f9b34fb"

    invoke-static {v0}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;

    move-result-object v0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->SERVICE_UUID:Ljava/util/UUID;

    .line 29
    const-string v0, "0000ae00-0000-1000-8000-00805f9b34fb"

    invoke-static {v0}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;

    move-result-object v0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->LEGACY_SERVICE_UUID:Ljava/util/UUID;

    .line 30
    const-string v0, "0000ae01-0000-1000-8000-00805f9b34fb"

    invoke-static {v0}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;

    move-result-object v0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->WRITE_UUID:Ljava/util/UUID;

    .line 31
    const-string v0, "0000ae02-0000-1000-8000-00805f9b34fb"

    invoke-static {v0}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;

    move-result-object v0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->NOTIFY_UUID:Ljava/util/UUID;

    .line 32
    const-string v0, "00002902-0000-1000-8000-00805f9b34fb"

    invoke-static {v0}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;

    move-result-object v0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->CLIENT_CONFIG_UUID:Ljava/util/UUID;

    .line 56
    const/4 v0, 0x5

    new-array v0, v0, [B

    fill-array-data v0, :array_0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_START:[B

    .line 59
    const/4 v0, 0x1

    new-array v0, v0, [B

    const/4 v1, -0x1

    const/4 v2, 0x0

    aput-byte v1, v0, v2

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_ACK:[B

    .line 63
    const/16 v0, 0x8

    new-array v0, v0, [B

    fill-array-data v0, :array_1

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_OFF:[B

    .line 66
    const/16 v0, 0xc

    new-array v1, v0, [B

    fill-array-data v1, :array_2

    sput-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_RED:[B

    .line 70
    new-array v0, v0, [B

    fill-array-data v0, :array_3

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_RESTORE:[B

    return-void

    nop

    :array_0
    .array-data 1
        0x2et
        -0x7ft
        0x1t
        0x1t
        0x7ct
    .end array-data

    nop

    :array_1
    .array-data 1
        0x2et
        -0x73t
        0x4t
        0x0t
        0x0t
        0x0t
        0x0t
        0x6et
    .end array-data

    :array_2
    .array-data 1
        0x2et
        -0x73t
        0x8t
        0x1t
        0x8t
        -0x1t
        0x0t
        0x0t
        -0x1t
        -0x15t
        -0x33t
        -0x55t
    .end array-data

    :array_3
    .array-data 1
        0x2et
        -0x73t
        0x8t
        0x1t
        0x8t
        -0x1t
        -0x1t
        -0x1t
        -0x1t
        -0x15t
        -0x33t
        -0x53t
    .end array-data
.end method

.method private constructor <init>(Landroid/content/Context;)V
    .locals 2

    .line 330
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 78
    new-instance v0, Landroid/os/Handler;

    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object v1

    invoke-direct {v0, v1}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    .line 79
    new-instance v0, Ljava/util/ArrayDeque;

    invoke-direct {v0}, Ljava/util/ArrayDeque;-><init>()V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    .line 80
    new-instance v0, Ljava/util/HashSet;

    invoke-direct {v0}, Ljava/util/HashSet;-><init>()V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSeenScanDevices:Ljava/util/Set;

    .line 82
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$1;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;

    .line 167
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$2;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$2;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanCallback:Landroid/bluetooth/BluetoothAdapter$LeScanCallback;

    .line 183
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$3;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$3;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStopScanRunnable:Ljava/lang/Runnable;

    .line 191
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$4;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$4;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectRunnable:Ljava/lang/Runnable;

    .line 199
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$5;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$5;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedStateRunnable:Ljava/lang/Runnable;

    .line 208
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$6;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBlinkRunnable:Ljava/lang/Runnable;

    .line 265
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$7;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    .line 278
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$8;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$8;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    .line 290
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$9;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$9;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFlushAfterAckRunnable:Ljava/lang/Runnable;

    .line 297
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$10;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$10;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    .line 327
    const/4 v0, -0x1

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 328
    const-string v0, ""

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastGear:Ljava/lang/String;

    .line 331
    invoke-virtual {p1}, Landroid/content/Context;->getApplicationContext()Landroid/content/Context;

    move-result-object p1

    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    .line 332
    return-void
.end method

.method static synthetic access$002(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 26
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    return p1
.end method

.method static synthetic access$1000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 26
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    return-object p0
.end method

.method static synthetic access$1002(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 26
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    return-object p1
.end method

.method static synthetic access$102(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 26
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectScheduled:Z

    return p1
.end method

.method static synthetic access$1100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 26
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    return-object p0
.end method

.method static synthetic access$1102(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 26
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    return-object p1
.end method

.method static synthetic access$1202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 26
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyReady:Z

    return p1
.end method

.method static synthetic access$1302(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 26
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStartQueued:Z

    return p1
.end method

.method static synthetic access$1400(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 26
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->closeGatt()V

    return-void
.end method

.method static synthetic access$1500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 26
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect()V

    return-void
.end method

.method static synthetic access$1600(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 26
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->findWriteCharacteristic(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$1700(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 26
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->findNotifyCharacteristic(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$1800(Landroid/bluetooth/BluetoothGattCharacteristic;)V
    .locals 0

    .line 26
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->configureWriteCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)V

    return-void
.end method

.method static synthetic access$1900(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 26
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->queueStartPacket()V

    return-void
.end method

.method static synthetic access$200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 26
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$2000(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 26
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->restoreActiveStateAfterConnect()V

    return-void
.end method

.method static synthetic access$2100(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z
    .locals 0

    .line 26
    invoke-static {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->enableNotifications(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result p0

    return p0
.end method

.method static synthetic access$2200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 26
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->flushNext()V

    return-void
.end method

.method static synthetic access$2300([B)Ljava/lang/String;
    .locals 0

    .line 26
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->bytesToHex([B)Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$2400(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 26
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->writeAck()V

    return-void
.end method

.method static synthetic access$2500(Landroid/bluetooth/BluetoothDevice;[B)Z
    .locals 0

    .line 26
    invoke-static {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->matchesAmbientDevice(Landroid/bluetooth/BluetoothDevice;[B)Z

    move-result p0

    return p0
.end method

.method static synthetic access$2600(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothDevice;I)V
    .locals 0

    .line 26
    invoke-direct {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->logSeenScanDevice(Landroid/bluetooth/BluetoothDevice;I)V

    return-void
.end method

.method static synthetic access$2700(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;
    .locals 0

    .line 26
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$2800(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 26
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopScan()V

    return-void
.end method

.method static synthetic access$2900(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothDevice;)V
    .locals 0

    .line 26
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectDevice(Landroid/bluetooth/BluetoothDevice;)V

    return-void
.end method

.method static synthetic access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;
    .locals 0

    .line 26
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    return-object p0
.end method

.method static synthetic access$3000(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 26
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectIfNeeded()V

    return-void
.end method

.method static synthetic access$3100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 26
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mRequestedOverspeed:Z

    return p0
.end method

.method static synthetic access$3200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 26
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    return p0
.end method

.method static synthetic access$3300(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V
    .locals 0

    .line 26
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setOverspeed(Z)V

    return-void
.end method

.method static synthetic access$3400(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 26
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    return p0
.end method

.method static synthetic access$3500(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 26
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientBrightness()I

    move-result p0

    return p0
.end method

.method static synthetic access$3600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 26
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningAnimationStarted:Z

    return p0
.end method

.method static synthetic access$3602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 26
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningAnimationStarted:Z

    return p1
.end method

.method static synthetic access$3700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 26
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLowLightWarning:Z

    return p0
.end method

.method static synthetic access$3702(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 26
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLowLightWarning:Z

    return p1
.end method

.method static synthetic access$3800()[B
    .locals 1

    .line 26
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_RED:[B

    return-object v0
.end method

.method static synthetic access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V
    .locals 0

    .line 26
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    return-void
.end method

.method static synthetic access$4000(ZII)[B
    .locals 0

    .line 26
    invoke-static {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildBrightnessPacket(ZII)[B

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$402(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGatt;
    .locals 0

    .line 26
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    return-object p1
.end method

.method static synthetic access$4100(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 26
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadePhase:I

    return p0
.end method

.method static synthetic access$4102(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I
    .locals 0

    .line 26
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadePhase:I

    return p1
.end method

.method static synthetic access$4200(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 26
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadeStep:I

    return p0
.end method

.method static synthetic access$4202(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I
    .locals 0

    .line 26
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadeStep:I

    return p1
.end method

.method static synthetic access$4208(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 2

    .line 26
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadeStep:I

    add-int/lit8 v1, v0, 0x1

    iput v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadeStep:I

    return v0
.end method

.method static synthetic access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 26
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    return p0
.end method

.method static synthetic access$4302(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I
    .locals 0

    .line 26
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    return p1
.end method

.method static synthetic access$4400()[B
    .locals 1

    .line 26
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_RESTORE:[B

    return-object v0
.end method

.method static synthetic access$4500(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 26
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    return p0
.end method

.method static synthetic access$4600(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V
    .locals 0

    .line 26
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->syncAmbientBrightness(Z)V

    return-void
.end method

.method static synthetic access$4700(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V
    .locals 0

    .line 26
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setGearText(Ljava/lang/String;)V

    return-void
.end method

.method static synthetic access$4800(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V
    .locals 0

    .line 26
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestOverspeed(Z)V

    return-void
.end method

.method static synthetic access$4900(Lcom/navdy/hud/app/ambient/AmbientLightController;II)V
    .locals 0

    .line 26
    invoke-direct {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestCameraSpeed(II)V

    return-void
.end method

.method static synthetic access$500(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 26
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    return p0
.end method

.method static synthetic access$502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 26
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    return p1
.end method

.method static synthetic access$600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 26
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 26
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 26
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFlushAfterAckRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 26
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method private static buildBrightnessPacket(ZI)[B
    .locals 1

    .line 706
    const/16 v0, 0x28

    invoke-static {p0, p1, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildBrightnessPacket(ZII)[B

    move-result-object p0

    return-object p0
.end method

.method private static buildBrightnessPacket(ZII)[B
    .locals 2

    .line 710
    const/16 v0, 0x64

    const/4 v1, 0x0

    if-eqz p0, :cond_0

    invoke-static {p1, v1, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    goto :goto_0

    :cond_0
    const/4 p1, 0x0

    .line 711
    :goto_0
    if-eqz p0, :cond_1

    invoke-static {p2, v1, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p2

    goto :goto_1

    :cond_1
    const/4 p2, 0x0

    .line 712
    :goto_1
    if-eqz p0, :cond_2

    const/16 p0, 0x48

    goto :goto_2

    :cond_2
    const/4 p0, 0x0

    .line 713
    :goto_2
    const/16 v0, 0x8d

    filled-new-array {v1, p0, p1, p2}, [I

    move-result-object p0

    invoke-static {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildPacket(I[I)[B

    move-result-object p0

    return-object p0
.end method

.method private static buildPacket(I[I)[B
    .locals 8

    .line 717
    array-length v0, p1

    .line 718
    add-int/lit8 v1, v0, 0x4

    new-array v2, v1, [B

    .line 719
    const/16 v3, 0x2e

    const/4 v4, 0x0

    aput-byte v3, v2, v4

    .line 720
    int-to-byte v3, p0

    const/4 v5, 0x1

    aput-byte v3, v2, v5

    .line 721
    const/4 v3, 0x2

    int-to-byte v6, v0

    aput-byte v6, v2, v3

    .line 722
    add-int/2addr p0, v0

    .line 723
    nop

    :goto_0
    if-ge v4, v0, :cond_0

    .line 724
    aget v3, p1, v4

    and-int/lit16 v3, v3, 0xff

    .line 725
    add-int/lit8 v6, v4, 0x3

    int-to-byte v7, v3

    aput-byte v7, v2, v6

    .line 726
    add-int/2addr p0, v3

    .line 723
    add-int/lit8 v4, v4, 0x1

    goto :goto_0

    .line 728
    :cond_0
    sub-int/2addr v1, v5

    not-int p0, p0

    and-int/lit16 p0, p0, 0xff

    int-to-byte p0, p0

    aput-byte p0, v2, v1

    .line 729
    return-object v2
.end method

.method private static bytesToHex([B)Ljava/lang/String;
    .locals 7

    .line 808
    new-instance v0, Ljava/lang/StringBuilder;

    array-length v1, p0

    mul-int/lit8 v1, v1, 0x2

    invoke-direct {v0, v1}, Ljava/lang/StringBuilder;-><init>(I)V

    .line 809
    array-length v1, p0

    const/4 v2, 0x0

    const/4 v3, 0x0

    :goto_0
    if-ge v3, v1, :cond_0

    aget-byte v4, p0, v3

    .line 810
    sget-object v5, Ljava/util/Locale;->US:Ljava/util/Locale;

    and-int/lit16 v4, v4, 0xff

    invoke-static {v4}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;

    move-result-object v4

    const/4 v6, 0x1

    new-array v6, v6, [Ljava/lang/Object;

    aput-object v4, v6, v2

    const-string v4, "%02X"

    invoke-static {v5, v4, v6}, Ljava/lang/String;->format(Ljava/util/Locale;Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v4

    invoke-virtual {v0, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    .line 809
    add-int/lit8 v3, v3, 0x1

    goto :goto_0

    .line 812
    :cond_0
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method private static clamp(III)I
    .locals 0

    .line 733
    invoke-static {p2, p0}, Ljava/lang/Math;->min(II)I

    move-result p0

    invoke-static {p1, p0}, Ljava/lang/Math;->max(II)I

    move-result p0

    return p0
.end method

.method private closeGatt()V
    .locals 1

    .line 621
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    if-eqz v0, :cond_0

    .line 623
    :try_start_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    invoke-virtual {v0}, Landroid/bluetooth/BluetoothGatt;->close()V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 625
    goto :goto_0

    .line 624
    :catch_0
    move-exception v0

    .line 626
    :goto_0
    const/4 v0, 0x0

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    .line 628
    :cond_0
    return-void
.end method

.method private static configureWriteCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)V
    .locals 1

    .line 737
    invoke-virtual {p0}, Landroid/bluetooth/BluetoothGattCharacteristic;->getProperties()I

    move-result v0

    .line 738
    and-int/lit8 v0, v0, 0x4

    if-eqz v0, :cond_0

    .line 739
    const/4 v0, 0x1

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGattCharacteristic;->setWriteType(I)V

    goto :goto_0

    .line 741
    :cond_0
    const/4 v0, 0x2

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGattCharacteristic;->setWriteType(I)V

    .line 743
    :goto_0
    return-void
.end method

.method private connectBondedCandidate()Z
    .locals 4

    .line 591
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    invoke-virtual {v0}, Landroid/bluetooth/BluetoothAdapter;->getBondedDevices()Ljava/util/Set;

    move-result-object v0

    .line 592
    const/4 v1, 0x0

    if-nez v0, :cond_0

    .line 593
    return v1

    .line 595
    :cond_0
    invoke-interface {v0}, Ljava/util/Set;->iterator()Ljava/util/Iterator;

    move-result-object v0

    :goto_0
    invoke-interface {v0}, Ljava/util/Iterator;->hasNext()Z

    move-result v2

    if-eqz v2, :cond_2

    invoke-interface {v0}, Ljava/util/Iterator;->next()Ljava/lang/Object;

    move-result-object v2

    check-cast v2, Landroid/bluetooth/BluetoothDevice;

    .line 596
    if-eqz v2, :cond_1

    const/4 v3, 0x0

    invoke-static {v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->matchesAmbientDevice(Landroid/bluetooth/BluetoothDevice;[B)Z

    move-result v3

    if-eqz v3, :cond_1

    .line 597
    invoke-direct {p0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectDevice(Landroid/bluetooth/BluetoothDevice;)V

    .line 598
    const/4 v0, 0x1

    return v0

    .line 600
    :cond_1
    goto :goto_0

    .line 601
    :cond_2
    return v1
.end method

.method private connectDevice(Landroid/bluetooth/BluetoothDevice;)V
    .locals 3

    .line 605
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->closeGatt()V

    .line 606
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "ambient connect "

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    const-string v1, " "

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {p1}, Landroid/bluetooth/BluetoothDevice;->getAddress()Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    const-string v1, "NavdyAmbient"

    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 607
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    const/4 v1, 0x0

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;

    invoke-virtual {p1, v0, v1, v2}, Landroid/bluetooth/BluetoothDevice;->connectGatt(Landroid/content/Context;ZLandroid/bluetooth/BluetoothGattCallback;)Landroid/bluetooth/BluetoothGatt;

    move-result-object p1

    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    .line 608
    return-void
.end method

.method private connectIfNeeded()V
    .locals 4

    .line 556
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    if-nez v0, :cond_6

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    if-eqz v0, :cond_0

    goto :goto_2

    .line 559
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    if-nez v0, :cond_1

    .line 560
    invoke-static {}, Landroid/bluetooth/BluetoothAdapter;->getDefaultAdapter()Landroid/bluetooth/BluetoothAdapter;

    move-result-object v0

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    .line 562
    :cond_1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    const-string v1, "NavdyAmbient"

    if-eqz v0, :cond_5

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    invoke-virtual {v0}, Landroid/bluetooth/BluetoothAdapter;->isEnabled()Z

    move-result v0

    if-nez v0, :cond_2

    goto :goto_1

    .line 567
    :cond_2
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectBondedCandidate()Z

    move-result v0

    if-eqz v0, :cond_3

    .line 568
    return-void

    .line 570
    :cond_3
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSeenScanDevices:Ljava/util/Set;

    invoke-interface {v0}, Ljava/util/Set;->clear()V

    .line 571
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanCallback:Landroid/bluetooth/BluetoothAdapter$LeScanCallback;

    invoke-virtual {v0, v2}, Landroid/bluetooth/BluetoothAdapter;->startLeScan(Landroid/bluetooth/BluetoothAdapter$LeScanCallback;)Z

    move-result v0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    .line 572
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "ambient scan start="

    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    iget-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 573
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    if-eqz v0, :cond_4

    .line 574
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStopScanRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 575
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStopScanRunnable:Ljava/lang/Runnable;

    const-wide/16 v2, 0x2710

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    goto :goto_0

    .line 577
    :cond_4
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect()V

    .line 579
    :goto_0
    return-void

    .line 563
    :cond_5
    :goto_1
    const-string v0, "bluetooth disabled"

    invoke-static {v1, v0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 564
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect()V

    .line 565
    return-void

    .line 557
    :cond_6
    :goto_2
    return-void
.end method

.method private static enableNotifications(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z
    .locals 5

    .line 746
    const/4 v0, 0x0

    if-eqz p0, :cond_4

    if-nez p1, :cond_0

    goto :goto_2

    .line 749
    :cond_0
    const/4 v1, 0x1

    invoke-virtual {p0, p1, v1}, Landroid/bluetooth/BluetoothGatt;->setCharacteristicNotification(Landroid/bluetooth/BluetoothGattCharacteristic;Z)Z

    move-result v2

    .line 750
    sget-object v3, Lcom/navdy/hud/app/ambient/AmbientLightController;->CLIENT_CONFIG_UUID:Ljava/util/UUID;

    invoke-virtual {p1, v3}, Landroid/bluetooth/BluetoothGattCharacteristic;->getDescriptor(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattDescriptor;

    move-result-object p1

    .line 751
    const-string v3, "NavdyAmbient"

    if-eqz v2, :cond_2

    if-nez p1, :cond_1

    goto :goto_0

    .line 755
    :cond_1
    sget-object v0, Landroid/bluetooth/BluetoothGattDescriptor;->ENABLE_NOTIFICATION_VALUE:[B

    invoke-virtual {p1, v0}, Landroid/bluetooth/BluetoothGattDescriptor;->setValue([B)Z

    .line 756
    invoke-virtual {p0, p1}, Landroid/bluetooth/BluetoothGatt;->writeDescriptor(Landroid/bluetooth/BluetoothGattDescriptor;)Z

    move-result p0

    .line 757
    new-instance p1, Ljava/lang/StringBuilder;

    invoke-direct {p1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v0, "ambient notify setup queued ok="

    invoke-virtual {p1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, p0}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-static {v3, p1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 758
    return p0

    .line 752
    :cond_2
    :goto_0
    new-instance p0, Ljava/lang/StringBuilder;

    invoke-direct {p0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v4, "ambient notify setup local="

    invoke-virtual {p0, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p0

    invoke-virtual {p0, v2}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object p0

    const-string v2, " descriptor="

    invoke-virtual {p0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p0

    if-eqz p1, :cond_3

    goto :goto_1

    :cond_3
    const/4 v1, 0x0

    :goto_1
    invoke-virtual {p0, v1}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object p0

    invoke-virtual {p0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    invoke-static {v3, p0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 753
    return v0

    .line 747
    :cond_4
    :goto_2
    return v0
.end method

.method private static findNotifyCharacteristic(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 1

    .line 773
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->SERVICE_UUID:Ljava/util/UUID;

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;

    move-result-object v0

    .line 774
    if-nez v0, :cond_0

    .line 775
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->LEGACY_SERVICE_UUID:Ljava/util/UUID;

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;

    move-result-object v0

    .line 777
    :cond_0
    if-nez v0, :cond_1

    .line 778
    const/4 p0, 0x0

    return-object p0

    .line 780
    :cond_1
    sget-object p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->NOTIFY_UUID:Ljava/util/UUID;

    invoke-virtual {v0, p0}, Landroid/bluetooth/BluetoothGattService;->getCharacteristic(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p0

    return-object p0
.end method

.method private static findWriteCharacteristic(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 1

    .line 762
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->SERVICE_UUID:Ljava/util/UUID;

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;

    move-result-object v0

    .line 763
    if-nez v0, :cond_0

    .line 764
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->LEGACY_SERVICE_UUID:Ljava/util/UUID;

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;

    move-result-object v0

    .line 766
    :cond_0
    if-nez v0, :cond_1

    .line 767
    const/4 p0, 0x0

    return-object p0

    .line 769
    :cond_1
    sget-object p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->WRITE_UUID:Ljava/util/UUID;

    invoke-virtual {v0, p0}, Landroid/bluetooth/BluetoothGattService;->getCharacteristic(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p0

    return-object p0
.end method

.method private flushNext()V
    .locals 6

    .line 525
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    if-nez v0, :cond_3

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyReady:Z

    if-eqz v0, :cond_3

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    if-eqz v0, :cond_3

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    if-eqz v0, :cond_3

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->isEmpty()Z

    move-result v0

    if-eqz v0, :cond_0

    goto/16 :goto_0

    .line 528
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->poll()Ljava/lang/Object;

    move-result-object v0

    check-cast v0, [B

    .line 529
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v1, v0}, Landroid/bluetooth/BluetoothGattCharacteristic;->setValue([B)Z

    .line 530
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->configureWriteCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)V

    .line 531
    const/4 v1, 0x1

    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    .line 532
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    invoke-virtual {v2, v3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 533
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    invoke-virtual {v2, v3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 534
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    const-wide/16 v4, 0x4b0

    invoke-virtual {v2, v3, v4, v5}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 535
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getWriteType()I

    move-result v2

    if-ne v2, v1, :cond_1

    .line 536
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    const-wide/16 v3, 0x15e

    invoke-virtual {v1, v2, v3, v4}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 538
    :cond_1
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v1, v2}, Landroid/bluetooth/BluetoothGatt;->writeCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result v1

    .line 539
    new-instance v2, Ljava/lang/StringBuilder;

    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V

    const-string v3, "ambient write queued ok="

    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    invoke-virtual {v2, v1}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v2

    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v2

    const-string v3, "NavdyAmbient"

    invoke-static {v3, v2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 540
    if-nez v1, :cond_2

    .line 541
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    invoke-virtual {v1, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 542
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    invoke-virtual {v1, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 543
    const/4 v1, 0x0

    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    .line 544
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v2, v0}, Ljava/util/ArrayDeque;->offerFirst(Ljava/lang/Object;)Z

    .line 545
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    .line 546
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyReady:Z

    .line 547
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStartQueued:Z

    .line 548
    const/4 v0, 0x0

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 549
    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 550
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->closeGatt()V

    .line 551
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect()V

    .line 553
    :cond_2
    return-void

    .line 526
    :cond_3
    :goto_0
    return-void
.end method

.method public static declared-synchronized get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;
    .locals 2

    const-class v0, Lcom/navdy/hud/app/ambient/AmbientLightController;

    monitor-enter v0

    .line 335
    :try_start_0
    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->sInstance:Lcom/navdy/hud/app/ambient/AmbientLightController;

    if-nez v1, :cond_0

    .line 336
    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {v1, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;-><init>(Landroid/content/Context;)V

    sput-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->sInstance:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 338
    :cond_0
    sget-object p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->sInstance:Lcom/navdy/hud/app/ambient/AmbientLightController;
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    monitor-exit v0

    return-object p0

    .line 334
    :catchall_0
    move-exception p0

    :try_start_1
    monitor-exit v0
    :try_end_1
    .catchall {:try_start_1 .. :try_end_1} :catchall_0

    throw p0
.end method

.method private static isDriveGear(Ljava/lang/String;)Z
    .locals 1

    .line 846
    const-string v0, "p"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "park"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    .line 847
    const-string v0, "n"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "neutral"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    .line 848
    const-string v0, "d"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "drive"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p0

    if-eqz p0, :cond_0

    goto :goto_0

    :cond_0
    const/4 p0, 0x0

    goto :goto_1

    :cond_1
    :goto_0
    const/4 p0, 0x1

    .line 846
    :goto_1
    return p0
.end method

.method private static isReverse(Ljava/lang/String;)Z
    .locals 1

    .line 842
    const-string v0, "r"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "reverse"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p0

    if-eqz p0, :cond_0

    goto :goto_0

    :cond_0
    const/4 p0, 0x0

    goto :goto_1

    :cond_1
    :goto_0
    const/4 p0, 0x1

    :goto_1
    return p0
.end method

.method private logSeenScanDevice(Landroid/bluetooth/BluetoothDevice;I)V
    .locals 3

    .line 631
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;

    move-result-object v0

    .line 632
    invoke-virtual {v0}, Ljava/lang/String;->length()I

    move-result v1

    if-nez v1, :cond_0

    .line 633
    return-void

    .line 635
    :cond_0
    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    const-string v2, "|"

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {p1}, Landroid/bluetooth/BluetoothDevice;->getAddress()Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    .line 636
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSeenScanDevices:Ljava/util/Set;

    invoke-interface {v2, v1}, Ljava/util/Set;->add(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_1

    .line 637
    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "ambient seen "

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    const-string v1, " "

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {p1}, Landroid/bluetooth/BluetoothDevice;->getAddress()Ljava/lang/String;

    move-result-object p1

    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    const-string v0, " rssi="

    invoke-virtual {p1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, p2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    const-string p2, "NavdyAmbient"

    invoke-static {p2, p1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 639
    :cond_1
    return-void
.end method

.method private static matchesAmbientDevice(Landroid/bluetooth/BluetoothDevice;[B)Z
    .locals 1

    .line 784
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;

    move-result-object p0

    sget-object p1, Ljava/util/Locale;->US:Ljava/util/Locale;

    invoke-virtual {p0, p1}, Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)Ljava/lang/String;

    move-result-object p0

    .line 785
    const-string p1, "rz-slave"

    invoke-virtual {p0, p1}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result p1

    const/4 v0, 0x0

    if-nez p1, :cond_3

    const-string p1, "rz_slave"

    invoke-virtual {p0, p1}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result p1

    if-nez p1, :cond_3

    const-string p1, "rz slave"

    invoke-virtual {p0, p1}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result p1

    if-nez p1, :cond_3

    .line 786
    const-string p1, "slave"

    invoke-virtual {p0, p1}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result p1

    if-eqz p1, :cond_0

    goto :goto_0

    .line 789
    :cond_0
    const-string p1, "lamp"

    invoke-virtual {p0, p1}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result p1

    if-nez p1, :cond_1

    const-string p1, "frgn"

    invoke-virtual {p0, p1}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result p1

    if-nez p1, :cond_1

    const-string p1, "ambient"

    invoke-virtual {p0, p1}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result p1

    if-nez p1, :cond_1

    .line 790
    const-string p1, "carled"

    invoke-virtual {p0, p1}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result p1

    if-nez p1, :cond_1

    const-string p1, "pocket"

    invoke-virtual {p0, p1}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result p0

    if-eqz p0, :cond_2

    :cond_1
    const/4 v0, 0x1

    .line 789
    :cond_2
    return v0

    .line 787
    :cond_3
    :goto_0
    return v0
.end method

.method private needsConnection()Z
    .locals 1

    .line 642
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    if-nez v0, :cond_1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->isEmpty()Z

    move-result v0

    if-eqz v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-nez v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-eqz v0, :cond_0

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    goto :goto_1

    :cond_1
    :goto_0
    const/4 v0, 0x1

    :goto_1
    return v0
.end method

.method private static normalizeGear(Ljava/lang/String;)Ljava/lang/String;
    .locals 1

    .line 825
    invoke-virtual {p0}, Ljava/lang/String;->trim()Ljava/lang/String;

    move-result-object p0

    sget-object v0, Ljava/util/Locale;->US:Ljava/util/Locale;

    invoke-virtual {p0, v0}, Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)Ljava/lang/String;

    move-result-object p0

    .line 826
    const-string v0, ".reverse"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 827
    const-string p0, "reverse"

    return-object p0

    .line 829
    :cond_0
    const-string v0, ".park"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_1

    .line 830
    const-string p0, "park"

    return-object p0

    .line 832
    :cond_1
    const-string v0, ".neutral"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_2

    .line 833
    const-string p0, "neutral"

    return-object p0

    .line 835
    :cond_2
    const-string v0, ".drive"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_3

    .line 836
    const-string p0, "drive"

    return-object p0

    .line 838
    :cond_3
    return-object p0
.end method

.method public static onCameraSpeedChanged(Landroid/content/Context;II)V
    .locals 2

    .line 383
    if-nez p0, :cond_0

    .line 384
    return-void

    .line 386
    :cond_0
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;

    move-result-object p0

    .line 387
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientLightController$13;

    invoke-direct {v1, p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController$13;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;II)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 393
    return-void
.end method

.method public static onGearText(Landroid/content/Context;Ljava/lang/String;)V
    .locals 2

    .line 357
    if-eqz p0, :cond_1

    if-nez p1, :cond_0

    goto :goto_0

    .line 360
    :cond_0
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;

    move-result-object p0

    .line 361
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientLightController$11;

    invoke-direct {v1, p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController$11;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 367
    return-void

    .line 358
    :cond_1
    :goto_0
    return-void
.end method

.method public static onOpenpilotPayload(Landroid/content/Context;Ljava/lang/String;)V
    .locals 3

    .line 342
    if-eqz p0, :cond_2

    if-nez p1, :cond_0

    goto :goto_1

    .line 346
    :cond_0
    :try_start_0
    new-instance v0, Lorg/json/JSONObject;

    invoke-direct {v0, p1}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    .line 347
    const-string p1, "gear"

    const-string v1, "gearShifter"

    const-string v2, ""

    invoke-virtual {v0, v1, v2}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, p1, v1}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    .line 348
    if-eqz p1, :cond_1

    invoke-virtual {p1}, Ljava/lang/String;->length()I

    move-result v0

    if-lez v0, :cond_1

    .line 349
    invoke-static {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onGearText(Landroid/content/Context;Ljava/lang/String;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 353
    :cond_1
    goto :goto_0

    .line 351
    :catch_0
    move-exception p0

    .line 352
    const-string p1, "NavdyAmbient"

    const-string v0, "bad openpilot payload"

    invoke-static {p1, v0, p0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 354
    :goto_0
    return-void

    .line 343
    :cond_2
    :goto_1
    return-void
.end method

.method public static onOverspeedChanged(Landroid/content/Context;Z)V
    .locals 2

    .line 370
    if-nez p0, :cond_0

    .line 371
    return-void

    .line 373
    :cond_0
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;

    move-result-object p0

    .line 374
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientLightController$12;

    invoke-direct {v1, p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController$12;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 380
    return-void
.end method

.method private queueStartPacket()V
    .locals 2

    .line 646
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStartQueued:Z

    if-eqz v0, :cond_0

    .line 647
    return-void

    .line 649
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_START:[B

    invoke-virtual {v1}, [B->clone()Ljava/lang/Object;

    move-result-object v1

    check-cast v1, [B

    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offerFirst(Ljava/lang/Object;)Z

    .line 650
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStartQueued:Z

    .line 651
    return-void
.end method

.method private readAmbientBrightness()I
    .locals 5

    .line 678
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readScreenBrightness()I

    move-result v0

    .line 679
    const/4 v1, 0x1

    const/16 v2, 0x10

    if-gt v0, v2, :cond_0

    .line 680
    return v1

    .line 682
    :cond_0
    const/16 v3, 0x29

    const/16 v4, 0x8

    if-gt v0, v3, :cond_1

    .line 683
    nop

    .line 684
    nop

    .line 685
    sub-int/2addr v0, v2

    mul-int/lit8 v0, v0, 0x7

    add-int/lit8 v0, v0, 0xc

    div-int/lit8 v0, v0, 0x19

    add-int/2addr v0, v1

    .line 688
    invoke-static {v0, v1, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v0

    return v0

    .line 690
    :cond_1
    const/16 v1, 0x64

    const/16 v2, 0x32

    if-gt v0, v1, :cond_2

    .line 691
    nop

    .line 692
    nop

    .line 693
    sub-int/2addr v0, v3

    mul-int/lit8 v0, v0, 0x2a

    add-int/lit8 v0, v0, 0x1d

    div-int/lit8 v0, v0, 0x3b

    add-int/2addr v0, v4

    .line 696
    invoke-static {v0, v4, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v0

    return v0

    .line 698
    :cond_2
    return v2
.end method

.method private readScreenBrightness()I
    .locals 3

    .line 702
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v0

    const-string v1, "screen_brightness"

    const/16 v2, 0xff

    invoke-static {v0, v1, v2}, Landroid/provider/Settings$System;->getInt(Landroid/content/ContentResolver;Ljava/lang/String;I)I

    move-result v0

    const/4 v1, 0x0

    invoke-static {v0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v0

    return v0
.end method

.method private requestCameraSpeed(II)V
    .locals 0

    .line 396
    if-lez p2, :cond_2

    if-gt p1, p2, :cond_0

    goto :goto_0

    .line 398
    :cond_0
    add-int/lit8 p2, p2, 0x2

    if-lt p1, p2, :cond_1

    .line 399
    const/4 p1, 0x1

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestOverspeed(Z)V

    goto :goto_1

    .line 402
    :cond_1
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestOverspeed(Z)V

    goto :goto_1

    .line 397
    :cond_2
    :goto_0
    const/4 p1, 0x0

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestOverspeed(Z)V

    .line 404
    :goto_1
    return-void
.end method

.method private requestOverspeed(Z)V
    .locals 8

    .line 407
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mRequestedOverspeed:Z

    if-ne v0, p1, :cond_0

    .line 408
    return-void

    .line 410
    :cond_0
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mRequestedOverspeed:Z

    .line 411
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedStateRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 412
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-ne v0, p1, :cond_1

    .line 413
    return-void

    .line 416
    :cond_1
    if-eqz p1, :cond_2

    const-wide/16 v0, 0x3e8

    goto :goto_0

    :cond_2
    const-wide/16 v0, 0x7d0

    .line 417
    :goto_0
    const-wide/16 v2, 0x0

    if-nez p1, :cond_3

    iget-wide v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActivatedAtMs:J

    cmp-long v6, v4, v2

    if-lez v6, :cond_3

    .line 418
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v4

    iget-wide v6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActivatedAtMs:J

    sub-long/2addr v4, v6

    .line 419
    const-wide/16 v6, 0xbb8

    sub-long/2addr v6, v4

    invoke-static {v0, v1, v6, v7}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v0

    .line 421
    :cond_3
    new-instance v4, Ljava/lang/StringBuilder;

    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    const-string v5, "camera overspeed requested="

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    invoke-virtual {v4, p1}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object p1

    const-string v4, " delayMs="

    invoke-virtual {p1, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-static {v2, v3, v0, v1}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v4

    invoke-virtual {p1, v4, v5}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    const-string v4, "NavdyAmbient"

    invoke-static {v4, p1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 422
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedStateRunnable:Ljava/lang/Runnable;

    invoke-static {v2, v3, v0, v1}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v0

    invoke-virtual {p1, v4, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 423
    return-void
.end method

.method private restoreActiveStateAfterConnect()V
    .locals 2

    .line 654
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-eqz v0, :cond_0

    .line 655
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_OFF:[B

    invoke-virtual {v1}, [B->clone()Ljava/lang/Object;

    move-result-object v1

    check-cast v1, [B

    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 656
    return-void

    .line 658
    :cond_0
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-eqz v0, :cond_1

    .line 659
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBlink()V

    .line 660
    return-void

    .line 662
    :cond_1
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    if-eqz v0, :cond_2

    .line 663
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    .line 665
    :cond_2
    return-void
.end method

.method private static safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;
    .locals 1

    .line 817
    const-string v0, ""

    :try_start_0
    invoke-virtual {p0}, Landroid/bluetooth/BluetoothDevice;->getName()Ljava/lang/String;

    move-result-object p0
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 818
    if-nez p0, :cond_0

    goto :goto_0

    :cond_0
    move-object v0, p0

    :goto_0
    return-object v0

    .line 819
    :catch_0
    move-exception p0

    .line 820
    return-object v0
.end method

.method private static scanRecordContainsAmbientUuid([B)Z
    .locals 5

    .line 794
    const/4 v0, 0x0

    if-nez p0, :cond_0

    .line 795
    return v0

    .line 797
    :cond_0
    const/4 v1, 0x0

    :goto_0
    add-int/lit8 v2, v1, 0x1

    array-length v3, p0

    if-ge v2, v3, :cond_4

    .line 798
    aget-byte v1, p0, v1

    and-int/lit16 v1, v1, 0xff

    .line 799
    aget-byte v3, p0, v2

    and-int/lit16 v3, v3, 0xff

    .line 800
    if-eqz v1, :cond_1

    const/16 v4, 0x30

    if-ne v1, v4, :cond_2

    :cond_1
    const/16 v1, 0xae

    if-eq v3, v1, :cond_3

    const/16 v1, 0xaf

    if-ne v3, v1, :cond_2

    goto :goto_1

    .line 797
    :cond_2
    move v1, v2

    goto :goto_0

    .line 801
    :cond_3
    :goto_1
    const/4 p0, 0x1

    return p0

    .line 804
    :cond_4
    return v0
.end method

.method private scheduleReconnect()V
    .locals 4

    .line 582
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->needsConnection()Z

    move-result v0

    if-eqz v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    if-nez v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    if-nez v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectScheduled:Z

    if-eqz v0, :cond_0

    goto :goto_0

    .line 585
    :cond_0
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectScheduled:Z

    .line 586
    const-string v0, "NavdyAmbient"

    const-string v1, "ambient reconnect scheduled"

    invoke-static {v0, v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 587
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectRunnable:Ljava/lang/Runnable;

    const-wide/16 v2, 0x1388

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 588
    return-void

    .line 583
    :cond_1
    :goto_0
    return-void
.end method

.method private sendPacket([B)V
    .locals 2

    .line 516
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->size()I

    move-result v0

    const/16 v1, 0x14

    if-le v0, v1, :cond_0

    .line 517
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->poll()Ljava/lang/Object;

    .line 519
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {p1}, [B->clone()Ljava/lang/Object;

    move-result-object p1

    check-cast p1, [B

    invoke-virtual {v0, p1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 520
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectIfNeeded()V

    .line 521
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->flushNext()V

    .line 522
    return-void
.end method

.method private setGearText(Ljava/lang/String;)V
    .locals 3

    .line 426
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalizeGear(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    .line 427
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastGear:Ljava/lang/String;

    invoke-virtual {p1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 428
    return-void

    .line 430
    :cond_0
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastGear:Ljava/lang/String;

    .line 431
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "gear="

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    const-string v1, "NavdyAmbient"

    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 433
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isReverse(Ljava/lang/String;)Z

    move-result v0

    const/4 v1, 0x0

    const/4 v2, 0x1

    if-eqz v0, :cond_1

    .line 434
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    .line 435
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 436
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 437
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBrightnessSync()V

    .line 438
    sget-object p1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_OFF:[B

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    .line 439
    return-void

    .line 442
    :cond_1
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isDriveGear(Ljava/lang/String;)Z

    move-result p1

    if-eqz p1, :cond_3

    .line 443
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    .line 444
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 445
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    .line 446
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-eqz p1, :cond_2

    .line 447
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBlink()V

    goto :goto_0

    .line 449
    :cond_2
    sget-object p1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_RESTORE:[B

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    .line 452
    :cond_3
    :goto_0
    return-void
.end method

.method private setOverspeed(Z)V
    .locals 2

    .line 455
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-ne v0, p1, :cond_0

    .line 456
    return-void

    .line 458
    :cond_0
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    .line 459
    if-eqz p1, :cond_1

    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    goto :goto_0

    :cond_1
    const-wide/16 v0, 0x0

    :goto_0
    iput-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActivatedAtMs:J

    .line 460
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "camera overspeed="

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    const-string v1, "NavdyAmbient"

    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 461
    if-eqz p1, :cond_2

    .line 462
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez p1, :cond_3

    .line 463
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBlink()V

    goto :goto_1

    .line 466
    :cond_2
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 467
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez p1, :cond_3

    .line 468
    const/4 p1, 0x1

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->syncAmbientBrightness(Z)V

    .line 469
    sget-object p1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_RESTORE:[B

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    .line 472
    :cond_3
    :goto_1
    return-void
.end method

.method private startBlink()V
    .locals 2

    .line 475
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 476
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 477
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    .line 478
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBlinkRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 479
    return-void
.end method

.method private startBrightnessSync()V
    .locals 4

    .line 490
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 491
    const/4 v0, 0x1

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->syncAmbientBrightness(Z)V

    .line 492
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    const-wide/16 v2, 0x1388

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 493
    return-void
.end method

.method private stopBlink()V
    .locals 2

    .line 482
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBlinkRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 483
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningAnimationStarted:Z

    .line 484
    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLowLightWarning:Z

    .line 485
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadePhase:I

    .line 486
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadeStep:I

    .line 487
    return-void
.end method

.method private stopBrightnessSync()V
    .locals 2

    .line 496
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 497
    const/4 v0, -0x1

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 498
    return-void
.end method

.method private stopScan()V
    .locals 2

    .line 611
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    if-eqz v0, :cond_1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    if-nez v0, :cond_0

    goto :goto_0

    .line 614
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanCallback:Landroid/bluetooth/BluetoothAdapter$LeScanCallback;

    invoke-virtual {v0, v1}, Landroid/bluetooth/BluetoothAdapter;->stopLeScan(Landroid/bluetooth/BluetoothAdapter$LeScanCallback;)V

    .line 615
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    .line 616
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStopScanRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 617
    const-string v0, "NavdyAmbient"

    const-string v1, "ambient scan stop"

    invoke-static {v0, v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 618
    return-void

    .line 612
    :cond_1
    :goto_0
    return-void
.end method

.method private syncAmbientBrightness(Z)V
    .locals 2

    .line 501
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientBrightness()I

    move-result v0

    .line 502
    iget-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-eqz v1, :cond_0

    iget-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningAnimationStarted:Z

    if-eqz v1, :cond_0

    .line 503
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 504
    return-void

    .line 506
    :cond_0
    if-nez p1, :cond_1

    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    if-ltz p1, :cond_1

    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    sub-int p1, v0, p1

    .line 507
    invoke-static {p1}, Ljava/lang/Math;->abs(I)I

    move-result p1

    const/4 v1, 0x2

    if-ge p1, v1, :cond_1

    .line 508
    return-void

    .line 510
    :cond_1
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 511
    new-instance p1, Ljava/lang/StringBuilder;

    invoke-direct {p1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "ambient brightness="

    invoke-virtual {p1, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, v0}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object p1

    const-string v1, " screen="

    invoke-virtual {p1, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readScreenBrightness()I

    move-result v1

    invoke-virtual {p1, v1}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    const-string v1, "NavdyAmbient"

    invoke-static {v1, p1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 512
    const/4 p1, 0x1

    const/16 v1, 0x28

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildBrightnessPacket(ZII)[B

    move-result-object p1

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    .line 513
    return-void
.end method

.method private writeAck()V
    .locals 3

    .line 668
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    if-eqz v0, :cond_1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    if-nez v0, :cond_0

    goto :goto_0

    .line 671
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_ACK:[B

    invoke-virtual {v0, v1}, Landroid/bluetooth/BluetoothGattCharacteristic;->setValue([B)Z

    .line 672
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->configureWriteCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)V

    .line 673
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v0, v1}, Landroid/bluetooth/BluetoothGatt;->writeCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result v0

    .line 674
    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "ambient ack queued ok="

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    const-string v1, "NavdyAmbient"

    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 675
    return-void

    .line 669
    :cond_1
    :goto_0
    return-void
.end method
