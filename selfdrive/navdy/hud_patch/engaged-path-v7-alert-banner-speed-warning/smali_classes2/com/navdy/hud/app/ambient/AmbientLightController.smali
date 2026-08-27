.class public final Lcom/navdy/hud/app/ambient/AmbientLightController;
.super Ljava/lang/Object;
.source "AmbientLightController.java"


# static fields
.field private static final ACK_SETTLE_INTERVAL_SETTING:Ljava/lang/String; = "navdy_ambient_ack_settle_ms"

.field private static final AMBIENT_DEVICE_ADDRESS_SETTING:Ljava/lang/String; = "navdy_ambient_device_address"

.field private static final AMBIENT_NORMAL_FADE_MS:J = 0x3e8L

.field private static final AMBIENT_TRANSITION_STEP_SETTING:Ljava/lang/String; = "navdy_ambient_transition_step_ms"

.field private static final BRIGHTNESS_SYNC_INTERVAL_MS:J = 0x1388L

.field private static final BRIGHTNESS_UPDATE_DELTA:I = 0x2

.field private static final CLIENT_CONFIG_UUID:Ljava/util/UUID;

.field private static final CONNECT_ATTEMPT_TIMEOUT_MS:J = 0x2710L

.field private static final CONNECT_RETRY_MS:J = 0x1388L

.field private static final DEFAULT_ACK_SETTLE_INTERVAL_MS:I = 0xa

.field private static final DEFAULT_AMBIENT_TRANSITION_STEP_MS:I = 0x21

.field private static final FADE_PHASE_ENTRY_WHITE_DOWN:I = 0x0

.field private static final FADE_PHASE_EXIT_RED_DOWN:I = 0x3

.field private static final FADE_PHASE_EXIT_WHITE_UP:I = 0x4

.field private static final FADE_PHASE_RED_DOWN:I = 0x2

.field private static final FADE_PHASE_RED_UP:I = 0x1

.field private static final FADE_STEPS:I = 0x2

.field private static final FADE_STEP_INTERVAL_MS:J = 0x15eL

.field private static final GATT_ERROR_RETRY_MS:J = 0x5dcL

.field private static final LEGACY_SERVICE_UUID:Ljava/util/UUID;

.field private static final LOW_LIGHT_CHECK_INTERVAL_MS:J = 0x3e8L

.field private static final MAX_ACK_SETTLE_INTERVAL_MS:I = 0x64

.field private static final MAX_AMBIENT_BRIGHTNESS:I = 0x32

.field private static final MAX_AMBIENT_TRANSITION_STEP_MS:I = 0xfa

.field private static final MID_AMBIENT_BRIGHTNESS:I = 0x8

.field private static final MIN_ACK_SETTLE_INTERVAL_MS:I = 0x5

.field private static final MIN_AMBIENT_BRIGHTNESS:I = 0x1

.field private static final MIN_AMBIENT_TRANSITION_STEP_MS:I = 0x21

.field private static final MIN_FADE_AMBIENT_BRIGHTNESS:I = 0x8

.field private static final NOTIFY_UUID:Ljava/util/UUID;

.field private static final OFFROAD_DELAYED_OFF_MS:J = 0xea60L

.field private static final OFFROAD_DOOR_CLOSE_DELAY_MS:J = 0x4e20L

.field private static final OFFROAD_DOOR_MAX_ON_MS:J = 0x124f80L

.field private static final OFFROAD_DOOR_ZONE_1_BRIGHTNESS:I = 0x14

.field private static final OFFROAD_DOOR_ZONE_2_BRIGHTNESS:I = 0x64

.field private static final OFFROAD_TRANSITION_LIGHT_MS:J = 0x1d4c0L

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

.field private static final START_PACKET_PACE_INTERVAL_MS:J = 0x78L

.field private static final TAG:Ljava/lang/String; = "NavdyAmbient"

.field private static final VEHICLE_DATA_TIMEOUT_MS:J = 0xbb8L

.field private static final WRITE_UUID:Ljava/util/UUID;

.field private static final ZONE_2_AMBIENT_BRIGHTNESS:I = 0x28

.field private static sInstance:Lcom/navdy/hud/app/ambient/AmbientLightController;


# instance fields
.field private mAdapter:Landroid/bluetooth/BluetoothAdapter;

.field private mAmbientActive:Z

.field private mAmbientFadeDurationMs:J

.field private final mAmbientFadeRunnable:Ljava/lang/Runnable;

.field private mAmbientFadeStartZone1:I

.field private mAmbientFadeStartZone2:I

.field private mAmbientFadeStartedAtMs:J

.field private mAmbientTargetZone1:I

.field private mAmbientTargetZone2:I

.field private final mBlinkRunnable:Ljava/lang/Runnable;

.field private final mBrightnessSyncRunnable:Ljava/lang/Runnable;

.field private final mConnectTimeoutRunnable:Ljava/lang/Runnable;

.field private mConnected:Z

.field private mConnecting:Z

.field private final mContext:Landroid/content/Context;

.field private final mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

.field private mCurrentZone1:I

.field private mCurrentZone2:I

.field private mDoorOpen:Z

.field private mFadePhase:I

.field private mFadeStep:I

.field private final mFlushAfterAckRunnable:Ljava/lang/Runnable;

.field private mGatt:Landroid/bluetooth/BluetoothGatt;

.field private final mGattCallback:Landroid/bluetooth/BluetoothGattCallback;

.field private final mHandler:Landroid/os/Handler;

.field private mLastAmbientBrightness:I

.field private mLastGear:Ljava/lang/String;

.field private mLastVehicleDataAtMs:J

.field private mLowLightWarning:Z

.field private mNotifyCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

.field private mNotifyReady:Z

.field private final mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

.field private final mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

.field private mOffroadDoorMaxExpired:Z

.field private final mOffroadDoorMaxRunnable:Ljava/lang/Runnable;

.field private mOnroad:Z

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

.field private mSkipRememberedOnce:Z

.field private mStartQueued:Z

.field private final mStopScanRunnable:Ljava/lang/Runnable;

.field private mVehicleDataTimedOut:Z

.field private final mVehicleDataWatchdogRunnable:Ljava/lang/Runnable;

.field private mVehicleStateKnown:Z

.field private mWarningAnimationStarted:Z

.field private mWarningColorRed:Z

.field private mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

.field private final mWritePaceRunnable:Ljava/lang/Runnable;

.field private final mWriteTimeoutRunnable:Ljava/lang/Runnable;

.field private mWriting:Z


# direct methods
.method static constructor <clinit>()V
    .locals 3

    .line 29
    const-string v0, "0000ae30-0000-1000-8000-00805f9b34fb"

    invoke-static {v0}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;

    move-result-object v0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->SERVICE_UUID:Ljava/util/UUID;

    .line 30
    const-string v0, "0000ae00-0000-1000-8000-00805f9b34fb"

    invoke-static {v0}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;

    move-result-object v0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->LEGACY_SERVICE_UUID:Ljava/util/UUID;

    .line 31
    const-string v0, "0000ae01-0000-1000-8000-00805f9b34fb"

    invoke-static {v0}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;

    move-result-object v0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->WRITE_UUID:Ljava/util/UUID;

    .line 32
    const-string v0, "0000ae02-0000-1000-8000-00805f9b34fb"

    invoke-static {v0}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;

    move-result-object v0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->NOTIFY_UUID:Ljava/util/UUID;

    .line 33
    const-string v0, "00002902-0000-1000-8000-00805f9b34fb"

    invoke-static {v0}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;

    move-result-object v0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->CLIENT_CONFIG_UUID:Ljava/util/UUID;

    .line 78
    const/4 v0, 0x5

    new-array v0, v0, [B

    fill-array-data v0, :array_0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_START:[B

    .line 81
    const/4 v0, 0x1

    new-array v0, v0, [B

    const/4 v1, -0x1

    const/4 v2, 0x0

    aput-byte v1, v0, v2

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_ACK:[B

    .line 85
    const/16 v0, 0x8

    new-array v0, v0, [B

    fill-array-data v0, :array_1

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_OFF:[B

    .line 88
    const/16 v0, 0xc

    new-array v1, v0, [B

    fill-array-data v1, :array_2

    sput-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_RED:[B

    .line 92
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
    .locals 3

    .line 490
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 101
    new-instance v0, Landroid/os/Handler;

    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object v1

    invoke-direct {v0, v1}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    .line 102
    new-instance v0, Ljava/util/ArrayDeque;

    invoke-direct {v0}, Ljava/util/ArrayDeque;-><init>()V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    .line 103
    new-instance v0, Ljava/util/HashSet;

    invoke-direct {v0}, Ljava/util/HashSet;-><init>()V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSeenScanDevices:Ljava/util/Set;

    .line 105
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$1;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;

    .line 201
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$2;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$2;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanCallback:Landroid/bluetooth/BluetoothAdapter$LeScanCallback;

    .line 217
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$3;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$3;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStopScanRunnable:Ljava/lang/Runnable;

    .line 225
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$4;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$4;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectRunnable:Ljava/lang/Runnable;

    .line 233
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$5;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$5;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnectTimeoutRunnable:Ljava/lang/Runnable;

    .line 245
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$6;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$6;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedStateRunnable:Ljava/lang/Runnable;

    .line 254
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$7;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$7;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBlinkRunnable:Ljava/lang/Runnable;

    .line 329
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$8;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$8;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    .line 342
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$9;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$9;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    .line 354
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$10;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$10;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFlushAfterAckRunnable:Ljava/lang/Runnable;

    .line 362
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$11;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$11;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    .line 373
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$12;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeRunnable:Ljava/lang/Runnable;

    .line 394
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$13;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$13;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    .line 403
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$14;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxRunnable:Ljava/lang/Runnable;

    .line 413
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$15;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    .line 422
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$16;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataWatchdogRunnable:Ljava/lang/Runnable;

    .line 487
    const/4 v0, -0x1

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 488
    const-string v0, ""

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastGear:Ljava/lang/String;

    .line 491
    invoke-virtual {p1}, Landroid/content/Context;->getApplicationContext()Landroid/content/Context;

    move-result-object p1

    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    .line 492
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    const-string v0, "power"

    invoke-virtual {p1, v0}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object p1

    check-cast p1, Landroid/os/PowerManager;

    .line 493
    if-nez p1, :cond_0

    const/4 p1, 0x0

    goto :goto_0

    .line 494
    :cond_0
    const/4 v0, 0x1

    const-string v1, "NavdyAmbient:OffroadController"

    invoke-virtual {p1, v0, v1}, Landroid/os/PowerManager;->newWakeLock(ILjava/lang/String;)Landroid/os/PowerManager$WakeLock;

    move-result-object p1

    :goto_0
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    .line 495
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    if-eqz p1, :cond_1

    .line 496
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    const/4 v0, 0x0

    invoke-virtual {p1, v0}, Landroid/os/PowerManager$WakeLock;->setReferenceCounted(Z)V

    .line 498
    :cond_1
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    iput-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastVehicleDataAtMs:J

    .line 499
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataWatchdogRunnable:Ljava/lang/Runnable;

    const-wide/16 v1, 0xbb8

    invoke-virtual {p1, v0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 500
    return-void
.end method

.method static synthetic access$000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGatt;
    .locals 0

    .line 27
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    return-object p0
.end method

.method static synthetic access$002(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGatt;
    .locals 0

    .line 27
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    return-object p1
.end method

.method static synthetic access$100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 27
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    return p0
.end method

.method static synthetic access$1000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 27
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$102(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    return p1
.end method

.method static synthetic access$1100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 27
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFlushAfterAckRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$1200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 27
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$1300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 27
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    return-object p0
.end method

.method static synthetic access$1302(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 27
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    return-object p1
.end method

.method static synthetic access$1400(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 27
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    return-object p0
.end method

.method static synthetic access$1402(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 27
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    return-object p1
.end method

.method static synthetic access$1502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyReady:Z

    return p1
.end method

.method static synthetic access$1602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStartQueued:Z

    return p1
.end method

.method static synthetic access$1700(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->closeGatt()V

    return-void
.end method

.method static synthetic access$1800(Lcom/navdy/hud/app/ambient/AmbientLightController;J)V
    .locals 0

    .line 27
    invoke-direct {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    return-void
.end method

.method static synthetic access$1900(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 27
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->findWriteCharacteristic(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 27
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnectTimeoutRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$2000(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 27
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->findNotifyCharacteristic(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$2100(Landroid/bluetooth/BluetoothGattCharacteristic;)V
    .locals 0

    .line 27
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->configureWriteCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)V

    return-void
.end method

.method static synthetic access$2200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->queueStartPacket()V

    return-void
.end method

.method static synthetic access$2300(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->restoreActiveStateAfterConnect()V

    return-void
.end method

.method static synthetic access$2400(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z
    .locals 0

    .line 27
    invoke-static {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->enableNotifications(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result p0

    return p0
.end method

.method static synthetic access$2500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->flushNext()V

    return-void
.end method

.method static synthetic access$2600([B)Ljava/lang/String;
    .locals 0

    .line 27
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->bytesToHex([B)Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$2700(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->writeAck()V

    return-void
.end method

.method static synthetic access$2800(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAckSettleIntervalMs()I

    move-result p0

    return p0
.end method

.method static synthetic access$2900(Landroid/bluetooth/BluetoothDevice;[B)Z
    .locals 0

    .line 27
    invoke-static {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->matchesAmbientDevice(Landroid/bluetooth/BluetoothDevice;[B)Z

    move-result p0

    return p0
.end method

.method static synthetic access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;
    .locals 0

    .line 27
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    return-object p0
.end method

.method static synthetic access$3000(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothDevice;I)V
    .locals 0

    .line 27
    invoke-direct {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->logSeenScanDevice(Landroid/bluetooth/BluetoothDevice;I)V

    return-void
.end method

.method static synthetic access$3100(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;
    .locals 0

    .line 27
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$3200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopScan()V

    return-void
.end method

.method static synthetic access$3300(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothDevice;)V
    .locals 0

    .line 27
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectDevice(Landroid/bluetooth/BluetoothDevice;)V

    return-void
.end method

.method static synthetic access$3400(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect()V

    return-void
.end method

.method static synthetic access$3500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectIfNeeded()V

    return-void
.end method

.method static synthetic access$3600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 27
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mRequestedOverspeed:Z

    return p0
.end method

.method static synthetic access$3602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mRequestedOverspeed:Z

    return p1
.end method

.method static synthetic access$3700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 27
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    return p0
.end method

.method static synthetic access$3702(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    return p1
.end method

.method static synthetic access$3800(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V
    .locals 0

    .line 27
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setOverspeed(Z)V

    return-void
.end method

.method static synthetic access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 27
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadePhase:I

    return p0
.end method

.method static synthetic access$3902(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I
    .locals 0

    .line 27
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadePhase:I

    return p1
.end method

.method static synthetic access$4000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 27
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    return p0
.end method

.method static synthetic access$402(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSkipRememberedOnce:Z

    return p1
.end method

.method static synthetic access$4100(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientBrightness()I

    move-result p0

    return p0
.end method

.method static synthetic access$4200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 27
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningAnimationStarted:Z

    return p0
.end method

.method static synthetic access$4202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningAnimationStarted:Z

    return p1
.end method

.method static synthetic access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 27
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLowLightWarning:Z

    return p0
.end method

.method static synthetic access$4302(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLowLightWarning:Z

    return p1
.end method

.method static synthetic access$4400()[B
    .locals 1

    .line 27
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_RED:[B

    return-object v0
.end method

.method static synthetic access$4500(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V
    .locals 0

    .line 27
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    return-void
.end method

.method static synthetic access$4600(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->warningZone2Brightness()I

    move-result p0

    return p0
.end method

.method static synthetic access$4700(ZII)[B
    .locals 0

    .line 27
    invoke-static {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildBrightnessPacket(ZII)[B

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$4802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningColorRed:Z

    return p1
.end method

.method static synthetic access$4900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 27
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadeStep:I

    return p0
.end method

.method static synthetic access$4902(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I
    .locals 0

    .line 27
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadeStep:I

    return p1
.end method

.method static synthetic access$500(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 27
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    return p0
.end method

.method static synthetic access$5000(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 27
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    return p0
.end method

.method static synthetic access$5002(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I
    .locals 0

    .line 27
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    return p1
.end method

.method static synthetic access$502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    return p1
.end method

.method static synthetic access$5100()[B
    .locals 1

    .line 27
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_RESTORE:[B

    return-object v0
.end method

.method static synthetic access$5200(Lcom/navdy/hud/app/ambient/AmbientLightController;I)V
    .locals 0

    .line 27
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->finishRestoreFade(I)V

    return-void
.end method

.method static synthetic access$5300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 27
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    return p0
.end method

.method static synthetic access$5400(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V
    .locals 0

    .line 27
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->syncAmbientBrightness(Z)V

    return-void
.end method

.method static synthetic access$5500(Lcom/navdy/hud/app/ambient/AmbientLightController;)J
    .locals 2

    .line 27
    iget-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartedAtMs:J

    return-wide v0
.end method

.method static synthetic access$5600(Lcom/navdy/hud/app/ambient/AmbientLightController;)J
    .locals 2

    .line 27
    iget-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeDurationMs:J

    return-wide v0
.end method

.method static synthetic access$5700(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 27
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1:I

    return p0
.end method

.method static synthetic access$5800(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 27
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    return p0
.end method

.method static synthetic access$5900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 27
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2:I

    return p0
.end method

.method static synthetic access$6000(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 27
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    return p0
.end method

.method static synthetic access$602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectScheduled:Z

    return p1
.end method

.method static synthetic access$6100(Lcom/navdy/hud/app/ambient/AmbientLightController;IIZ)V
    .locals 0

    .line 27
    invoke-direct {p0, p1, p2, p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->applyAmbientBrightness(IIZ)V

    return-void
.end method

.method static synthetic access$6200(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientTransitionStepMs()I

    move-result p0

    return p0
.end method

.method static synthetic access$6300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 27
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    return p0
.end method

.method static synthetic access$6302(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    return p1
.end method

.method static synthetic access$6400(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 27
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    return p0
.end method

.method static synthetic access$6402(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    return p1
.end method

.method static synthetic access$6500(Lcom/navdy/hud/app/ambient/AmbientLightController;IIJ)V
    .locals 0

    .line 27
    invoke-direct {p0, p1, p2, p3, p4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    return-void
.end method

.method static synthetic access$6602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    return p1
.end method

.method static synthetic access$6700(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V
    .locals 0

    .line 27
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    return-void
.end method

.method static synthetic access$6800(Lcom/navdy/hud/app/ambient/AmbientLightController;)J
    .locals 2

    .line 27
    iget-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastVehicleDataAtMs:J

    return-wide v0
.end method

.method static synthetic access$6902(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    return p1
.end method

.method static synthetic access$700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 27
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$7000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 27
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    return p0
.end method

.method static synthetic access$7002(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    return p1
.end method

.method static synthetic access$7100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 27
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedStateRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$7202(Lcom/navdy/hud/app/ambient/AmbientLightController;J)J
    .locals 0

    .line 27
    iput-wide p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActivatedAtMs:J

    return-wide p1
.end method

.method static synthetic access$7300(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    return-void
.end method

.method static synthetic access$7400(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBrightnessSync()V

    return-void
.end method

.method static synthetic access$7500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->cancelOffroadTimers()V

    return-void
.end method

.method static synthetic access$7600(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->updateCpuWakeLock()V

    return-void
.end method

.method static synthetic access$7700(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 27
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->noteVehicleDataReceived()V

    return-void
.end method

.method static synthetic access$7800(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V
    .locals 0

    .line 27
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setGearText(Ljava/lang/String;)V

    return-void
.end method

.method static synthetic access$7900(Lcom/navdy/hud/app/ambient/AmbientLightController;ZZ)V
    .locals 0

    .line 27
    invoke-direct {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setVehicleState(ZZ)V

    return-void
.end method

.method static synthetic access$800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 27
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    return p0
.end method

.method static synthetic access$8000(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V
    .locals 0

    .line 27
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestOverspeed(Z)V

    return-void
.end method

.method static synthetic access$802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 27
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    return p1
.end method

.method static synthetic access$8100(Lcom/navdy/hud/app/ambient/AmbientLightController;II)V
    .locals 0

    .line 27
    invoke-direct {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestCameraSpeed(II)V

    return-void
.end method

.method static synthetic access$900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 27
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method private applyAmbientBrightness(IIZ)V
    .locals 2

    .line 872
    const/4 v0, 0x0

    const/16 v1, 0x64

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    .line 873
    invoke-static {p2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2:I

    .line 874
    if-eqz p3, :cond_0

    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    if-nez p1, :cond_0

    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2:I

    if-nez p1, :cond_0

    .line 875
    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 876
    sget-object p1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_OFF:[B

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    goto :goto_0

    .line 878
    :cond_0
    const/4 p1, 0x1

    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 879
    iget p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    iget p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2:I

    invoke-static {p1, p2, p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildBrightnessPacket(ZII)[B

    move-result-object p1

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    .line 881
    :goto_0
    return-void
.end method

.method private applyVehicleStateTargets()V
    .locals 5

    .line 736
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez v0, :cond_3

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-eqz v0, :cond_0

    goto :goto_1

    .line 738
    :cond_0
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    const-wide/16 v1, 0x3e8

    const/16 v3, 0x64

    if-eqz v0, :cond_2

    .line 739
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientBrightness()I

    move-result v0

    iget-boolean v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eqz v4, :cond_1

    goto :goto_0

    :cond_1
    const/16 v3, 0x28

    :goto_0
    invoke-direct {p0, v0, v3, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    goto :goto_3

    .line 741
    :cond_2
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eqz v0, :cond_5

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    if-nez v0, :cond_5

    .line 742
    const/16 v0, 0x14

    invoke-direct {p0, v0, v3, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    goto :goto_3

    .line 737
    :cond_3
    :goto_1
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-eqz v0, :cond_4

    const-string v0, "reverse"

    goto :goto_2

    :cond_4
    const-string v0, "comma data timeout"

    :goto_2
    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    .line 745
    :cond_5
    :goto_3
    return-void
.end method

.method private beginRestoreFade()V
    .locals 2

    .line 793
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBlinkRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 794
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_4

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez v0, :cond_4

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-eqz v0, :cond_0

    goto :goto_2

    .line 798
    :cond_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientBrightness()I

    move-result v0

    .line 799
    iget-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningAnimationStarted:Z

    if-eqz v1, :cond_3

    iget-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLowLightWarning:Z

    if-nez v1, :cond_3

    const/16 v1, 0x8

    if-ge v0, v1, :cond_1

    goto :goto_1

    .line 807
    :cond_1
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningColorRed:Z

    if-eqz v0, :cond_2

    const/4 v0, 0x3

    goto :goto_0

    :cond_2
    const/4 v0, 0x4

    :goto_0
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadePhase:I

    .line 808
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBlinkRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 809
    return-void

    .line 801
    :cond_3
    :goto_1
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 802
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_RESTORE:[B

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    .line 803
    const/4 v0, 0x1

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->syncAmbientBrightness(Z)V

    .line 804
    return-void

    .line 795
    :cond_4
    :goto_2
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 796
    return-void
.end method

.method private static buildBrightnessPacket(ZI)[B
    .locals 1

    .line 1195
    const/16 v0, 0x28

    invoke-static {p0, p1, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildBrightnessPacket(ZII)[B

    move-result-object p0

    return-object p0
.end method

.method private static buildBrightnessPacket(ZII)[B
    .locals 2

    .line 1199
    const/16 v0, 0x64

    const/4 v1, 0x0

    if-eqz p0, :cond_0

    invoke-static {p1, v1, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    goto :goto_0

    :cond_0
    const/4 p1, 0x0

    .line 1200
    :goto_0
    if-eqz p0, :cond_1

    invoke-static {p2, v1, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p2

    goto :goto_1

    :cond_1
    const/4 p2, 0x0

    .line 1201
    :goto_1
    if-eqz p0, :cond_2

    const/16 p0, 0x48

    goto :goto_2

    :cond_2
    const/4 p0, 0x0

    .line 1202
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

    .line 1206
    array-length v0, p1

    .line 1207
    add-int/lit8 v1, v0, 0x4

    new-array v2, v1, [B

    .line 1208
    const/16 v3, 0x2e

    const/4 v4, 0x0

    aput-byte v3, v2, v4

    .line 1209
    int-to-byte v3, p0

    const/4 v5, 0x1

    aput-byte v3, v2, v5

    .line 1210
    const/4 v3, 0x2

    int-to-byte v6, v0

    aput-byte v6, v2, v3

    .line 1211
    add-int/2addr p0, v0

    .line 1212
    nop

    :goto_0
    if-ge v4, v0, :cond_0

    .line 1213
    aget v3, p1, v4

    and-int/lit16 v3, v3, 0xff

    .line 1214
    add-int/lit8 v6, v4, 0x3

    int-to-byte v7, v3

    aput-byte v7, v2, v6

    .line 1215
    add-int/2addr p0, v3

    .line 1212
    add-int/lit8 v4, v4, 0x1

    goto :goto_0

    .line 1217
    :cond_0
    sub-int/2addr v1, v5

    not-int p0, p0

    and-int/lit16 p0, p0, 0xff

    int-to-byte p0, p0

    aput-byte p0, v2, v1

    .line 1218
    return-object v2
.end method

.method private static bytesToHex([B)Ljava/lang/String;
    .locals 7

    .line 1298
    new-instance v0, Ljava/lang/StringBuilder;

    array-length v1, p0

    mul-int/lit8 v1, v1, 0x2

    invoke-direct {v0, v1}, Ljava/lang/StringBuilder;-><init>(I)V

    .line 1299
    array-length v1, p0

    const/4 v2, 0x0

    const/4 v3, 0x0

    :goto_0
    if-ge v3, v1, :cond_0

    aget-byte v4, p0, v3

    .line 1300
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

    .line 1299
    add-int/lit8 v3, v3, 0x1

    goto :goto_0

    .line 1302
    :cond_0
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method private cancelOffroadTimers()V
    .locals 2

    .line 748
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 749
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 750
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 751
    return-void
.end method

.method private static clamp(III)I
    .locals 0

    .line 1222
    invoke-static {p2, p0}, Ljava/lang/Math;->min(II)I

    move-result p0

    invoke-static {p1, p0}, Ljava/lang/Math;->max(II)I

    move-result p0

    return p0
.end method

.method private closeGatt()V
    .locals 2

    .line 1045
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    .line 1046
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnectTimeoutRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1047
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    if-eqz v0, :cond_0

    .line 1049
    :try_start_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    invoke-virtual {v0}, Landroid/bluetooth/BluetoothGatt;->close()V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 1051
    goto :goto_0

    .line 1050
    :catch_0
    move-exception v0

    .line 1052
    :goto_0
    const/4 v0, 0x0

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    .line 1054
    :cond_0
    return-void
.end method

.method private coalescePendingBrightnessPackets()V
    .locals 3

    .line 1166
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->isEmpty()Z

    move-result v0

    if-eqz v0, :cond_0

    .line 1167
    return-void

    .line 1169
    :cond_0
    new-instance v0, Ljava/util/ArrayDeque;

    invoke-direct {v0}, Ljava/util/ArrayDeque;-><init>()V

    .line 1170
    :goto_0
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1}, Ljava/util/ArrayDeque;->isEmpty()Z

    move-result v1

    if-nez v1, :cond_2

    .line 1171
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1}, Ljava/util/ArrayDeque;->poll()Ljava/lang/Object;

    move-result-object v1

    check-cast v1, [B

    .line 1172
    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isBrightnessPacket([B)Z

    move-result v2

    if-nez v2, :cond_1

    .line 1173
    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1175
    :cond_1
    goto :goto_0

    .line 1176
    :cond_2
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1, v0}, Ljava/util/ArrayDeque;->addAll(Ljava/util/Collection;)Z

    .line 1177
    return-void
.end method

.method private static configureWriteCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)V
    .locals 1

    .line 1226
    invoke-virtual {p0}, Landroid/bluetooth/BluetoothGattCharacteristic;->getProperties()I

    move-result v0

    .line 1227
    and-int/lit8 v0, v0, 0x4

    if-eqz v0, :cond_0

    .line 1228
    const/4 v0, 0x1

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGattCharacteristic;->setWriteType(I)V

    goto :goto_0

    .line 1230
    :cond_0
    const/4 v0, 0x2

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGattCharacteristic;->setWriteType(I)V

    .line 1232
    :goto_0
    return-void
.end method

.method private connectBondedCandidate()Z
    .locals 4

    .line 1003
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    invoke-virtual {v0}, Landroid/bluetooth/BluetoothAdapter;->getBondedDevices()Ljava/util/Set;

    move-result-object v0

    .line 1004
    const/4 v1, 0x0

    if-nez v0, :cond_0

    .line 1005
    return v1

    .line 1007
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

    .line 1008
    if-eqz v2, :cond_1

    const/4 v3, 0x0

    invoke-static {v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->matchesAmbientDevice(Landroid/bluetooth/BluetoothDevice;[B)Z

    move-result v3

    if-eqz v3, :cond_1

    .line 1009
    invoke-direct {p0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectDevice(Landroid/bluetooth/BluetoothDevice;)V

    .line 1010
    const/4 v0, 0x1

    return v0

    .line 1012
    :cond_1
    goto :goto_0

    .line 1013
    :cond_2
    return v1
.end method

.method private connectDevice(Landroid/bluetooth/BluetoothDevice;)V
    .locals 4

    .line 1017
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->closeGatt()V

    .line 1018
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    .line 1019
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectScheduled:Z

    .line 1020
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectRunnable:Ljava/lang/Runnable;

    invoke-virtual {v1, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1021
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    .line 1022
    invoke-virtual {v1}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v1

    invoke-virtual {p1}, Landroid/bluetooth/BluetoothDevice;->getAddress()Ljava/lang/String;

    move-result-object v2

    .line 1021
    const-string v3, "navdy_ambient_device_address"

    invoke-static {v1, v3, v2}, Landroid/provider/Settings$System;->putString(Landroid/content/ContentResolver;Ljava/lang/String;Ljava/lang/String;)Z

    .line 1023
    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "ambient connect "

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    const-string v2, " "

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {p1}, Landroid/bluetooth/BluetoothDevice;->getAddress()Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    const-string v2, "NavdyAmbient"

    invoke-static {v2, v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 1024
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;

    invoke-virtual {p1, v1, v0, v2}, Landroid/bluetooth/BluetoothDevice;->connectGatt(Landroid/content/Context;ZLandroid/bluetooth/BluetoothGattCallback;)Landroid/bluetooth/BluetoothGatt;

    move-result-object p1

    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    .line 1025
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    if-nez p1, :cond_0

    .line 1026
    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    .line 1027
    const-wide/16 v0, 0x1388

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    goto :goto_0

    .line 1029
    :cond_0
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnectTimeoutRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1030
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnectTimeoutRunnable:Ljava/lang/Runnable;

    const-wide/16 v1, 0x2710

    invoke-virtual {p1, v0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 1032
    :goto_0
    return-void
.end method

.method private connectIfNeeded()V
    .locals 5

    .line 943
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    if-nez v0, :cond_7

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    if-nez v0, :cond_7

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    if-nez v0, :cond_7

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectScheduled:Z

    if-eqz v0, :cond_0

    goto/16 :goto_2

    .line 946
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    if-nez v0, :cond_1

    .line 947
    invoke-static {}, Landroid/bluetooth/BluetoothAdapter;->getDefaultAdapter()Landroid/bluetooth/BluetoothAdapter;

    move-result-object v0

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    .line 949
    :cond_1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    const-wide/16 v1, 0x1388

    const-string v3, "NavdyAmbient"

    if-eqz v0, :cond_6

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    invoke-virtual {v0}, Landroid/bluetooth/BluetoothAdapter;->isEnabled()Z

    move-result v0

    if-nez v0, :cond_2

    goto :goto_1

    .line 954
    :cond_2
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSkipRememberedOnce:Z

    if-nez v0, :cond_3

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectRememberedCandidate()Z

    move-result v0

    if-eqz v0, :cond_3

    .line 955
    return-void

    .line 957
    :cond_3
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSkipRememberedOnce:Z

    .line 958
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectBondedCandidate()Z

    move-result v0

    if-eqz v0, :cond_4

    .line 959
    return-void

    .line 961
    :cond_4
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSeenScanDevices:Ljava/util/Set;

    invoke-interface {v0}, Ljava/util/Set;->clear()V

    .line 962
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanCallback:Landroid/bluetooth/BluetoothAdapter$LeScanCallback;

    invoke-virtual {v0, v4}, Landroid/bluetooth/BluetoothAdapter;->startLeScan(Landroid/bluetooth/BluetoothAdapter$LeScanCallback;)Z

    move-result v0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    .line 963
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v4, "ambient scan start="

    invoke-virtual {v0, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    iget-boolean v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    invoke-virtual {v0, v4}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    invoke-static {v3, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 964
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    if-eqz v0, :cond_5

    .line 965
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStopScanRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 966
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStopScanRunnable:Ljava/lang/Runnable;

    const-wide/16 v2, 0x2710

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    goto :goto_0

    .line 968
    :cond_5
    invoke-direct {p0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    .line 970
    :goto_0
    return-void

    .line 950
    :cond_6
    :goto_1
    const-string v0, "bluetooth disabled"

    invoke-static {v3, v0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 951
    invoke-direct {p0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    .line 952
    return-void

    .line 944
    :cond_7
    :goto_2
    return-void
.end method

.method private connectRememberedCandidate()Z
    .locals 4

    .line 987
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    .line 988
    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v0

    .line 987
    const-string v1, "navdy_ambient_device_address"

    invoke-static {v0, v1}, Landroid/provider/Settings$System;->getString(Landroid/content/ContentResolver;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    .line 989
    const/4 v1, 0x0

    if-eqz v0, :cond_1

    invoke-static {v0}, Landroid/bluetooth/BluetoothAdapter;->checkBluetoothAddress(Ljava/lang/String;)Z

    move-result v2

    if-nez v2, :cond_0

    goto :goto_0

    .line 993
    :cond_0
    :try_start_0
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    invoke-virtual {v2, v0}, Landroid/bluetooth/BluetoothAdapter;->getRemoteDevice(Ljava/lang/String;)Landroid/bluetooth/BluetoothDevice;

    move-result-object v0

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectDevice(Landroid/bluetooth/BluetoothDevice;)V

    .line 994
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSkipRememberedOnce:Z
    :try_end_0
    .catch Ljava/lang/IllegalArgumentException; {:try_start_0 .. :try_end_0} :catch_0

    .line 995
    return v0

    .line 996
    :catch_0
    move-exception v0

    .line 997
    const-string v2, "NavdyAmbient"

    const-string v3, "bad remembered ambient address"

    invoke-static {v2, v3, v0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 998
    return v1

    .line 990
    :cond_1
    :goto_0
    return v1
.end method

.method private static enableNotifications(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z
    .locals 5

    .line 1235
    const/4 v0, 0x0

    if-eqz p0, :cond_4

    if-nez p1, :cond_0

    goto :goto_2

    .line 1238
    :cond_0
    const/4 v1, 0x1

    invoke-virtual {p0, p1, v1}, Landroid/bluetooth/BluetoothGatt;->setCharacteristicNotification(Landroid/bluetooth/BluetoothGattCharacteristic;Z)Z

    move-result v2

    .line 1239
    sget-object v3, Lcom/navdy/hud/app/ambient/AmbientLightController;->CLIENT_CONFIG_UUID:Ljava/util/UUID;

    invoke-virtual {p1, v3}, Landroid/bluetooth/BluetoothGattCharacteristic;->getDescriptor(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattDescriptor;

    move-result-object p1

    .line 1240
    const-string v3, "NavdyAmbient"

    if-eqz v2, :cond_2

    if-nez p1, :cond_1

    goto :goto_0

    .line 1244
    :cond_1
    sget-object v0, Landroid/bluetooth/BluetoothGattDescriptor;->ENABLE_NOTIFICATION_VALUE:[B

    invoke-virtual {p1, v0}, Landroid/bluetooth/BluetoothGattDescriptor;->setValue([B)Z

    .line 1245
    invoke-virtual {p0, p1}, Landroid/bluetooth/BluetoothGatt;->writeDescriptor(Landroid/bluetooth/BluetoothGattDescriptor;)Z

    move-result p0

    .line 1246
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

    .line 1247
    return p0

    .line 1241
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

    .line 1242
    return v0

    .line 1236
    :cond_4
    :goto_2
    return v0
.end method

.method private static findNotifyCharacteristic(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 1

    .line 1262
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->SERVICE_UUID:Ljava/util/UUID;

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;

    move-result-object v0

    .line 1263
    if-nez v0, :cond_0

    .line 1264
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->LEGACY_SERVICE_UUID:Ljava/util/UUID;

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;

    move-result-object v0

    .line 1266
    :cond_0
    if-nez v0, :cond_1

    .line 1267
    const/4 p0, 0x0

    return-object p0

    .line 1269
    :cond_1
    sget-object p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->NOTIFY_UUID:Ljava/util/UUID;

    invoke-virtual {v0, p0}, Landroid/bluetooth/BluetoothGattService;->getCharacteristic(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p0

    return-object p0
.end method

.method private static findWriteCharacteristic(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 1

    .line 1251
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->SERVICE_UUID:Ljava/util/UUID;

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;

    move-result-object v0

    .line 1252
    if-nez v0, :cond_0

    .line 1253
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->LEGACY_SERVICE_UUID:Ljava/util/UUID;

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;

    move-result-object v0

    .line 1255
    :cond_0
    if-nez v0, :cond_1

    .line 1256
    const/4 p0, 0x0

    return-object p0

    .line 1258
    :cond_1
    sget-object p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->WRITE_UUID:Ljava/util/UUID;

    invoke-virtual {v0, p0}, Landroid/bluetooth/BluetoothGattService;->getCharacteristic(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p0

    return-object p0
.end method

.method private finishRestoreFade(I)V
    .locals 2

    .line 812
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBlinkRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 813
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningAnimationStarted:Z

    .line 814
    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLowLightWarning:Z

    .line 815
    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningColorRed:Z

    .line 816
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadePhase:I

    .line 817
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadeStep:I

    .line 818
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 819
    return-void
.end method

.method private flushNext()V
    .locals 6

    .line 911
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

    .line 914
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->poll()Ljava/lang/Object;

    move-result-object v0

    check-cast v0, [B

    .line 915
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v1, v0}, Landroid/bluetooth/BluetoothGattCharacteristic;->setValue([B)Z

    .line 916
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->configureWriteCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)V

    .line 917
    const/4 v1, 0x1

    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    .line 918
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    invoke-virtual {v2, v3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 919
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    invoke-virtual {v2, v3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 920
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    const-wide/16 v4, 0x4b0

    invoke-virtual {v2, v3, v4, v5}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 921
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getWriteType()I

    move-result v2

    if-ne v2, v1, :cond_1

    .line 922
    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->usesPacedWrite([B)Z

    move-result v1

    if-eqz v1, :cond_1

    .line 923
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    const-wide/16 v3, 0x78

    invoke-virtual {v1, v2, v3, v4}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 925
    :cond_1
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v1, v2}, Landroid/bluetooth/BluetoothGatt;->writeCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result v1

    .line 926
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

    .line 927
    if-nez v1, :cond_2

    .line 928
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    invoke-virtual {v1, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 929
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    invoke-virtual {v1, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 930
    const/4 v1, 0x0

    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    .line 931
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v2, v0}, Ljava/util/ArrayDeque;->offerFirst(Ljava/lang/Object;)Z

    .line 932
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    .line 933
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyReady:Z

    .line 934
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStartQueued:Z

    .line 935
    const/4 v0, 0x0

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 936
    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 937
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->closeGatt()V

    .line 938
    const-wide/16 v0, 0x1388

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    .line 940
    :cond_2
    return-void

    .line 912
    :cond_3
    :goto_0
    return-void
.end method

.method public static declared-synchronized get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;
    .locals 2

    const-class v0, Lcom/navdy/hud/app/ambient/AmbientLightController;

    monitor-enter v0

    .line 503
    :try_start_0
    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->sInstance:Lcom/navdy/hud/app/ambient/AmbientLightController;

    if-nez v1, :cond_0

    .line 504
    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {v1, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;-><init>(Landroid/content/Context;)V

    sput-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->sInstance:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 506
    :cond_0
    sget-object p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->sInstance:Lcom/navdy/hud/app/ambient/AmbientLightController;
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    monitor-exit v0

    return-object p0

    .line 502
    :catchall_0
    move-exception p0

    :try_start_1
    monitor-exit v0
    :try_end_1
    .catchall {:try_start_1 .. :try_end_1} :catchall_0

    throw p0
.end method

.method private hardAmbientOff(Ljava/lang/String;)V
    .locals 2

    .line 884
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "ambient off reason="

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    const-string v0, "NavdyAmbient"

    invoke-static {v0, p1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 885
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 886
    const/4 p1, 0x0

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    .line 887
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2:I

    .line 888
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    .line 889
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    .line 890
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 891
    sget-object p1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_OFF:[B

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    .line 892
    return-void
.end method

.method private static isBrightnessPacket([B)Z
    .locals 4

    .line 1189
    const/4 v0, 0x0

    if-eqz p0, :cond_0

    array-length v1, p0

    const/16 v2, 0x8

    if-ne v1, v2, :cond_0

    aget-byte v1, p0, v0

    const/16 v2, 0x2e

    if-ne v1, v2, :cond_0

    const/4 v1, 0x1

    aget-byte v2, p0, v1

    const/16 v3, -0x73

    if-ne v2, v3, :cond_0

    const/4 v2, 0x2

    aget-byte v2, p0, v2

    const/4 v3, 0x4

    if-ne v2, v3, :cond_0

    aget-byte p0, p0, v3

    const/16 v2, 0x48

    if-ne p0, v2, :cond_0

    const/4 v0, 0x1

    :cond_0
    return v0
.end method

.method private static isDriveGear(Ljava/lang/String;)Z
    .locals 1

    .line 1336
    const-string v0, "p"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "park"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    .line 1337
    const-string v0, "n"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "neutral"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    .line 1338
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

    .line 1336
    :goto_1
    return p0
.end method

.method private static isReverse(Ljava/lang/String;)Z
    .locals 1

    .line 1332
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

.method private static isStartPacket([B)Z
    .locals 4

    .line 1180
    const/4 v0, 0x0

    if-eqz p0, :cond_0

    array-length v1, p0

    const/4 v2, 0x1

    if-le v1, v2, :cond_0

    aget-byte v1, p0, v0

    const/16 v3, 0x2e

    if-ne v1, v3, :cond_0

    aget-byte p0, p0, v2

    const/16 v1, -0x7f

    if-ne p0, v1, :cond_0

    const/4 v0, 0x1

    :cond_0
    return v0
.end method

.method private logSeenScanDevice(Landroid/bluetooth/BluetoothDevice;I)V
    .locals 3

    .line 1057
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;

    move-result-object v0

    .line 1058
    invoke-virtual {v0}, Ljava/lang/String;->length()I

    move-result v1

    if-nez v1, :cond_0

    .line 1059
    return-void

    .line 1061
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

    .line 1062
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSeenScanDevices:Ljava/util/Set;

    invoke-interface {v2, v1}, Ljava/util/Set;->add(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_1

    .line 1063
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

    .line 1065
    :cond_1
    return-void
.end method

.method private static matchesAmbientDevice(Landroid/bluetooth/BluetoothDevice;[B)Z
    .locals 2

    .line 1273
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;

    move-result-object p0

    sget-object v0, Ljava/util/Locale;->US:Ljava/util/Locale;

    invoke-virtual {p0, v0}, Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)Ljava/lang/String;

    move-result-object p0

    .line 1274
    const-string v0, "rz-slave"

    invoke-virtual {p0, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    const/4 v1, 0x0

    if-nez v0, :cond_3

    const-string v0, "rz_slave"

    invoke-virtual {p0, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-nez v0, :cond_3

    const-string v0, "rz slave"

    invoke-virtual {p0, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-nez v0, :cond_3

    .line 1275
    const-string v0, "slave"

    invoke-virtual {p0, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-eqz v0, :cond_0

    goto :goto_0

    .line 1278
    :cond_0
    const-string v0, "lamp"

    invoke-virtual {p0, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "frgn"

    invoke-virtual {p0, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "ambient"

    invoke-virtual {p0, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-nez v0, :cond_1

    .line 1279
    const-string v0, "carled"

    invoke-virtual {p0, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "pocket"

    invoke-virtual {p0, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result p0

    if-nez p0, :cond_1

    .line 1280
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scanRecordContainsAmbientUuid([B)Z

    move-result p0

    if-eqz p0, :cond_2

    :cond_1
    const/4 v1, 0x1

    .line 1278
    :cond_2
    return v1

    .line 1276
    :cond_3
    :goto_0
    return v1
.end method

.method private needsConnection()Z
    .locals 1

    .line 1068
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

    .line 1315
    invoke-virtual {p0}, Ljava/lang/String;->trim()Ljava/lang/String;

    move-result-object p0

    sget-object v0, Ljava/util/Locale;->US:Ljava/util/Locale;

    invoke-virtual {p0, v0}, Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)Ljava/lang/String;

    move-result-object p0

    .line 1316
    const-string v0, ".reverse"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 1317
    const-string p0, "reverse"

    return-object p0

    .line 1319
    :cond_0
    const-string v0, ".park"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_1

    .line 1320
    const-string p0, "park"

    return-object p0

    .line 1322
    :cond_1
    const-string v0, ".neutral"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_2

    .line 1323
    const-string p0, "neutral"

    return-object p0

    .line 1325
    :cond_2
    const-string v0, ".drive"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_3

    .line 1326
    const-string p0, "drive"

    return-object p0

    .line 1328
    :cond_3
    return-object p0
.end method

.method private noteVehicleDataReceived()V
    .locals 4

    .line 651
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    iput-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastVehicleDataAtMs:J

    .line 652
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    .line 653
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataWatchdogRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 654
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataWatchdogRunnable:Ljava/lang/Runnable;

    const-wide/16 v2, 0xbb8

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 655
    return-void
.end method

.method public static onCameraSpeedChanged(Landroid/content/Context;II)V
    .locals 2

    .line 575
    if-nez p0, :cond_0

    .line 576
    return-void

    .line 578
    :cond_0
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;

    move-result-object p0

    .line 579
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientLightController$20;

    invoke-direct {v1, p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController$20;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;II)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 585
    return-void
.end method

.method public static onGearText(Landroid/content/Context;Ljava/lang/String;)V
    .locals 2

    .line 549
    if-eqz p0, :cond_1

    if-nez p1, :cond_0

    goto :goto_0

    .line 552
    :cond_0
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;

    move-result-object p0

    .line 553
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientLightController$18;

    invoke-direct {v1, p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController$18;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 559
    return-void

    .line 550
    :cond_1
    :goto_0
    return-void
.end method

.method public static onOpenpilotPayload(Landroid/content/Context;Ljava/lang/String;)V
    .locals 11

    .line 510
    const-string v0, "doorOpen"

    const-string v1, "onroad"

    if-eqz p0, :cond_1

    if-nez p1, :cond_0

    goto :goto_1

    .line 514
    :cond_0
    :try_start_0
    new-instance v2, Lorg/json/JSONObject;

    invoke-direct {v2, p1}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    .line 515
    const-string p1, "gear"

    const-string v3, "gearShifter"

    const-string v4, ""

    invoke-virtual {v2, v3, v4}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v3

    invoke-virtual {v2, p1, v3}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v6

    .line 516
    invoke-virtual {v2, v1}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result v7

    .line 517
    invoke-virtual {v2, v0}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result v8

    .line 518
    const/4 p1, 0x1

    invoke-virtual {v2, v1, p1}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v9

    .line 519
    const/4 p1, 0x0

    invoke-virtual {v2, v0, p1}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v10

    .line 520
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;

    move-result-object v5

    .line 521
    iget-object p0, v5, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    new-instance v4, Lcom/navdy/hud/app/ambient/AmbientLightController$17;

    invoke-direct/range {v4 .. v10}, Lcom/navdy/hud/app/ambient/AmbientLightController$17;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;ZZZZ)V

    invoke-virtual {p0, v4}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 539
    goto :goto_0

    .line 537
    :catch_0
    move-exception v0

    move-object p0, v0

    .line 538
    const-string p1, "NavdyAmbient"

    const-string v0, "bad openpilot payload"

    invoke-static {p1, v0, p0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 540
    :goto_0
    return-void

    .line 511
    :cond_1
    :goto_1
    return-void
.end method

.method public static onOpenpilotPayload(Landroid/content/Context;Lorg/json/JSONObject;)V
    .locals 0

    .line 543
    if-eqz p1, :cond_0

    .line 544
    invoke-virtual {p1}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-static {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onOpenpilotPayload(Landroid/content/Context;Ljava/lang/String;)V

    .line 546
    :cond_0
    return-void
.end method

.method public static onOverspeedChanged(Landroid/content/Context;Z)V
    .locals 2

    .line 562
    if-nez p0, :cond_0

    .line 563
    return-void

    .line 565
    :cond_0
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;

    move-result-object p0

    .line 566
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientLightController$19;

    invoke-direct {v1, p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController$19;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 572
    return-void
.end method

.method private queueStartPacket()V
    .locals 2

    .line 1072
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStartQueued:Z

    if-eqz v0, :cond_0

    .line 1073
    return-void

    .line 1075
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_START:[B

    invoke-virtual {v1}, [B->clone()Ljava/lang/Object;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offerFirst(Ljava/lang/Object;)Z

    .line 1076
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStartQueued:Z

    .line 1077
    return-void
.end method

.method private readAckSettleIntervalMs()I
    .locals 3

    .line 1160
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v0

    const-string v1, "navdy_ambient_ack_settle_ms"

    const/16 v2, 0xa

    invoke-static {v0, v1, v2}, Landroid/provider/Settings$System;->getInt(Landroid/content/ContentResolver;Ljava/lang/String;I)I

    move-result v0

    const/4 v1, 0x5

    const/16 v2, 0x64

    invoke-static {v0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v0

    return v0
.end method

.method private readAmbientBrightness()I
    .locals 5

    .line 1126
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readScreenBrightness()I

    move-result v0

    .line 1127
    const/4 v1, 0x1

    const/16 v2, 0x10

    if-gt v0, v2, :cond_0

    .line 1128
    return v1

    .line 1130
    :cond_0
    const/16 v3, 0x29

    const/16 v4, 0x8

    if-gt v0, v3, :cond_1

    .line 1131
    nop

    .line 1132
    nop

    .line 1133
    sub-int/2addr v0, v2

    mul-int/lit8 v0, v0, 0x7

    add-int/lit8 v0, v0, 0xc

    div-int/lit8 v0, v0, 0x19

    add-int/2addr v0, v1

    .line 1136
    invoke-static {v0, v1, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v0

    return v0

    .line 1138
    :cond_1
    const/16 v1, 0x64

    const/16 v2, 0x32

    if-gt v0, v1, :cond_2

    .line 1139
    nop

    .line 1140
    nop

    .line 1141
    sub-int/2addr v0, v3

    mul-int/lit8 v0, v0, 0x2a

    add-int/lit8 v0, v0, 0x1d

    div-int/lit8 v0, v0, 0x3b

    add-int/2addr v0, v4

    .line 1144
    invoke-static {v0, v4, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v0

    return v0

    .line 1146
    :cond_2
    return v2
.end method

.method private readAmbientTransitionStepMs()I
    .locals 3

    .line 1154
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v0

    const-string v1, "navdy_ambient_transition_step_ms"

    const/16 v2, 0x21

    invoke-static {v0, v1, v2}, Landroid/provider/Settings$System;->getInt(Landroid/content/ContentResolver;Ljava/lang/String;I)I

    move-result v0

    const/16 v1, 0xfa

    invoke-static {v0, v2, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v0

    return v0
.end method

.method private readScreenBrightness()I
    .locals 3

    .line 1150
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

.method private removePendingAmbientStatePackets()V
    .locals 4

    .line 1102
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->isEmpty()Z

    move-result v0

    if-eqz v0, :cond_0

    .line 1103
    return-void

    .line 1105
    :cond_0
    new-instance v0, Ljava/util/ArrayDeque;

    invoke-direct {v0}, Ljava/util/ArrayDeque;-><init>()V

    .line 1106
    :goto_0
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1}, Ljava/util/ArrayDeque;->isEmpty()Z

    move-result v1

    if-nez v1, :cond_3

    .line 1107
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1}, Ljava/util/ArrayDeque;->poll()Ljava/lang/Object;

    move-result-object v1

    check-cast v1, [B

    .line 1108
    if-eqz v1, :cond_2

    array-length v2, v1

    const/4 v3, 0x2

    if-lt v2, v3, :cond_1

    const/4 v2, 0x1

    aget-byte v2, v1, v2

    const/16 v3, -0x73

    if-eq v2, v3, :cond_2

    .line 1109
    :cond_1
    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1111
    :cond_2
    goto :goto_0

    .line 1112
    :cond_3
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1, v0}, Ljava/util/ArrayDeque;->addAll(Ljava/util/Collection;)Z

    .line 1113
    return-void
.end method

.method private requestCameraSpeed(II)V
    .locals 0

    .line 588
    if-lez p2, :cond_2

    if-gt p1, p2, :cond_0

    goto :goto_0

    .line 590
    :cond_0
    add-int/lit8 p2, p2, 0x2

    if-lt p1, p2, :cond_1

    .line 591
    const/4 p1, 0x1

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestOverspeed(Z)V

    goto :goto_1

    .line 594
    :cond_1
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestOverspeed(Z)V

    goto :goto_1

    .line 589
    :cond_2
    :goto_0
    const/4 p1, 0x0

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestOverspeed(Z)V

    .line 596
    :goto_1
    return-void
.end method

.method private requestOverspeed(Z)V
    .locals 8

    .line 599
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    if-eqz v0, :cond_0

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-nez v0, :cond_0

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_0

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-eqz v0, :cond_1

    .line 600
    :cond_0
    const/4 p1, 0x0

    .line 602
    :cond_1
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mRequestedOverspeed:Z

    if-ne v0, p1, :cond_2

    .line 603
    return-void

    .line 605
    :cond_2
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mRequestedOverspeed:Z

    .line 606
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedStateRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 607
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-ne v0, p1, :cond_3

    .line 608
    return-void

    .line 611
    :cond_3
    if-eqz p1, :cond_4

    const-wide/16 v0, 0x3e8

    goto :goto_0

    :cond_4
    const-wide/16 v0, 0x7d0

    .line 612
    :goto_0
    const-wide/16 v2, 0x0

    if-nez p1, :cond_5

    iget-wide v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActivatedAtMs:J

    cmp-long v6, v4, v2

    if-lez v6, :cond_5

    .line 613
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v4

    iget-wide v6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActivatedAtMs:J

    sub-long/2addr v4, v6

    .line 614
    const-wide/16 v6, 0xbb8

    sub-long/2addr v6, v4

    invoke-static {v0, v1, v6, v7}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v0

    .line 616
    :cond_5
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

    .line 617
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedStateRunnable:Ljava/lang/Runnable;

    invoke-static {v2, v3, v0, v1}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v0

    invoke-virtual {p1, v4, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 618
    return-void
.end method

.method private restoreActiveStateAfterConnect()V
    .locals 4

    .line 1080
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->removePendingAmbientStatePackets()V

    .line 1081
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-eqz v0, :cond_0

    .line 1082
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_OFF:[B

    invoke-virtual {v1}, [B->clone()Ljava/lang/Object;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1083
    return-void

    .line 1085
    :cond_0
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-eqz v0, :cond_1

    .line 1086
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBlink()V

    .line 1087
    return-void

    .line 1089
    :cond_1
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    if-eqz v0, :cond_3

    .line 1090
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_RESTORE:[B

    invoke-virtual {v1}, [B->clone()Ljava/lang/Object;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1091
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_2

    .line 1092
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    goto :goto_0

    .line 1094
    :cond_2
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    const/4 v3, 0x1

    invoke-static {v3, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildBrightnessPacket(ZII)[B

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1096
    :goto_0
    return-void

    .line 1098
    :cond_3
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_OFF:[B

    invoke-virtual {v1}, [B->clone()Ljava/lang/Object;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1099
    return-void
.end method

.method private static safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;
    .locals 1

    .line 1307
    const-string v0, ""

    :try_start_0
    invoke-virtual {p0}, Landroid/bluetooth/BluetoothDevice;->getName()Ljava/lang/String;

    move-result-object p0
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 1308
    if-nez p0, :cond_0

    goto :goto_0

    :cond_0
    move-object v0, p0

    :goto_0
    return-object v0

    .line 1309
    :catch_0
    move-exception p0

    .line 1310
    return-object v0
.end method

.method private static scanRecordContainsAmbientUuid([B)Z
    .locals 5

    .line 1284
    const/4 v0, 0x0

    if-nez p0, :cond_0

    .line 1285
    return v0

    .line 1287
    :cond_0
    const/4 v1, 0x0

    :goto_0
    add-int/lit8 v2, v1, 0x1

    array-length v3, p0

    if-ge v2, v3, :cond_4

    .line 1288
    aget-byte v1, p0, v1

    and-int/lit16 v1, v1, 0xff

    .line 1289
    aget-byte v3, p0, v2

    and-int/lit16 v3, v3, 0xff

    .line 1290
    if-eqz v1, :cond_1

    const/16 v4, 0x30

    if-ne v1, v4, :cond_2

    :cond_1
    const/16 v1, 0xae

    if-eq v3, v1, :cond_3

    const/16 v1, 0xaf

    if-ne v3, v1, :cond_2

    goto :goto_1

    .line 1287
    :cond_2
    move v1, v2

    goto :goto_0

    .line 1291
    :cond_3
    :goto_1
    const/4 p0, 0x1

    return p0

    .line 1294
    :cond_4
    return v0
.end method

.method private scheduleReconnect()V
    .locals 2

    .line 973
    const-wide/16 v0, 0x1388

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    .line 974
    return-void
.end method

.method private scheduleReconnect(J)V
    .locals 4

    .line 977
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->needsConnection()Z

    move-result v0

    if-eqz v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    if-nez v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    if-nez v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    if-eqz v0, :cond_0

    goto :goto_0

    .line 980
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 981
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectScheduled:Z

    .line 982
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "ambient reconnect scheduled delayMs="

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p1, p2}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    const-string v1, "NavdyAmbient"

    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 983
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectRunnable:Ljava/lang/Runnable;

    const-wide/16 v2, 0x0

    invoke-static {v2, v3, p1, p2}, Ljava/lang/Math;->max(JJ)J

    move-result-wide p1

    invoke-virtual {v0, v1, p1, p2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 984
    return-void

    .line 978
    :cond_1
    :goto_0
    return-void
.end method

.method private sendPacket([B)V
    .locals 2

    .line 899
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isBrightnessPacket([B)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 900
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->coalescePendingBrightnessPackets()V

    .line 902
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->size()I

    move-result v0

    const/16 v1, 0x14

    if-le v0, v1, :cond_1

    .line 903
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->poll()Ljava/lang/Object;

    .line 905
    :cond_1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {p1}, [B->clone()Ljava/lang/Object;

    move-result-object p1

    invoke-virtual {v0, p1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 906
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectIfNeeded()V

    .line 907
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->flushNext()V

    .line 908
    return-void
.end method

.method private setGearText(Ljava/lang/String;)V
    .locals 2

    .line 621
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalizeGear(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    .line 622
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastGear:Ljava/lang/String;

    invoke-virtual {p1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 623
    return-void

    .line 625
    :cond_0
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastGear:Ljava/lang/String;

    .line 626
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

    .line 628
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isReverse(Ljava/lang/String;)Z

    move-result v0

    const/4 v1, 0x1

    if-eqz v0, :cond_1

    .line 629
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    .line 630
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 631
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBrightnessSync()V

    .line 632
    const-string p1, "reverse"

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    .line 633
    return-void

    .line 636
    :cond_1
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isDriveGear(Ljava/lang/String;)Z

    move-result p1

    if-eqz p1, :cond_3

    .line 637
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    .line 638
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    .line 639
    if-eqz p1, :cond_2

    .line 640
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->applyVehicleStateTargets()V

    goto :goto_0

    .line 641
    :cond_2
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    if-nez p1, :cond_3

    .line 642
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    .line 643
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 644
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    .line 645
    sget-object p1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_RESTORE:[B

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    .line 648
    :cond_3
    :goto_0
    return-void
.end method

.method private setOverspeed(Z)V
    .locals 2

    .line 754
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-ne v0, p1, :cond_0

    .line 755
    return-void

    .line 757
    :cond_0
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    .line 758
    if-eqz p1, :cond_1

    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    goto :goto_0

    :cond_1
    const-wide/16 v0, 0x0

    :goto_0
    iput-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActivatedAtMs:J

    .line 759
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

    .line 760
    if-eqz p1, :cond_2

    .line 761
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz p1, :cond_4

    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez p1, :cond_4

    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-nez p1, :cond_4

    .line 762
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBlink()V

    goto :goto_1

    .line 765
    :cond_2
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez p1, :cond_3

    .line 766
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->beginRestoreFade()V

    goto :goto_1

    .line 768
    :cond_3
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 771
    :cond_4
    :goto_1
    return-void
.end method

.method private setVehicleState(ZZ)V
    .locals 7

    .line 658
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    .line 659
    const/4 v1, 0x1

    const/4 v2, 0x0

    if-eqz v0, :cond_1

    iget-boolean v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eq v3, p1, :cond_0

    goto :goto_0

    :cond_0
    const/4 v3, 0x0

    goto :goto_1

    :cond_1
    :goto_0
    const/4 v3, 0x1

    .line 660
    :goto_1
    if-eqz v0, :cond_3

    iget-boolean v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eq v4, p2, :cond_2

    goto :goto_2

    :cond_2
    const/4 v4, 0x0

    goto :goto_3

    :cond_3
    :goto_2
    const/4 v4, 0x1

    .line 661
    :goto_3
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    .line 662
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    .line 663
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    .line 664
    iput-boolean p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    .line 665
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->updateCpuWakeLock()V

    .line 666
    if-nez v3, :cond_4

    if-eqz v4, :cond_5

    .line 667
    :cond_4
    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v5, "vehicle state onroad="

    invoke-virtual {v1, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1, p1}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v1

    const-string v5, " doorOpen="

    invoke-virtual {v1, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1, p2}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    const-string v5, "NavdyAmbient"

    invoke-static {v5, v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 670
    :cond_5
    if-eqz p1, :cond_8

    .line 671
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->cancelOffroadTimers()V

    .line 672
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    .line 673
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    .line 674
    if-nez v3, :cond_6

    if-eqz v4, :cond_7

    .line 675
    :cond_6
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->applyVehicleStateTargets()V

    .line 677
    :cond_7
    return-void

    .line 680
    :cond_8
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBrightnessSync()V

    .line 681
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mRequestedOverspeed:Z

    .line 682
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedStateRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 683
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-eqz p1, :cond_9

    .line 684
    invoke-direct {p0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setOverspeed(Z)V

    .line 687
    :cond_9
    const-wide/16 v5, 0x3e8

    const/16 p1, 0x64

    if-eqz p2, :cond_e

    .line 688
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-virtual {p2, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 689
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-virtual {p2, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 690
    if-nez v4, :cond_a

    if-eqz v3, :cond_b

    .line 691
    :cond_a
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    .line 692
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxRunnable:Ljava/lang/Runnable;

    invoke-virtual {p2, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 693
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxRunnable:Ljava/lang/Runnable;

    const-wide/32 v1, 0x124f80

    invoke-virtual {p2, v0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 695
    :cond_b
    iget-boolean p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    if-nez p2, :cond_d

    if-nez v4, :cond_c

    if-eqz v3, :cond_d

    .line 696
    :cond_c
    const/16 p2, 0x14

    invoke-direct {p0, p2, p1, v5, v6}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    .line 699
    :cond_d
    return-void

    .line 702
    :cond_e
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxRunnable:Ljava/lang/Runnable;

    invoke-virtual {p2, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 703
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    .line 704
    if-eqz v4, :cond_f

    if-eqz v0, :cond_f

    .line 705
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 706
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 707
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    const-wide/16 v0, 0x4e20

    invoke-virtual {p1, p2, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    goto :goto_4

    .line 708
    :cond_f
    if-eqz v0, :cond_10

    if-eqz v3, :cond_10

    .line 709
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-virtual {p2, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 710
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-virtual {p2, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 711
    iget p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    invoke-direct {p0, p2, p1, v5, v6}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    .line 713
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    const-wide/32 v0, 0x1d4c0

    invoke-virtual {p1, p2, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    goto :goto_4

    .line 714
    :cond_10
    if-nez v0, :cond_11

    .line 715
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 716
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 717
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    const-wide/32 v0, 0xea60

    invoke-virtual {p1, p2, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 719
    :cond_11
    :goto_4
    return-void
.end method

.method private startAmbientFade(IIJ)V
    .locals 2

    .line 854
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 855
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1:I

    .line 856
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2:I

    .line 857
    const/4 v0, 0x0

    const/16 v1, 0x64

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    .line 858
    invoke-static {p2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    .line 859
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide p1

    iput-wide p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartedAtMs:J

    .line 860
    const-wide/16 p1, 0x0

    invoke-static {p1, p2, p3, p4}, Ljava/lang/Math;->max(JJ)J

    move-result-wide p3

    iput-wide p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeDurationMs:J

    .line 861
    iget p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    if-gtz p3, :cond_0

    iget p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    if-lez p3, :cond_1

    .line 862
    :cond_0
    const/4 p3, 0x1

    iput-boolean p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 863
    iget-boolean p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-nez p3, :cond_1

    .line 864
    sget-object p3, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_RESTORE:[B

    invoke-direct {p0, p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    .line 867
    :cond_1
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientTransitionStepMs()I

    move-result p3

    int-to-long p3, p3

    iget-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeDurationMs:J

    invoke-static {p3, p4, v0, v1}, Ljava/lang/Math;->min(JJ)J

    move-result-wide p3

    .line 868
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeRunnable:Ljava/lang/Runnable;

    invoke-static {p1, p2, p3, p4}, Ljava/lang/Math;->max(JJ)J

    move-result-wide p1

    invoke-virtual {v0, v1, p1, p2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 869
    return-void
.end method

.method private startBlink()V
    .locals 2

    .line 774
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-eqz v0, :cond_0

    goto :goto_0

    .line 777
    :cond_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 778
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 779
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    .line 780
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBlinkRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 781
    return-void

    .line 775
    :cond_1
    :goto_0
    return-void
.end method

.method private startBrightnessSync()V
    .locals 4

    .line 822
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 823
    const/4 v0, 0x1

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->syncAmbientBrightness(Z)V

    .line 824
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    const-wide/16 v2, 0x1388

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 825
    return-void
.end method

.method private stopBlink()V
    .locals 2

    .line 784
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBlinkRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 785
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningAnimationStarted:Z

    .line 786
    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLowLightWarning:Z

    .line 787
    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningColorRed:Z

    .line 788
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadePhase:I

    .line 789
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFadeStep:I

    .line 790
    return-void
.end method

.method private stopBrightnessSync()V
    .locals 2

    .line 828
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 829
    const/4 v0, -0x1

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 830
    return-void
.end method

.method private stopScan()V
    .locals 2

    .line 1035
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    if-eqz v0, :cond_1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    if-nez v0, :cond_0

    goto :goto_0

    .line 1038
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanCallback:Landroid/bluetooth/BluetoothAdapter$LeScanCallback;

    invoke-virtual {v0, v1}, Landroid/bluetooth/BluetoothAdapter;->stopLeScan(Landroid/bluetooth/BluetoothAdapter$LeScanCallback;)V

    .line 1039
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    .line 1040
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStopScanRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1041
    const-string v0, "NavdyAmbient"

    const-string v1, "ambient scan stop"

    invoke-static {v0, v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 1042
    return-void

    .line 1036
    :cond_1
    :goto_0
    return-void
.end method

.method private syncAmbientBrightness(Z)V
    .locals 4

    .line 833
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_6

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez v0, :cond_6

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-eqz v0, :cond_0

    goto :goto_1

    .line 836
    :cond_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientBrightness()I

    move-result v0

    .line 837
    iget-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningAnimationStarted:Z

    if-eqz v1, :cond_1

    .line 838
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 839
    return-void

    .line 841
    :cond_1
    if-nez p1, :cond_2

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    if-ltz v1, :cond_2

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    sub-int v1, v0, v1

    .line 842
    invoke-static {v1}, Ljava/lang/Math;->abs(I)I

    move-result v1

    const/4 v2, 0x2

    if-ge v1, v2, :cond_2

    .line 843
    return-void

    .line 845
    :cond_2
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 846
    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "ambient brightness="

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v1

    const-string v2, " screen="

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readScreenBrightness()I

    move-result v2

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    const-string v2, "NavdyAmbient"

    invoke-static {v2, v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 847
    iget-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eqz v1, :cond_3

    const/16 v1, 0x64

    goto :goto_0

    :cond_3
    const/16 v1, 0x28

    .line 848
    :goto_0
    if-nez p1, :cond_4

    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    if-ne v0, p1, :cond_4

    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    if-eq v1, p1, :cond_5

    .line 849
    :cond_4
    const-wide/16 v2, 0x3e8

    invoke-direct {p0, v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    .line 851
    :cond_5
    return-void

    .line 834
    :cond_6
    :goto_1
    return-void
.end method

.method private updateCpuWakeLock()V
    .locals 3

    .line 722
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    if-nez v0, :cond_0

    .line 723
    return-void

    .line 725
    :cond_0
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    if-eqz v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-nez v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-nez v0, :cond_1

    const/4 v0, 0x1

    goto :goto_0

    :cond_1
    const/4 v0, 0x0

    .line 726
    :goto_0
    const-string v1, "NavdyAmbient"

    if-eqz v0, :cond_2

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    invoke-virtual {v2}, Landroid/os/PowerManager$WakeLock;->isHeld()Z

    move-result v2

    if-nez v2, :cond_2

    .line 727
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    invoke-virtual {v0}, Landroid/os/PowerManager$WakeLock;->acquire()V

    .line 728
    const-string v0, "offroad ambient CPU wake lock acquired"

    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    goto :goto_1

    .line 729
    :cond_2
    if-nez v0, :cond_3

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    invoke-virtual {v0}, Landroid/os/PowerManager$WakeLock;->isHeld()Z

    move-result v0

    if-eqz v0, :cond_3

    .line 730
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    invoke-virtual {v0}, Landroid/os/PowerManager$WakeLock;->release()V

    .line 731
    const-string v0, "offroad ambient CPU wake lock released"

    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 733
    :cond_3
    :goto_1
    return-void
.end method

.method private static usesPacedWrite([B)Z
    .locals 1

    .line 1185
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isStartPacket([B)Z

    move-result v0

    if-nez v0, :cond_1

    if-eqz p0, :cond_0

    array-length p0, p0

    const/16 v0, 0xc

    if-ne p0, v0, :cond_0

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

.method private warningZone2Brightness()I
    .locals 1

    .line 895
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eqz v0, :cond_0

    const/16 v0, 0x64

    goto :goto_0

    :cond_0
    const/16 v0, 0x28

    :goto_0
    return v0
.end method

.method private writeAck()V
    .locals 3

    .line 1116
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    if-eqz v0, :cond_1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    if-nez v0, :cond_0

    goto :goto_0

    .line 1119
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_ACK:[B

    invoke-virtual {v0, v1}, Landroid/bluetooth/BluetoothGattCharacteristic;->setValue([B)Z

    .line 1120
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->configureWriteCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)V

    .line 1121
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v0, v1}, Landroid/bluetooth/BluetoothGatt;->writeCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result v0

    .line 1122
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

    .line 1123
    return-void

    .line 1117
    :cond_1
    :goto_0
    return-void
.end method
