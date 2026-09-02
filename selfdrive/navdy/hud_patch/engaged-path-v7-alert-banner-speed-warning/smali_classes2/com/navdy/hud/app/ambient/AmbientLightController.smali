.class public final Lcom/navdy/hud/app/ambient/AmbientLightController;
.super Ljava/lang/Object;
.source "AmbientLightController.java"


# static fields
.field private static final ACK_SETTLE_INTERVAL_SETTING:Ljava/lang/String; = "navdy_ambient_ack_settle_ms"

.field private static final AMBIENT_DEVICE_ADDRESS_SETTING:Ljava/lang/String; = "navdy_ambient_device_address"

.field private static final AMBIENT_NORMAL_FADE_MS:J = 0x3e8L

.field private static final AMBIENT_PROFILE_SETTING:Ljava/lang/String; = "navdy_ambient_profile_json"

.field private static final AMBIENT_TRANSITION_STEP_SETTING:Ljava/lang/String; = "navdy_ambient_transition_step_ms"

.field private static final BRIGHTNESS_SYNC_INTERVAL_MS:J = 0x1388L

.field private static final BRIGHTNESS_UPDATE_DELTA:I = 0x2

.field private static final CLIENT_CONFIG_UUID:Ljava/util/UUID;

.field private static final CONNECT_ATTEMPT_TIMEOUT_MS:J = 0x2710L

.field private static final CONNECT_RETRY_MS:J = 0x1388L

.field private static final DAY_WARNING_DIM_PERCENT:I = 0x2d

.field private static final DAY_WARNING_STEP_INTERVAL_MS:J = 0x2bcL

.field private static final DEFAULT_ACK_SETTLE_INTERVAL_MS:I = 0xa

.field private static final DEFAULT_AMBIENT_TRANSITION_STEP_MS:I = 0x21

.field private static final GATT_ERROR_RETRY_MS:J = 0x5dcL

.field private static final LEGACY_SERVICE_UUID:Ljava/util/UUID;

.field private static final LOW_LIGHT_CHECK_INTERVAL_MS:J = 0x3e8L

.field private static final MANUAL_OVERRIDE_MAX_MS:J = 0x124f80L

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

.field private mAmbientFadeStartZone1Blue:I

.field private mAmbientFadeStartZone1Green:I

.field private mAmbientFadeStartZone1Red:I

.field private mAmbientFadeStartZone2:I

.field private mAmbientFadeStartZone2Blue:I

.field private mAmbientFadeStartZone2Green:I

.field private mAmbientFadeStartZone2Red:I

.field private mAmbientFadeStartedAtMs:J

.field private mAmbientTargetZone1:I

.field private mAmbientTargetZone1Blue:I

.field private mAmbientTargetZone1Green:I

.field private mAmbientTargetZone1Red:I

.field private mAmbientTargetZone2:I

.field private mAmbientTargetZone2Blue:I

.field private mAmbientTargetZone2Green:I

.field private mAmbientTargetZone2Red:I

.field private final mBlinkRunnable:Ljava/lang/Runnable;

.field private final mBrightnessSyncRunnable:Ljava/lang/Runnable;

.field private final mConnectTimeoutRunnable:Ljava/lang/Runnable;

.field private mConnected:Z

.field private mConnecting:Z

.field private final mContext:Landroid/content/Context;

.field private final mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

.field private mCurrentZone1:I

.field private mCurrentZone1Blue:I

.field private mCurrentZone1Green:I

.field private mCurrentZone1Red:I

.field private mCurrentZone2:I

.field private mCurrentZone2Blue:I

.field private mCurrentZone2Green:I

.field private mCurrentZone2Red:I

.field private mDayWarningDimmed:Z

.field private mDoorOpen:Z

.field private mExitCourtesyActive:Z

.field private final mFlushAfterAckRunnable:Ljava/lang/Runnable;

.field private mGatt:Landroid/bluetooth/BluetoothGatt;

.field private final mGattCallback:Landroid/bluetooth/BluetoothGattCallback;

.field private final mHandler:Landroid/os/Handler;

.field private mLastAmbientBrightness:I

.field private mLastGear:Ljava/lang/String;

.field private mLastVehicleDataAtMs:J

.field private mLowLightWarning:Z

.field private mManualOverrideActive:Z

.field private mManualOverrideExpiresAtMs:J

.field private final mManualOverrideExpiryRunnable:Ljava/lang/Runnable;

.field private mManualOverrideId:Ljava/lang/String;

.field private mManualZone1Blue:I

.field private mManualZone1Brightness:I

.field private mManualZone1Enabled:Z

.field private mManualZone1Green:I

.field private mManualZone1Red:I

.field private mManualZone2Blue:I

.field private mManualZone2Brightness:I

.field private mManualZone2Enabled:Z

.field private mManualZone2Green:I

.field private mManualZone2Red:I

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

.field private mProfile:Lorg/json/JSONObject;

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

.field private mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

.field private final mWritePaceRunnable:Ljava/lang/Runnable;

.field private final mWriteTimeoutRunnable:Ljava/lang/Runnable;

.field private mWriting:Z


# direct methods
.method static constructor <clinit>()V
    .locals 3

    .line 32
    const-string v0, "0000ae30-0000-1000-8000-00805f9b34fb"

    invoke-static {v0}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;

    move-result-object v0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->SERVICE_UUID:Ljava/util/UUID;

    .line 33
    const-string v0, "0000ae00-0000-1000-8000-00805f9b34fb"

    invoke-static {v0}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;

    move-result-object v0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->LEGACY_SERVICE_UUID:Ljava/util/UUID;

    .line 34
    const-string v0, "0000ae01-0000-1000-8000-00805f9b34fb"

    invoke-static {v0}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;

    move-result-object v0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->WRITE_UUID:Ljava/util/UUID;

    .line 35
    const-string v0, "0000ae02-0000-1000-8000-00805f9b34fb"

    invoke-static {v0}, Ljava/util/UUID;->fromString(Ljava/lang/String;)Ljava/util/UUID;

    move-result-object v0

    sput-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->NOTIFY_UUID:Ljava/util/UUID;

    .line 36
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

    .line 518
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

    .line 297
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$8;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$8;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    .line 310
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$9;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$9;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    .line 322
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$10;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$10;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFlushAfterAckRunnable:Ljava/lang/Runnable;

    .line 330
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$11;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$11;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    .line 341
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$12;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeRunnable:Ljava/lang/Runnable;

    .line 371
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$13;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$13;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    .line 385
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$14;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxRunnable:Ljava/lang/Runnable;

    .line 396
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$15;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    .line 410
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$16;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiryRunnable:Ljava/lang/Runnable;

    .line 419
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$17;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$17;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataWatchdogRunnable:Ljava/lang/Runnable;

    .line 480
    const/16 v0, 0xff

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Red:I

    .line 481
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Green:I

    .line 482
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Blue:I

    .line 483
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Red:I

    .line 484
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Green:I

    .line 485
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Blue:I

    .line 500
    const/4 v1, -0x1

    iput v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 501
    const-string v1, ""

    iput-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastGear:Ljava/lang/String;

    .line 505
    iput-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideId:Ljava/lang/String;

    .line 506
    const/4 v1, 0x1

    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Enabled:Z

    .line 507
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Enabled:Z

    .line 508
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Red:I

    .line 509
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Green:I

    .line 510
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Blue:I

    .line 511
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Red:I

    .line 512
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Green:I

    .line 513
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Blue:I

    .line 514
    const/16 v0, 0x14

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Brightness:I

    .line 515
    const/16 v0, 0x28

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Brightness:I

    .line 516
    new-instance v0, Lorg/json/JSONObject;

    invoke-direct {v0}, Lorg/json/JSONObject;-><init>()V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mProfile:Lorg/json/JSONObject;

    .line 519
    invoke-virtual {p1}, Landroid/content/Context;->getApplicationContext()Landroid/content/Context;

    move-result-object p1

    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    .line 520
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->loadAmbientProfile()V

    .line 521
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    const-string v0, "power"

    invoke-virtual {p1, v0}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object p1

    check-cast p1, Landroid/os/PowerManager;

    .line 522
    if-nez p1, :cond_0

    const/4 p1, 0x0

    goto :goto_0

    .line 523
    :cond_0
    const-string v0, "NavdyAmbient:OffroadController"

    invoke-virtual {p1, v1, v0}, Landroid/os/PowerManager;->newWakeLock(ILjava/lang/String;)Landroid/os/PowerManager$WakeLock;

    move-result-object p1

    :goto_0
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    .line 524
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    if-eqz p1, :cond_1

    .line 525
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    const/4 v0, 0x0

    invoke-virtual {p1, v0}, Landroid/os/PowerManager$WakeLock;->setReferenceCounted(Z)V

    .line 527
    :cond_1
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    iput-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastVehicleDataAtMs:J

    .line 528
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataWatchdogRunnable:Ljava/lang/Runnable;

    const-wide/16 v1, 0xbb8

    invoke-virtual {p1, v0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 529
    return-void
.end method

.method static synthetic access$000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGatt;
    .locals 0

    .line 30
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    return-object p0
.end method

.method static synthetic access$002(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGatt;
    .locals 0

    .line 30
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    return-object p1
.end method

.method static synthetic access$100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    return p0
.end method

.method static synthetic access$1000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 30
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$102(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    return p1
.end method

.method static synthetic access$1100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 30
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFlushAfterAckRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$1200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 30
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$1300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 30
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    return-object p0
.end method

.method static synthetic access$1302(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 30
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    return-object p1
.end method

.method static synthetic access$1400(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 30
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    return-object p0
.end method

.method static synthetic access$1402(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 30
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    return-object p1
.end method

.method static synthetic access$1502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyReady:Z

    return p1
.end method

.method static synthetic access$1602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStartQueued:Z

    return p1
.end method

.method static synthetic access$1700(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->closeGatt()V

    return-void
.end method

.method static synthetic access$1800(Lcom/navdy/hud/app/ambient/AmbientLightController;J)V
    .locals 0

    .line 30
    invoke-direct {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    return-void
.end method

.method static synthetic access$1900(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 30
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->findWriteCharacteristic(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 30
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnectTimeoutRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$2000(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 0

    .line 30
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->findNotifyCharacteristic(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$2100(Landroid/bluetooth/BluetoothGattCharacteristic;)V
    .locals 0

    .line 30
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->configureWriteCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)V

    return-void
.end method

.method static synthetic access$2200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->queueStartPacket()V

    return-void
.end method

.method static synthetic access$2300(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->restoreActiveStateAfterConnect()V

    return-void
.end method

.method static synthetic access$2400(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z
    .locals 0

    .line 30
    invoke-static {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->enableNotifications(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result p0

    return p0
.end method

.method static synthetic access$2500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->flushNext()V

    return-void
.end method

.method static synthetic access$2600([B)Ljava/lang/String;
    .locals 0

    .line 30
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->bytesToHex([B)Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$2700(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->writeAck()V

    return-void
.end method

.method static synthetic access$2800(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAckSettleIntervalMs()I

    move-result p0

    return p0
.end method

.method static synthetic access$2900(Landroid/bluetooth/BluetoothDevice;[B)Z
    .locals 0

    .line 30
    invoke-static {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->matchesAmbientDevice(Landroid/bluetooth/BluetoothDevice;[B)Z

    move-result p0

    return p0
.end method

.method static synthetic access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;
    .locals 0

    .line 30
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    return-object p0
.end method

.method static synthetic access$3000(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothDevice;I)V
    .locals 0

    .line 30
    invoke-direct {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->logSeenScanDevice(Landroid/bluetooth/BluetoothDevice;I)V

    return-void
.end method

.method static synthetic access$3100(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;
    .locals 0

    .line 30
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$3200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopScan()V

    return-void
.end method

.method static synthetic access$3300(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothDevice;)V
    .locals 0

    .line 30
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectDevice(Landroid/bluetooth/BluetoothDevice;)V

    return-void
.end method

.method static synthetic access$3400(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect()V

    return-void
.end method

.method static synthetic access$3500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectIfNeeded()V

    return-void
.end method

.method static synthetic access$3600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mRequestedOverspeed:Z

    return p0
.end method

.method static synthetic access$3602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mRequestedOverspeed:Z

    return p1
.end method

.method static synthetic access$3700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    return p0
.end method

.method static synthetic access$3702(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    return p1
.end method

.method static synthetic access$3800(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V
    .locals 0

    .line 30
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setOverspeed(Z)V

    return-void
.end method

.method static synthetic access$3900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    return p0
.end method

.method static synthetic access$4000(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientBrightness()I

    move-result p0

    return p0
.end method

.method static synthetic access$402(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSkipRememberedOnce:Z

    return p1
.end method

.method static synthetic access$4100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningAnimationStarted:Z

    return p0
.end method

.method static synthetic access$4102(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningAnimationStarted:Z

    return p1
.end method

.method static synthetic access$4200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLowLightWarning:Z

    return p0
.end method

.method static synthetic access$4202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLowLightWarning:Z

    return p1
.end method

.method static synthetic access$4300(Lcom/navdy/hud/app/ambient/AmbientLightController;)[B
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->warningColorPacket()[B

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$4400(Lcom/navdy/hud/app/ambient/AmbientLightController;[B)V
    .locals 0

    .line 30
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    return-void
.end method

.method static synthetic access$4500(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->warningZone2Brightness()I

    move-result p0

    return p0
.end method

.method static synthetic access$4600(ZII)[B
    .locals 0

    .line 30
    invoke-static {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildBrightnessPacket(ZII)[B

    move-result-object p0

    return-object p0
.end method

.method static synthetic access$4700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDayWarningDimmed:Z

    return p0
.end method

.method static synthetic access$4702(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDayWarningDimmed:Z

    return p1
.end method

.method static synthetic access$4800(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    return p0
.end method

.method static synthetic access$4802(Lcom/navdy/hud/app/ambient/AmbientLightController;I)I
    .locals 0

    .line 30
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    return p1
.end method

.method static synthetic access$4900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    return p0
.end method

.method static synthetic access$500(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    return p0
.end method

.method static synthetic access$5000(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V
    .locals 0

    .line 30
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->syncAmbientBrightness(Z)V

    return-void
.end method

.method static synthetic access$502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    return p1
.end method

.method static synthetic access$5100(Lcom/navdy/hud/app/ambient/AmbientLightController;)J
    .locals 2

    .line 30
    iget-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartedAtMs:J

    return-wide v0
.end method

.method static synthetic access$5200(Lcom/navdy/hud/app/ambient/AmbientLightController;)J
    .locals 2

    .line 30
    iget-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeDurationMs:J

    return-wide v0
.end method

.method static synthetic access$5300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1:I

    return p0
.end method

.method static synthetic access$5400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    return p0
.end method

.method static synthetic access$5500(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2:I

    return p0
.end method

.method static synthetic access$5600(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    return p0
.end method

.method static synthetic access$5700(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1Red:I

    return p0
.end method

.method static synthetic access$5800(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1Red:I

    return p0
.end method

.method static synthetic access$5900(IIF)I
    .locals 0

    .line 30
    invoke-static {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->interpolate(IIF)I

    move-result p0

    return p0
.end method

.method static synthetic access$6000(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1Green:I

    return p0
.end method

.method static synthetic access$602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectScheduled:Z

    return p1
.end method

.method static synthetic access$6100(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1Green:I

    return p0
.end method

.method static synthetic access$6200(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1Blue:I

    return p0
.end method

.method static synthetic access$6300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1Blue:I

    return p0
.end method

.method static synthetic access$6400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2Red:I

    return p0
.end method

.method static synthetic access$6500(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2Red:I

    return p0
.end method

.method static synthetic access$6600(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2Green:I

    return p0
.end method

.method static synthetic access$6700(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2Green:I

    return p0
.end method

.method static synthetic access$6800(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2Blue:I

    return p0
.end method

.method static synthetic access$6900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2Blue:I

    return p0
.end method

.method static synthetic access$700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 30
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$7000(Lcom/navdy/hud/app/ambient/AmbientLightController;IIIIIIIIZ)V
    .locals 0

    .line 30
    invoke-direct/range {p0 .. p9}, Lcom/navdy/hud/app/ambient/AmbientLightController;->applyAmbientFrame(IIIIIIIIZ)V

    return-void
.end method

.method static synthetic access$7100(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientFrameStepMs()I

    move-result p0

    return p0
.end method

.method static synthetic access$7200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    return p0
.end method

.method static synthetic access$7202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    return p1
.end method

.method static synthetic access$7300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    return p0
.end method

.method static synthetic access$7302(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    return p1
.end method

.method static synthetic access$7402(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mExitCourtesyActive:Z

    return p1
.end method

.method static synthetic access$7500(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    return p0
.end method

.method static synthetic access$7600(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone1Brightness()I

    move-result p0

    return p0
.end method

.method static synthetic access$7700(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result p0

    return p0
.end method

.method static synthetic access$7800(Lcom/navdy/hud/app/ambient/AmbientLightController;)J
    .locals 2

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v0

    return-wide v0
.end method

.method static synthetic access$7900(Lcom/navdy/hud/app/ambient/AmbientLightController;IIJ)V
    .locals 0

    .line 30
    invoke-direct {p0, p1, p2, p3, p4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    return-void
.end method

.method static synthetic access$800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    return p0
.end method

.method static synthetic access$8002(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    return p1
.end method

.method static synthetic access$802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    return p1
.end method

.method static synthetic access$8100(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V
    .locals 0

    .line 30
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    return-void
.end method

.method static synthetic access$8200(Lcom/navdy/hud/app/ambient/AmbientLightController;)J
    .locals 2

    .line 30
    iget-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiresAtMs:J

    return-wide v0
.end method

.method static synthetic access$8300(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V
    .locals 0

    .line 30
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clearManualOverride(Ljava/lang/String;)V

    return-void
.end method

.method static synthetic access$8400(Lcom/navdy/hud/app/ambient/AmbientLightController;)J
    .locals 2

    .line 30
    iget-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastVehicleDataAtMs:J

    return-wide v0
.end method

.method static synthetic access$8502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    return p1
.end method

.method static synthetic access$8600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    return p0
.end method

.method static synthetic access$8602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    return p1
.end method

.method static synthetic access$8700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 30
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedStateRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$8802(Lcom/navdy/hud/app/ambient/AmbientLightController;J)J
    .locals 0

    .line 30
    iput-wide p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActivatedAtMs:J

    return-wide p1
.end method

.method static synthetic access$8900(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    return-void
.end method

.method static synthetic access$900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 30
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$9000(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBrightnessSync()V

    return-void
.end method

.method static synthetic access$9100(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->cancelOffroadTimers()V

    return-void
.end method

.method static synthetic access$9200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->updateCpuWakeLock()V

    return-void
.end method

.method static synthetic access$9300(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->noteVehicleDataReceived()V

    return-void
.end method

.method static synthetic access$9400(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V
    .locals 0

    .line 30
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setGearText(Ljava/lang/String;)V

    return-void
.end method

.method static synthetic access$9500(Lcom/navdy/hud/app/ambient/AmbientLightController;ZZ)V
    .locals 0

    .line 30
    invoke-direct {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setVehicleState(ZZ)V

    return-void
.end method

.method static synthetic access$9600(Lcom/navdy/hud/app/ambient/AmbientLightController;Lorg/json/JSONObject;)V
    .locals 0

    .line 30
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setAmbientOverride(Lorg/json/JSONObject;)V

    return-void
.end method

.method static synthetic access$9700(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V
    .locals 0

    .line 30
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestOverspeed(Z)V

    return-void
.end method

.method static synthetic access$9800(Lcom/navdy/hud/app/ambient/AmbientLightController;II)V
    .locals 0

    .line 30
    invoke-direct {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestCameraSpeed(II)V

    return-void
.end method

.method private activeStateColorPacket()[B
    .locals 2

    .line 771
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_0

    .line 772
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalColorPacket()[B

    move-result-object v0

    return-object v0

    .line 774
    :cond_0
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mExitCourtesyActive:Z

    if-eqz v0, :cond_1

    .line 775
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->exitCourtesyColorPacket()[B

    move-result-object v0

    return-object v0

    .line 777
    :cond_1
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    const/4 v1, 0x1

    if-nez v0, :cond_2

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eqz v0, :cond_2

    const-string v0, "offroadDoor"

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result v0

    if-eqz v0, :cond_2

    .line 778
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->offroadDoorColorPacket()[B

    move-result-object v0

    return-object v0

    .line 780
    :cond_2
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_3

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eqz v0, :cond_3

    const-string v0, "onroadDoor"

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result v0

    if-eqz v0, :cond_3

    .line 781
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onroadDoorColorPacket()[B

    move-result-object v0

    return-object v0

    .line 783
    :cond_3
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->drivingColorPacket()[B

    move-result-object v0

    return-object v0
.end method

.method private applyAmbientFrame(IIIIIIIIZ)V
    .locals 2

    .line 1169
    const/4 v0, 0x0

    const/16 v1, 0x64

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    .line 1170
    invoke-static {p2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2:I

    .line 1171
    const/16 p1, 0xff

    invoke-static {p3, v0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Red:I

    .line 1172
    invoke-static {p4, v0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Green:I

    .line 1173
    invoke-static {p5, v0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Blue:I

    .line 1174
    invoke-static {p6, v0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Red:I

    .line 1175
    invoke-static {p7, v0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Green:I

    .line 1176
    invoke-static {p8, v0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Blue:I

    .line 1177
    if-eqz p9, :cond_0

    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    if-nez p1, :cond_0

    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2:I

    if-nez p1, :cond_0

    .line 1178
    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 1179
    sget-object p1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_OFF:[B

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    goto :goto_0

    .line 1181
    :cond_0
    const/4 p1, 0x1

    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 1182
    iget p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Red:I

    iget p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Green:I

    iget p4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Blue:I

    iget p5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Red:I

    iget p6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Green:I

    iget p7, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Blue:I

    .line 1183
    invoke-static/range {p2 .. p7}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildColorPacket(IIIIII)[B

    move-result-object p2

    iget p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    iget p4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2:I

    .line 1186
    invoke-static {p1, p3, p4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildBrightnessPacket(ZII)[B

    move-result-object p1

    .line 1182
    invoke-direct {p0, p2, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendAmbientFrame([B[B)V

    .line 1188
    :goto_0
    return-void
.end method

.method private applyVehicleStateTargets()V
    .locals 4

    .line 1025
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileMasterEnabled()Z

    move-result v0

    if-nez v0, :cond_0

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-nez v0, :cond_0

    .line 1026
    const-string v0, "profile disabled"

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    goto/16 :goto_4

    .line 1027
    :cond_0
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez v0, :cond_7

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-eqz v0, :cond_1

    goto :goto_2

    .line 1029
    :cond_1
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    const/4 v1, 0x1

    if-eqz v0, :cond_3

    .line 1030
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mExitCourtesyActive:Z

    .line 1031
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone1Brightness()I

    move-result v0

    .line 1032
    iget-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eqz v2, :cond_2

    const-string v2, "onroadDoor"

    invoke-direct {p0, v2, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result v1

    if-eqz v1, :cond_2

    .line 1033
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onroadDoorZone2Brightness()I

    move-result v1

    goto :goto_0

    :cond_2
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result v1

    .line 1034
    :goto_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v2

    .line 1031
    invoke-direct {p0, v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    goto :goto_4

    .line 1035
    :cond_3
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eqz v0, :cond_6

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    if-nez v0, :cond_6

    .line 1036
    const-string v0, "offroadDoor"

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result v0

    if-nez v0, :cond_5

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_4

    goto :goto_1

    .line 1040
    :cond_4
    const-string v0, "offroad door profile disabled"

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    goto :goto_4

    .line 1037
    :cond_5
    :goto_1
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->offroadDoorZone1Brightness()I

    move-result v0

    .line 1038
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->offroadDoorZone2Brightness()I

    move-result v1

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v2

    .line 1037
    invoke-direct {p0, v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    goto :goto_4

    .line 1042
    :cond_6
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_9

    .line 1043
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone1Brightness()I

    move-result v0

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result v1

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v2

    invoke-direct {p0, v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    goto :goto_4

    .line 1028
    :cond_7
    :goto_2
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-eqz v0, :cond_8

    const-string v0, "reverse"

    goto :goto_3

    :cond_8
    const-string v0, "comma data timeout"

    :goto_3
    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    .line 1045
    :cond_9
    :goto_4
    return-void
.end method

.method private beginRestoreFade()V
    .locals 4

    .line 1091
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBlinkRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1092
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_2

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez v0, :cond_2

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-eqz v0, :cond_0

    goto :goto_1

    .line 1096
    :cond_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 1097
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone1Brightness()I

    move-result v0

    .line 1098
    iget-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eqz v1, :cond_1

    const-string v1, "onroadDoor"

    const/4 v2, 0x1

    invoke-direct {p0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result v1

    if-eqz v1, :cond_1

    .line 1099
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onroadDoorZone2Brightness()I

    move-result v1

    goto :goto_0

    :cond_1
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result v1

    .line 1100
    :goto_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v2

    .line 1097
    invoke-direct {p0, v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    .line 1101
    return-void

    .line 1093
    :cond_2
    :goto_1
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 1094
    return-void
.end method

.method private static buildBrightnessPacket(ZI)[B
    .locals 1

    .line 1609
    const/16 v0, 0x28

    invoke-static {p0, p1, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildBrightnessPacket(ZII)[B

    move-result-object p0

    return-object p0
.end method

.method private static buildBrightnessPacket(ZII)[B
    .locals 2

    .line 1613
    const/16 v0, 0x64

    const/4 v1, 0x0

    if-eqz p0, :cond_0

    invoke-static {p1, v1, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    goto :goto_0

    :cond_0
    const/4 p1, 0x0

    .line 1614
    :goto_0
    if-eqz p0, :cond_1

    invoke-static {p2, v1, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p2

    goto :goto_1

    :cond_1
    const/4 p2, 0x0

    .line 1615
    :goto_1
    if-eqz p0, :cond_2

    const/16 p0, 0x48

    goto :goto_2

    :cond_2
    const/4 p0, 0x0

    .line 1616
    :goto_2
    const/16 v0, 0x8d

    filled-new-array {v1, p0, p1, p2}, [I

    move-result-object p0

    invoke-static {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildPacket(I[I)[B

    move-result-object p0

    return-object p0
.end method

.method private static buildColorPacket(IIIIII)[B
    .locals 10

    .line 1621
    nop

    .line 1623
    const/4 v0, 0x0

    const/16 v1, 0xff

    invoke-static {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v4

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v5

    invoke-static {p2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v6

    .line 1624
    invoke-static {p3, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v7

    invoke-static {p4, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v8

    invoke-static {p5, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v9

    const/4 v2, 0x1

    const/16 v3, 0x8

    filled-new-array/range {v2 .. v9}, [I

    move-result-object p0

    .line 1621
    const/16 p1, 0x8d

    invoke-static {p1, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildPacket(I[I)[B

    move-result-object p0

    return-object p0
.end method

.method private static buildPacket(I[I)[B
    .locals 8

    .line 1638
    array-length v0, p1

    .line 1639
    add-int/lit8 v1, v0, 0x4

    new-array v2, v1, [B

    .line 1640
    const/16 v3, 0x2e

    const/4 v4, 0x0

    aput-byte v3, v2, v4

    .line 1641
    int-to-byte v3, p0

    const/4 v5, 0x1

    aput-byte v3, v2, v5

    .line 1642
    const/4 v3, 0x2

    int-to-byte v6, v0

    aput-byte v6, v2, v3

    .line 1643
    add-int/2addr p0, v0

    .line 1644
    nop

    :goto_0
    if-ge v4, v0, :cond_0

    .line 1645
    aget v3, p1, v4

    and-int/lit16 v3, v3, 0xff

    .line 1646
    add-int/lit8 v6, v4, 0x3

    int-to-byte v7, v3

    aput-byte v7, v2, v6

    .line 1647
    add-int/2addr p0, v3

    .line 1644
    add-int/lit8 v4, v4, 0x1

    goto :goto_0

    .line 1649
    :cond_0
    sub-int/2addr v1, v5

    not-int p0, p0

    and-int/lit16 p0, p0, 0xff

    int-to-byte p0, p0

    aput-byte p0, v2, v1

    .line 1650
    return-object v2
.end method

.method private static bytesToHex([B)Ljava/lang/String;
    .locals 7

    .line 1730
    new-instance v0, Ljava/lang/StringBuilder;

    array-length v1, p0

    mul-int/lit8 v1, v1, 0x2

    invoke-direct {v0, v1}, Ljava/lang/StringBuilder;-><init>(I)V

    .line 1731
    array-length v1, p0

    const/4 v2, 0x0

    const/4 v3, 0x0

    :goto_0
    if-ge v3, v1, :cond_0

    aget-byte v4, p0, v3

    .line 1732
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

    .line 1731
    add-int/lit8 v3, v3, 0x1

    goto :goto_0

    .line 1734
    :cond_0
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method private cancelOffroadTimers()V
    .locals 2

    .line 1048
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1049
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1050
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1051
    return-void
.end method

.method private static clamp(III)I
    .locals 0

    .line 1654
    invoke-static {p2, p0}, Ljava/lang/Math;->min(II)I

    move-result p0

    invoke-static {p1, p0}, Ljava/lang/Math;->max(II)I

    move-result p0

    return p0
.end method

.method private clearManualOverride(Ljava/lang/String;)V
    .locals 2

    .line 838
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-nez v0, :cond_0

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideId:Ljava/lang/String;

    invoke-virtual {v0}, Ljava/lang/String;->length()I

    move-result v0

    if-nez v0, :cond_0

    .line 839
    return-void

    .line 841
    :cond_0
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "manual ambient override cleared reason="

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    const-string v0, "NavdyAmbient"

    invoke-static {v0, p1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 842
    const/4 p1, 0x0

    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    .line 843
    const-wide/16 v0, 0x0

    iput-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiresAtMs:J

    .line 844
    const-string v0, ""

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideId:Ljava/lang/String;

    .line 845
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiryRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 846
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-eqz v0, :cond_1

    .line 847
    const-string p1, "reverse"

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    goto :goto_0

    .line 848
    :cond_1
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-nez v0, :cond_2

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-nez v0, :cond_2

    .line 849
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v0

    invoke-direct {p0, p1, p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    goto :goto_0

    .line 851
    :cond_2
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->applyVehicleStateTargets()V

    .line 853
    :goto_0
    return-void
.end method

.method private closeGatt()V
    .locals 2

    .line 1430
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    .line 1431
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnectTimeoutRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1432
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    if-eqz v0, :cond_0

    .line 1434
    :try_start_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    invoke-virtual {v0}, Landroid/bluetooth/BluetoothGatt;->close()V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 1436
    goto :goto_0

    .line 1435
    :catch_0
    move-exception v0

    .line 1437
    :goto_0
    const/4 v0, 0x0

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    .line 1439
    :cond_0
    return-void
.end method

.method private coalescePendingBrightnessPackets()V
    .locals 3

    .line 1565
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->isEmpty()Z

    move-result v0

    if-eqz v0, :cond_0

    .line 1566
    return-void

    .line 1568
    :cond_0
    new-instance v0, Ljava/util/ArrayDeque;

    invoke-direct {v0}, Ljava/util/ArrayDeque;-><init>()V

    .line 1569
    :goto_0
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1}, Ljava/util/ArrayDeque;->isEmpty()Z

    move-result v1

    if-nez v1, :cond_2

    .line 1570
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1}, Ljava/util/ArrayDeque;->poll()Ljava/lang/Object;

    move-result-object v1

    check-cast v1, [B

    .line 1571
    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isBrightnessPacket([B)Z

    move-result v2

    if-nez v2, :cond_1

    .line 1572
    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1574
    :cond_1
    goto :goto_0

    .line 1575
    :cond_2
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1, v0}, Ljava/util/ArrayDeque;->addAll(Ljava/util/Collection;)Z

    .line 1576
    return-void
.end method

.method private static colorPacketValue([BII)I
    .locals 1

    .line 1629
    if-eqz p0, :cond_0

    if-ltz p1, :cond_0

    array-length v0, p0

    add-int/lit8 v0, v0, -0x1

    if-ge p1, v0, :cond_0

    .line 1630
    aget-byte p0, p0, p1

    and-int/lit16 p2, p0, 0xff

    goto :goto_0

    :cond_0
    nop

    .line 1629
    :goto_0
    return p2
.end method

.method private static colorValue(Lorg/json/JSONObject;II)I
    .locals 2

    .line 658
    if-eqz p0, :cond_1

    const-string v0, "rgb"

    invoke-virtual {p0, v0}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v1

    if-nez v1, :cond_0

    goto :goto_0

    .line 661
    :cond_0
    invoke-virtual {p0, v0}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object p0

    invoke-virtual {p0, p1, p2}, Lorg/json/JSONArray;->optInt(II)I

    move-result p0

    const/4 p1, 0x0

    const/16 p2, 0xff

    invoke-static {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p0

    return p0

    .line 659
    :cond_1
    :goto_0
    return p2
.end method

.method private static configureWriteCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)V
    .locals 1

    .line 1658
    invoke-virtual {p0}, Landroid/bluetooth/BluetoothGattCharacteristic;->getProperties()I

    move-result v0

    .line 1659
    and-int/lit8 v0, v0, 0x4

    if-eqz v0, :cond_0

    .line 1660
    const/4 v0, 0x1

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGattCharacteristic;->setWriteType(I)V

    goto :goto_0

    .line 1662
    :cond_0
    const/4 v0, 0x2

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGattCharacteristic;->setWriteType(I)V

    .line 1664
    :goto_0
    return-void
.end method

.method private connectBondedCandidate()Z
    .locals 4

    .line 1388
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    invoke-virtual {v0}, Landroid/bluetooth/BluetoothAdapter;->getBondedDevices()Ljava/util/Set;

    move-result-object v0

    .line 1389
    const/4 v1, 0x0

    if-nez v0, :cond_0

    .line 1390
    return v1

    .line 1392
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

    .line 1393
    if-eqz v2, :cond_1

    const/4 v3, 0x0

    invoke-static {v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->matchesAmbientDevice(Landroid/bluetooth/BluetoothDevice;[B)Z

    move-result v3

    if-eqz v3, :cond_1

    .line 1394
    invoke-direct {p0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectDevice(Landroid/bluetooth/BluetoothDevice;)V

    .line 1395
    const/4 v0, 0x1

    return v0

    .line 1397
    :cond_1
    goto :goto_0

    .line 1398
    :cond_2
    return v1
.end method

.method private connectDevice(Landroid/bluetooth/BluetoothDevice;)V
    .locals 4

    .line 1402
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->closeGatt()V

    .line 1403
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    .line 1404
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectScheduled:Z

    .line 1405
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectRunnable:Ljava/lang/Runnable;

    invoke-virtual {v1, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1406
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    .line 1407
    invoke-virtual {v1}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v1

    invoke-virtual {p1}, Landroid/bluetooth/BluetoothDevice;->getAddress()Ljava/lang/String;

    move-result-object v2

    .line 1406
    const-string v3, "navdy_ambient_device_address"

    invoke-static {v1, v3, v2}, Landroid/provider/Settings$System;->putString(Landroid/content/ContentResolver;Ljava/lang/String;Ljava/lang/String;)Z

    .line 1408
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

    .line 1409
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;

    invoke-virtual {p1, v1, v0, v2}, Landroid/bluetooth/BluetoothDevice;->connectGatt(Landroid/content/Context;ZLandroid/bluetooth/BluetoothGattCallback;)Landroid/bluetooth/BluetoothGatt;

    move-result-object p1

    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    .line 1410
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    if-nez p1, :cond_0

    .line 1411
    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    .line 1412
    const-wide/16 v0, 0x1388

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    goto :goto_0

    .line 1414
    :cond_0
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnectTimeoutRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1415
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnectTimeoutRunnable:Ljava/lang/Runnable;

    const-wide/16 v1, 0x2710

    invoke-virtual {p1, v0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 1417
    :goto_0
    return-void
.end method

.method private connectIfNeeded()V
    .locals 5

    .line 1328
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    if-nez v0, :cond_7

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    if-nez v0, :cond_7

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    if-nez v0, :cond_7

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectScheduled:Z

    if-eqz v0, :cond_0

    goto/16 :goto_2

    .line 1331
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    if-nez v0, :cond_1

    .line 1332
    invoke-static {}, Landroid/bluetooth/BluetoothAdapter;->getDefaultAdapter()Landroid/bluetooth/BluetoothAdapter;

    move-result-object v0

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    .line 1334
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

    .line 1339
    :cond_2
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSkipRememberedOnce:Z

    if-nez v0, :cond_3

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectRememberedCandidate()Z

    move-result v0

    if-eqz v0, :cond_3

    .line 1340
    return-void

    .line 1342
    :cond_3
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSkipRememberedOnce:Z

    .line 1343
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectBondedCandidate()Z

    move-result v0

    if-eqz v0, :cond_4

    .line 1344
    return-void

    .line 1346
    :cond_4
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSeenScanDevices:Ljava/util/Set;

    invoke-interface {v0}, Ljava/util/Set;->clear()V

    .line 1347
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanCallback:Landroid/bluetooth/BluetoothAdapter$LeScanCallback;

    invoke-virtual {v0, v4}, Landroid/bluetooth/BluetoothAdapter;->startLeScan(Landroid/bluetooth/BluetoothAdapter$LeScanCallback;)Z

    move-result v0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    .line 1348
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

    .line 1349
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    if-eqz v0, :cond_5

    .line 1350
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStopScanRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1351
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStopScanRunnable:Ljava/lang/Runnable;

    const-wide/16 v2, 0x2710

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    goto :goto_0

    .line 1353
    :cond_5
    invoke-direct {p0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    .line 1355
    :goto_0
    return-void

    .line 1335
    :cond_6
    :goto_1
    const-string v0, "bluetooth disabled"

    invoke-static {v3, v0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 1336
    invoke-direct {p0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    .line 1337
    return-void

    .line 1329
    :cond_7
    :goto_2
    return-void
.end method

.method private connectRememberedCandidate()Z
    .locals 4

    .line 1372
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    .line 1373
    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v0

    .line 1372
    const-string v1, "navdy_ambient_device_address"

    invoke-static {v0, v1}, Landroid/provider/Settings$System;->getString(Landroid/content/ContentResolver;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    .line 1374
    const/4 v1, 0x0

    if-eqz v0, :cond_1

    invoke-static {v0}, Landroid/bluetooth/BluetoothAdapter;->checkBluetoothAddress(Ljava/lang/String;)Z

    move-result v2

    if-nez v2, :cond_0

    goto :goto_0

    .line 1378
    :cond_0
    :try_start_0
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    invoke-virtual {v2, v0}, Landroid/bluetooth/BluetoothAdapter;->getRemoteDevice(Ljava/lang/String;)Landroid/bluetooth/BluetoothDevice;

    move-result-object v0

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectDevice(Landroid/bluetooth/BluetoothDevice;)V

    .line 1379
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSkipRememberedOnce:Z
    :try_end_0
    .catch Ljava/lang/IllegalArgumentException; {:try_start_0 .. :try_end_0} :catch_0

    .line 1380
    return v0

    .line 1381
    :catch_0
    move-exception v0

    .line 1382
    const-string v2, "NavdyAmbient"

    const-string v3, "bad remembered ambient address"

    invoke-static {v2, v3, v0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 1383
    return v1

    .line 1375
    :cond_1
    :goto_0
    return v1
.end method

.method private drivingColorPacket()[B
    .locals 3

    .line 755
    const-string v0, "zone1"

    const-string v1, "zone2"

    const-string v2, "driving"

    invoke-direct {p0, v2, v0, v2, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileColorPacket(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)[B

    move-result-object v0

    return-object v0
.end method

.method private static enableNotifications(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z
    .locals 5

    .line 1667
    const/4 v0, 0x0

    if-eqz p0, :cond_4

    if-nez p1, :cond_0

    goto :goto_2

    .line 1670
    :cond_0
    const/4 v1, 0x1

    invoke-virtual {p0, p1, v1}, Landroid/bluetooth/BluetoothGatt;->setCharacteristicNotification(Landroid/bluetooth/BluetoothGattCharacteristic;Z)Z

    move-result v2

    .line 1671
    sget-object v3, Lcom/navdy/hud/app/ambient/AmbientLightController;->CLIENT_CONFIG_UUID:Ljava/util/UUID;

    invoke-virtual {p1, v3}, Landroid/bluetooth/BluetoothGattCharacteristic;->getDescriptor(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattDescriptor;

    move-result-object p1

    .line 1672
    const-string v3, "NavdyAmbient"

    if-eqz v2, :cond_2

    if-nez p1, :cond_1

    goto :goto_0

    .line 1676
    :cond_1
    sget-object v0, Landroid/bluetooth/BluetoothGattDescriptor;->ENABLE_NOTIFICATION_VALUE:[B

    invoke-virtual {p1, v0}, Landroid/bluetooth/BluetoothGattDescriptor;->setValue([B)Z

    .line 1677
    invoke-virtual {p0, p1}, Landroid/bluetooth/BluetoothGatt;->writeDescriptor(Landroid/bluetooth/BluetoothGattDescriptor;)Z

    move-result p0

    .line 1678
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

    .line 1679
    return p0

    .line 1673
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

    .line 1674
    return v0

    .line 1668
    :cond_4
    :goto_2
    return v0
.end method

.method private exitCourtesyColorPacket()[B
    .locals 4

    .line 767
    const-string v0, "exitCourtesy"

    const-string v1, "zone2"

    const-string v2, "driving"

    const-string v3, "zone1"

    invoke-direct {p0, v2, v3, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileColorPacket(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)[B

    move-result-object v0

    return-object v0
.end method

.method private exitCourtesyZone2Brightness()I
    .locals 3

    .line 1253
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_0

    .line 1254
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result v0

    goto :goto_0

    .line 1255
    :cond_0
    const-string v0, "zone2"

    const/16 v1, 0x64

    const-string v2, "exitCourtesy"

    invoke-direct {p0, v2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileBrightness(Ljava/lang/String;Ljava/lang/String;I)I

    move-result v0

    .line 1253
    :goto_0
    return v0
.end method

.method private static findNotifyCharacteristic(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 1

    .line 1694
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->SERVICE_UUID:Ljava/util/UUID;

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;

    move-result-object v0

    .line 1695
    if-nez v0, :cond_0

    .line 1696
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->LEGACY_SERVICE_UUID:Ljava/util/UUID;

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;

    move-result-object v0

    .line 1698
    :cond_0
    if-nez v0, :cond_1

    .line 1699
    const/4 p0, 0x0

    return-object p0

    .line 1701
    :cond_1
    sget-object p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->NOTIFY_UUID:Ljava/util/UUID;

    invoke-virtual {v0, p0}, Landroid/bluetooth/BluetoothGattService;->getCharacteristic(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p0

    return-object p0
.end method

.method private static findWriteCharacteristic(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 1

    .line 1683
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->SERVICE_UUID:Ljava/util/UUID;

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;

    move-result-object v0

    .line 1684
    if-nez v0, :cond_0

    .line 1685
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->LEGACY_SERVICE_UUID:Ljava/util/UUID;

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;

    move-result-object v0

    .line 1687
    :cond_0
    if-nez v0, :cond_1

    .line 1688
    const/4 p0, 0x0

    return-object p0

    .line 1690
    :cond_1
    sget-object p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->WRITE_UUID:Ljava/util/UUID;

    invoke-virtual {v0, p0}, Landroid/bluetooth/BluetoothGattService;->getCharacteristic(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p0

    return-object p0
.end method

.method private flushNext()V
    .locals 6

    .line 1296
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

    .line 1299
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->poll()Ljava/lang/Object;

    move-result-object v0

    check-cast v0, [B

    .line 1300
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v1, v0}, Landroid/bluetooth/BluetoothGattCharacteristic;->setValue([B)Z

    .line 1301
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->configureWriteCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)V

    .line 1302
    const/4 v1, 0x1

    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    .line 1303
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    invoke-virtual {v2, v3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1304
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    invoke-virtual {v2, v3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1305
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    const-wide/16 v4, 0x4b0

    invoke-virtual {v2, v3, v4, v5}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 1306
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getWriteType()I

    move-result v2

    if-ne v2, v1, :cond_1

    .line 1307
    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->usesPacedWrite([B)Z

    move-result v1

    if-eqz v1, :cond_1

    .line 1308
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    const-wide/16 v3, 0x78

    invoke-virtual {v1, v2, v3, v4}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 1310
    :cond_1
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v1, v2}, Landroid/bluetooth/BluetoothGatt;->writeCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result v1

    .line 1311
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

    .line 1312
    if-nez v1, :cond_2

    .line 1313
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    invoke-virtual {v1, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1314
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    invoke-virtual {v1, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1315
    const/4 v1, 0x0

    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    .line 1316
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v2, v0}, Ljava/util/ArrayDeque;->offerFirst(Ljava/lang/Object;)Z

    .line 1317
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    .line 1318
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyReady:Z

    .line 1319
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStartQueued:Z

    .line 1320
    const/4 v0, 0x0

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 1321
    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 1322
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->closeGatt()V

    .line 1323
    const-wide/16 v0, 0x1388

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    .line 1325
    :cond_2
    return-void

    .line 1297
    :cond_3
    :goto_0
    return-void
.end method

.method public static declared-synchronized get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;
    .locals 2

    const-class v0, Lcom/navdy/hud/app/ambient/AmbientLightController;

    monitor-enter v0

    .line 532
    :try_start_0
    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->sInstance:Lcom/navdy/hud/app/ambient/AmbientLightController;

    if-nez v1, :cond_0

    .line 533
    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {v1, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;-><init>(Landroid/content/Context;)V

    sput-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->sInstance:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 535
    :cond_0
    sget-object p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->sInstance:Lcom/navdy/hud/app/ambient/AmbientLightController;
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    monitor-exit v0

    return-object p0

    .line 531
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

    .line 1202
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

    .line 1203
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1204
    const/4 p1, 0x0

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    .line 1205
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2:I

    .line 1206
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    .line 1207
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    .line 1208
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 1209
    sget-object p1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_OFF:[B

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    .line 1210
    return-void
.end method

.method private static interpolate(IIF)I
    .locals 1

    .line 1634
    int-to-float v0, p0

    sub-int/2addr p1, p0

    int-to-float p0, p1

    mul-float p0, p0, p2

    add-float/2addr v0, p0

    invoke-static {v0}, Ljava/lang/Math;->round(F)I

    move-result p0

    return p0
.end method

.method private static isBrightnessPacket([B)Z
    .locals 4

    .line 1588
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

.method private static isColorPacket([B)Z
    .locals 4

    .line 1594
    const/4 v0, 0x0

    if-eqz p0, :cond_0

    array-length v1, p0

    const/16 v2, 0xc

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

    const/16 v3, 0x8

    if-ne v2, v3, :cond_0

    const/4 v2, 0x3

    aget-byte p0, p0, v2

    if-ne p0, v1, :cond_0

    const/4 v0, 0x1

    :cond_0
    return v0
.end method

.method private static isDriveGear(Ljava/lang/String;)Z
    .locals 1

    .line 1768
    const-string v0, "p"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "park"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    .line 1769
    const-string v0, "n"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "neutral"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    .line 1770
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

    .line 1768
    :goto_1
    return p0
.end method

.method private static isReverse(Ljava/lang/String;)Z
    .locals 1

    .line 1764
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

    .line 1579
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

.method private loadAmbientProfile()V
    .locals 3

    .line 665
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    .line 666
    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v0

    .line 665
    const-string v1, "navdy_ambient_profile_json"

    invoke-static {v0, v1}, Landroid/provider/Settings$System;->getString(Landroid/content/ContentResolver;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    .line 667
    if-eqz v0, :cond_1

    invoke-virtual {v0}, Ljava/lang/String;->length()I

    move-result v1

    if-nez v1, :cond_0

    goto :goto_1

    .line 672
    :cond_0
    :try_start_0
    new-instance v1, Lorg/json/JSONObject;

    invoke-direct {v1, v0}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    iput-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mProfile:Lorg/json/JSONObject;
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 676
    goto :goto_0

    .line 673
    :catch_0
    move-exception v0

    .line 674
    const-string v1, "NavdyAmbient"

    const-string v2, "bad stored ambient profile"

    invoke-static {v1, v2, v0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 675
    new-instance v0, Lorg/json/JSONObject;

    invoke-direct {v0}, Lorg/json/JSONObject;-><init>()V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mProfile:Lorg/json/JSONObject;

    .line 677
    :goto_0
    return-void

    .line 668
    :cond_1
    :goto_1
    new-instance v0, Lorg/json/JSONObject;

    invoke-direct {v0}, Lorg/json/JSONObject;-><init>()V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mProfile:Lorg/json/JSONObject;

    .line 669
    return-void
.end method

.method private logSeenScanDevice(Landroid/bluetooth/BluetoothDevice;I)V
    .locals 3

    .line 1442
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;

    move-result-object v0

    .line 1443
    invoke-virtual {v0}, Ljava/lang/String;->length()I

    move-result v1

    if-nez v1, :cond_0

    .line 1444
    return-void

    .line 1446
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

    .line 1447
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSeenScanDevices:Ljava/util/Set;

    invoke-interface {v2, v1}, Ljava/util/Set;->add(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_1

    .line 1448
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

    .line 1450
    :cond_1
    return-void
.end method

.method private static matchesAmbientDevice(Landroid/bluetooth/BluetoothDevice;[B)Z
    .locals 2

    .line 1705
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;

    move-result-object p0

    sget-object v0, Ljava/util/Locale;->US:Ljava/util/Locale;

    invoke-virtual {p0, v0}, Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)Ljava/lang/String;

    move-result-object p0

    .line 1706
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

    .line 1707
    const-string v0, "slave"

    invoke-virtual {p0, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-eqz v0, :cond_0

    goto :goto_0

    .line 1710
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

    .line 1711
    const-string v0, "carled"

    invoke-virtual {p0, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "pocket"

    invoke-virtual {p0, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result p0

    if-nez p0, :cond_1

    .line 1712
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scanRecordContainsAmbientUuid([B)Z

    move-result p0

    if-eqz p0, :cond_2

    :cond_1
    const/4 v1, 0x1

    .line 1710
    :cond_2
    return v1

    .line 1708
    :cond_3
    :goto_0
    return v1
.end method

.method private needsConnection()Z
    .locals 1

    .line 1453
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

.method private normalColorPacket()[B
    .locals 7

    .line 1259
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-nez v0, :cond_0

    .line 1260
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->drivingColorPacket()[B

    move-result-object v0

    return-object v0

    .line 1262
    :cond_0
    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Red:I

    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Green:I

    iget v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Blue:I

    iget v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Red:I

    iget v5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Green:I

    iget v6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Blue:I

    invoke-static/range {v1 .. v6}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildColorPacket(IIIIII)[B

    move-result-object v0

    return-object v0
.end method

.method private normalZone1Brightness()I
    .locals 5

    .line 1218
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_1

    .line 1219
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Enabled:Z

    if-eqz v0, :cond_0

    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Brightness:I

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    :goto_0
    return v0

    .line 1221
    :cond_1
    const-string v0, "driving"

    const-string v1, "zone1"

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileZone(Ljava/lang/String;Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v2

    .line 1222
    const-string v3, "automaticBrightness"

    const/4 v4, 0x1

    invoke-virtual {v2, v3, v4}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v2

    if-nez v2, :cond_2

    .line 1223
    const/16 v2, 0x14

    invoke-direct {p0, v0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileBrightness(Ljava/lang/String;Ljava/lang/String;I)I

    move-result v0

    return v0

    .line 1225
    :cond_2
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientBrightness()I

    move-result v0

    return v0
.end method

.method private normalZone2Brightness()I
    .locals 3

    .line 1229
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_1

    .line 1230
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Enabled:Z

    if-eqz v0, :cond_0

    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Brightness:I

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    :goto_0
    return v0

    .line 1232
    :cond_1
    const-string v0, "zone2"

    const/16 v1, 0x28

    const-string v2, "driving"

    invoke-direct {p0, v2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileBrightness(Ljava/lang/String;Ljava/lang/String;I)I

    move-result v0

    return v0
.end method

.method private static normalizeGear(Ljava/lang/String;)Ljava/lang/String;
    .locals 1

    .line 1747
    invoke-virtual {p0}, Ljava/lang/String;->trim()Ljava/lang/String;

    move-result-object p0

    sget-object v0, Ljava/util/Locale;->US:Ljava/util/Locale;

    invoke-virtual {p0, v0}, Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)Ljava/lang/String;

    move-result-object p0

    .line 1748
    const-string v0, ".reverse"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 1749
    const-string p0, "reverse"

    return-object p0

    .line 1751
    :cond_0
    const-string v0, ".park"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_1

    .line 1752
    const-string p0, "park"

    return-object p0

    .line 1754
    :cond_1
    const-string v0, ".neutral"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_2

    .line 1755
    const-string p0, "neutral"

    return-object p0

    .line 1757
    :cond_2
    const-string v0, ".drive"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_3

    .line 1758
    const-string p0, "drive"

    return-object p0

    .line 1760
    :cond_3
    return-object p0
.end method

.method private noteVehicleDataReceived()V
    .locals 4

    .line 916
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    iput-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastVehicleDataAtMs:J

    .line 917
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    .line 918
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataWatchdogRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 919
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataWatchdogRunnable:Ljava/lang/Runnable;

    const-wide/16 v2, 0xbb8

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 920
    return-void
.end method

.method private offroadDoorColorPacket()[B
    .locals 3

    .line 763
    const-string v0, "zone1"

    const-string v1, "zone2"

    const-string v2, "offroadDoor"

    invoke-direct {p0, v2, v0, v2, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileColorPacket(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)[B

    move-result-object v0

    return-object v0
.end method

.method private offroadDoorZone1Brightness()I
    .locals 3

    .line 1241
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_0

    .line 1242
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone1Brightness()I

    move-result v0

    goto :goto_0

    .line 1243
    :cond_0
    const-string v0, "zone1"

    const/16 v1, 0x14

    const-string v2, "offroadDoor"

    invoke-direct {p0, v2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileBrightness(Ljava/lang/String;Ljava/lang/String;I)I

    move-result v0

    .line 1241
    :goto_0
    return v0
.end method

.method private offroadDoorZone2Brightness()I
    .locals 3

    .line 1247
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_0

    .line 1248
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result v0

    goto :goto_0

    .line 1249
    :cond_0
    const-string v0, "zone2"

    const/16 v1, 0x64

    const-string v2, "offroadDoor"

    invoke-direct {p0, v2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileBrightness(Ljava/lang/String;Ljava/lang/String;I)I

    move-result v0

    .line 1247
    :goto_0
    return v0
.end method

.method public static onCameraSpeedChanged(Landroid/content/Context;II)V
    .locals 2

    .line 608
    if-nez p0, :cond_0

    .line 609
    return-void

    .line 611
    :cond_0
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;

    move-result-object p0

    .line 612
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientLightController$21;

    invoke-direct {v1, p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController$21;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;II)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 618
    return-void
.end method

.method public static onGearText(Landroid/content/Context;Ljava/lang/String;)V
    .locals 2

    .line 582
    if-eqz p0, :cond_1

    if-nez p1, :cond_0

    goto :goto_0

    .line 585
    :cond_0
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;

    move-result-object p0

    .line 586
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientLightController$19;

    invoke-direct {v1, p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController$19;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 592
    return-void

    .line 583
    :cond_1
    :goto_0
    return-void
.end method

.method public static onOpenpilotPayload(Landroid/content/Context;Ljava/lang/String;)V
    .locals 12

    .line 539
    const-string v0, "doorOpen"

    const-string v1, "onroad"

    if-eqz p0, :cond_1

    if-nez p1, :cond_0

    goto :goto_1

    .line 543
    :cond_0
    :try_start_0
    new-instance v2, Lorg/json/JSONObject;

    invoke-direct {v2, p1}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    .line 544
    const-string p1, "gear"

    const-string v3, "gearShifter"

    const-string v4, ""

    invoke-virtual {v2, v3, v4}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v3

    invoke-virtual {v2, p1, v3}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v6

    .line 545
    invoke-virtual {v2, v1}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result v7

    .line 546
    invoke-virtual {v2, v0}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result v8

    .line 547
    const/4 p1, 0x1

    invoke-virtual {v2, v1, p1}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v9

    .line 548
    const/4 p1, 0x0

    invoke-virtual {v2, v0, p1}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v10

    .line 549
    const-string p1, "ambientOverride"

    invoke-virtual {v2, p1}, Lorg/json/JSONObject;->optJSONObject(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v11

    .line 550
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;

    move-result-object v5

    .line 551
    iget-object p0, v5, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    new-instance v4, Lcom/navdy/hud/app/ambient/AmbientLightController$18;

    invoke-direct/range {v4 .. v11}, Lcom/navdy/hud/app/ambient/AmbientLightController$18;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;ZZZZLorg/json/JSONObject;)V

    invoke-virtual {p0, v4}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 572
    goto :goto_0

    .line 570
    :catch_0
    move-exception v0

    move-object p0, v0

    .line 571
    const-string p1, "NavdyAmbient"

    const-string v0, "bad openpilot payload"

    invoke-static {p1, v0, p0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 573
    :goto_0
    return-void

    .line 540
    :cond_1
    :goto_1
    return-void
.end method

.method public static onOpenpilotPayload(Landroid/content/Context;Lorg/json/JSONObject;)V
    .locals 0

    .line 576
    if-eqz p1, :cond_0

    .line 577
    invoke-virtual {p1}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-static {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onOpenpilotPayload(Landroid/content/Context;Ljava/lang/String;)V

    .line 579
    :cond_0
    return-void
.end method

.method public static onOverspeedChanged(Landroid/content/Context;Z)V
    .locals 2

    .line 595
    if-nez p0, :cond_0

    .line 596
    return-void

    .line 598
    :cond_0
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;

    move-result-object p0

    .line 599
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientLightController$20;

    invoke-direct {v1, p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController$20;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 605
    return-void
.end method

.method private onroadDoorColorPacket()[B
    .locals 4

    .line 759
    const-string v0, "onroadDoor"

    const-string v1, "zone2"

    const-string v2, "driving"

    const-string v3, "zone1"

    invoke-direct {p0, v2, v3, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileColorPacket(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)[B

    move-result-object v0

    return-object v0
.end method

.method private onroadDoorZone2Brightness()I
    .locals 3

    .line 1236
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_0

    .line 1237
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result v0

    goto :goto_0

    :cond_0
    const-string v0, "zone2"

    const/16 v1, 0x64

    const-string v2, "onroadDoor"

    invoke-direct {p0, v2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileBrightness(Ljava/lang/String;Ljava/lang/String;I)I

    move-result v0

    .line 1236
    :goto_0
    return v0
.end method

.method private static parseIsoTimeMs(Ljava/lang/String;)J
    .locals 7

    .line 632
    const-wide/16 v0, 0x0

    if-eqz p0, :cond_3

    invoke-virtual {p0}, Ljava/lang/String;->length()I

    move-result v2

    if-nez v2, :cond_0

    goto :goto_2

    .line 635
    :cond_0
    const-string v2, "yyyy-MM-dd\'T\'HH:mm:ss.SSS\'Z\'"

    const-string v3, "yyyy-MM-dd\'T\'HH:mm:ss\'Z\'"

    filled-new-array {v2, v3}, [Ljava/lang/String;

    move-result-object v2

    .line 639
    const/4 v3, 0x0

    :goto_0
    const/4 v4, 0x2

    if-ge v3, v4, :cond_2

    aget-object v4, v2, v3

    .line 641
    :try_start_0
    new-instance v5, Ljava/text/SimpleDateFormat;

    sget-object v6, Ljava/util/Locale;->US:Ljava/util/Locale;

    invoke-direct {v5, v4, v6}, Ljava/text/SimpleDateFormat;-><init>(Ljava/lang/String;Ljava/util/Locale;)V

    .line 642
    const-string v4, "UTC"

    invoke-static {v4}, Ljava/util/TimeZone;->getTimeZone(Ljava/lang/String;)Ljava/util/TimeZone;

    move-result-object v4

    invoke-virtual {v5, v4}, Ljava/text/SimpleDateFormat;->setTimeZone(Ljava/util/TimeZone;)V

    .line 643
    invoke-virtual {v5, p0}, Ljava/text/SimpleDateFormat;->parse(Ljava/lang/String;)Ljava/util/Date;

    move-result-object v4

    .line 644
    if-eqz v4, :cond_1

    .line 645
    invoke-virtual {v4}, Ljava/util/Date;->getTime()J

    move-result-wide v0
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    return-wide v0

    .line 648
    :cond_1
    goto :goto_1

    .line 647
    :catch_0
    move-exception v4

    .line 639
    :goto_1
    add-int/lit8 v3, v3, 0x1

    goto :goto_0

    .line 650
    :cond_2
    return-wide v0

    .line 633
    :cond_3
    :goto_2
    return-wide v0
.end method

.method private profileBrightness(Ljava/lang/String;Ljava/lang/String;I)I
    .locals 1

    .line 720
    invoke-direct {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileZone(Ljava/lang/String;Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    const-string p2, "brightness"

    const/16 v0, 0x64

    invoke-static {p1, p2, p3, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->zoneValue(Lorg/json/JSONObject;Ljava/lang/String;II)I

    move-result p1

    return p1
.end method

.method private profileColorPacket(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)[B
    .locals 6

    .line 747
    invoke-direct {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileZone(Ljava/lang/String;Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    .line 748
    invoke-direct {p0, p3, p4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileZone(Ljava/lang/String;Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p2

    .line 749
    nop

    .line 750
    const/4 p3, 0x0

    const/16 p4, 0xff

    invoke-static {p1, p3, p4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v0

    const/4 v1, 0x1

    const/4 v2, 0x1

    invoke-static {p1, v2, p4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v1

    const/4 v3, 0x2

    invoke-static {p1, v3, p4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result p1

    .line 751
    invoke-static {p2, p3, p4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result p3

    invoke-static {p2, v2, p4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v4

    invoke-static {p2, v3, p4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v5

    .line 749
    move v2, p1

    move v3, p3

    invoke-static/range {v0 .. v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildColorPacket(IIIIII)[B

    move-result-object p1

    return-object p1
.end method

.method private profileDoorCloseDelayMs()J
    .locals 8

    .line 733
    const-wide/16 v4, 0x0

    const-wide/16 v6, 0x78

    const-string v1, "doorCloseDelaySeconds"

    const-wide/16 v2, 0x14

    move-object v0, p0

    invoke-direct/range {v0 .. v7}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileTimingMs(Ljava/lang/String;JJJ)J

    move-result-wide v1

    const-wide/16 v3, 0x3e8

    mul-long v1, v1, v3

    return-wide v1
.end method

.method private profileDoorMaxOnMs()J
    .locals 8

    .line 737
    const-wide/16 v4, 0x1

    const-wide/16 v6, 0x3c

    const-string v1, "doorMaxOnMinutes"

    const-wide/16 v2, 0x14

    move-object v0, p0

    invoke-direct/range {v0 .. v7}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileTimingMs(Ljava/lang/String;JJJ)J

    move-result-wide v1

    const-wide/32 v3, 0xea60

    mul-long v1, v1, v3

    return-wide v1
.end method

.method private profileExitCourtesyMs()J
    .locals 4

    .line 741
    nop

    .line 742
    const-string v0, "exitCourtesy"

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileSection(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v0

    const-string v1, "durationSeconds"

    const-wide/16 v2, 0x78

    invoke-virtual {v0, v1, v2, v3}, Lorg/json/JSONObject;->optLong(Ljava/lang/String;J)J

    move-result-wide v0

    const-wide/16 v2, 0x258

    invoke-static {v2, v3, v0, v1}, Ljava/lang/Math;->min(JJ)J

    move-result-wide v0

    .line 741
    const-wide/16 v2, 0x0

    invoke-static {v2, v3, v0, v1}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v0

    const-wide/16 v2, 0x3e8

    mul-long v0, v0, v2

    return-wide v0
.end method

.method private profileFadeMs()J
    .locals 8

    .line 729
    const-wide/16 v4, 0xc8

    const-wide/16 v6, 0x1388

    const-string v1, "fadeMilliseconds"

    const-wide/16 v2, 0x3e8

    move-object v0, p0

    invoke-direct/range {v0 .. v7}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileTimingMs(Ljava/lang/String;JJJ)J

    move-result-wide v1

    return-wide v1
.end method

.method private profileFeatureEnabled(Ljava/lang/String;Z)Z
    .locals 1

    .line 716
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileSection(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    const-string v0, "enabled"

    invoke-virtual {p1, v0, p2}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result p1

    return p1
.end method

.method private profileMasterEnabled()Z
    .locals 3

    .line 712
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mProfile:Lorg/json/JSONObject;

    const-string v1, "enabled"

    const/4 v2, 0x1

    invoke-virtual {v0, v1, v2}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v0

    return v0
.end method

.method private profileSection(Ljava/lang/String;)Lorg/json/JSONObject;
    .locals 1

    .line 702
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mProfile:Lorg/json/JSONObject;

    invoke-virtual {v0, p1}, Lorg/json/JSONObject;->optJSONObject(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    .line 703
    if-nez p1, :cond_0

    new-instance p1, Lorg/json/JSONObject;

    invoke-direct {p1}, Lorg/json/JSONObject;-><init>()V

    :cond_0
    return-object p1
.end method

.method private profileTimingMs(Ljava/lang/String;JJJ)J
    .locals 1

    .line 724
    nop

    .line 725
    const-string v0, "timing"

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileSection(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v0

    invoke-virtual {v0, p1, p2, p3}, Lorg/json/JSONObject;->optLong(Ljava/lang/String;J)J

    move-result-wide p1

    invoke-static {p6, p7, p1, p2}, Ljava/lang/Math;->min(JJ)J

    move-result-wide p1

    .line 724
    invoke-static {p4, p5, p1, p2}, Ljava/lang/Math;->max(JJ)J

    move-result-wide p1

    return-wide p1
.end method

.method private profileZone(Ljava/lang/String;Ljava/lang/String;)Lorg/json/JSONObject;
    .locals 0

    .line 707
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileSection(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    invoke-virtual {p1, p2}, Lorg/json/JSONObject;->optJSONObject(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    .line 708
    if-nez p1, :cond_0

    new-instance p1, Lorg/json/JSONObject;

    invoke-direct {p1}, Lorg/json/JSONObject;-><init>()V

    :cond_0
    return-object p1
.end method

.method private queueStartPacket()V
    .locals 2

    .line 1457
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStartQueued:Z

    if-eqz v0, :cond_0

    .line 1458
    return-void

    .line 1460
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_START:[B

    invoke-virtual {v1}, [B->clone()Ljava/lang/Object;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offerFirst(Ljava/lang/Object;)Z

    .line 1461
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStartQueued:Z

    .line 1462
    return-void
.end method

.method private readAckSettleIntervalMs()I
    .locals 3

    .line 1559
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

    .line 1513
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readScreenBrightness()I

    move-result v0

    .line 1514
    const/4 v1, 0x1

    const/16 v2, 0x10

    if-gt v0, v2, :cond_0

    .line 1515
    return v1

    .line 1517
    :cond_0
    const/16 v3, 0x29

    const/16 v4, 0x8

    if-gt v0, v3, :cond_1

    .line 1518
    nop

    .line 1519
    nop

    .line 1520
    sub-int/2addr v0, v2

    mul-int/lit8 v0, v0, 0x7

    add-int/lit8 v0, v0, 0xc

    div-int/lit8 v0, v0, 0x19

    add-int/2addr v0, v1

    .line 1523
    invoke-static {v0, v1, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v0

    return v0

    .line 1525
    :cond_1
    const/16 v1, 0x64

    const/16 v2, 0x32

    if-gt v0, v1, :cond_2

    .line 1526
    nop

    .line 1527
    nop

    .line 1528
    sub-int/2addr v0, v3

    mul-int/lit8 v0, v0, 0x2a

    add-int/lit8 v0, v0, 0x1d

    div-int/lit8 v0, v0, 0x3b

    add-int/2addr v0, v4

    .line 1531
    invoke-static {v0, v4, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v0

    return v0

    .line 1533
    :cond_2
    return v2
.end method

.method private readAmbientFrameStepMs()I
    .locals 2

    .line 1555
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientTransitionStepMs()I

    move-result v0

    mul-int/lit8 v0, v0, 0x2

    const/16 v1, 0xfa

    invoke-static {v1, v0}, Ljava/lang/Math;->min(II)I

    move-result v0

    return v0
.end method

.method private readAmbientTransitionStepMs()I
    .locals 5

    .line 1541
    const-string v0, "timing"

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileSection(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v0

    .line 1542
    const-string v1, "transitionUpdatesPerSecond"

    invoke-virtual {v0, v1}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result v2

    const/16 v3, 0xfa

    const/16 v4, 0x21

    if-eqz v2, :cond_0

    .line 1543
    const/16 v2, 0x1e

    invoke-virtual {v0, v1, v2}, Lorg/json/JSONObject;->optInt(Ljava/lang/String;I)I

    move-result v0

    const/4 v1, 0x5

    invoke-static {v0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v0

    .line 1544
    const/16 v1, 0x3e8

    div-int/2addr v1, v0

    .line 1545
    invoke-static {v3, v1}, Ljava/lang/Math;->min(II)I

    move-result v0

    .line 1544
    invoke-static {v4, v0}, Ljava/lang/Math;->max(II)I

    move-result v0

    return v0

    .line 1547
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v0

    const-string v1, "navdy_ambient_transition_step_ms"

    invoke-static {v0, v1, v4}, Landroid/provider/Settings$System;->getInt(Landroid/content/ContentResolver;Ljava/lang/String;I)I

    move-result v0

    invoke-static {v0, v4, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v0

    return v0
.end method

.method private readScreenBrightness()I
    .locals 3

    .line 1537
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

.method private rememberColorPacket([B)V
    .locals 2

    .line 1600
    const/4 v0, 0x5

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Red:I

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result v0

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Red:I

    .line 1601
    const/4 v0, 0x6

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Green:I

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result v0

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Green:I

    .line 1602
    const/4 v0, 0x7

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Blue:I

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result v0

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Blue:I

    .line 1603
    const/16 v0, 0x8

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Red:I

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result v0

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Red:I

    .line 1604
    const/16 v0, 0x9

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Green:I

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result v0

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Green:I

    .line 1605
    const/16 v0, 0xa

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Blue:I

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Blue:I

    .line 1606
    return-void
.end method

.method private removePendingAmbientStatePackets()V
    .locals 4

    .line 1489
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->isEmpty()Z

    move-result v0

    if-eqz v0, :cond_0

    .line 1490
    return-void

    .line 1492
    :cond_0
    new-instance v0, Ljava/util/ArrayDeque;

    invoke-direct {v0}, Ljava/util/ArrayDeque;-><init>()V

    .line 1493
    :goto_0
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1}, Ljava/util/ArrayDeque;->isEmpty()Z

    move-result v1

    if-nez v1, :cond_3

    .line 1494
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1}, Ljava/util/ArrayDeque;->poll()Ljava/lang/Object;

    move-result-object v1

    check-cast v1, [B

    .line 1495
    if-eqz v1, :cond_2

    array-length v2, v1

    const/4 v3, 0x2

    if-lt v2, v3, :cond_1

    const/4 v2, 0x1

    aget-byte v2, v1, v2

    const/16 v3, -0x73

    if-eq v2, v3, :cond_2

    .line 1496
    :cond_1
    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1498
    :cond_2
    goto :goto_0

    .line 1499
    :cond_3
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1, v0}, Ljava/util/ArrayDeque;->addAll(Ljava/util/Collection;)Z

    .line 1500
    return-void
.end method

.method private requestCameraSpeed(II)V
    .locals 0

    .line 621
    if-lez p2, :cond_2

    if-gt p1, p2, :cond_0

    goto :goto_0

    .line 623
    :cond_0
    add-int/lit8 p2, p2, 0x2

    if-lt p1, p2, :cond_1

    .line 624
    const/4 p1, 0x1

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestOverspeed(Z)V

    goto :goto_1

    .line 627
    :cond_1
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestOverspeed(Z)V

    goto :goto_1

    .line 622
    :cond_2
    :goto_0
    const/4 p1, 0x0

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestOverspeed(Z)V

    .line 629
    :goto_1
    return-void
.end method

.method private requestOverspeed(Z)V
    .locals 8

    .line 856
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileMasterEnabled()Z

    move-result v0

    if-eqz v0, :cond_0

    const-string v0, "overspeed"

    const/4 v1, 0x1

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result v0

    if-eqz v0, :cond_0

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    if-eqz v0, :cond_0

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-nez v0, :cond_0

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_0

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-eqz v0, :cond_1

    .line 858
    :cond_0
    const/4 p1, 0x0

    .line 860
    :cond_1
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mRequestedOverspeed:Z

    if-ne v0, p1, :cond_2

    .line 861
    return-void

    .line 863
    :cond_2
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mRequestedOverspeed:Z

    .line 864
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedStateRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 865
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-ne v0, p1, :cond_3

    .line 866
    return-void

    .line 869
    :cond_3
    if-eqz p1, :cond_4

    const-wide/16 v0, 0x3e8

    goto :goto_0

    :cond_4
    const-wide/16 v0, 0x7d0

    .line 870
    :goto_0
    const-wide/16 v2, 0x0

    if-nez p1, :cond_5

    iget-wide v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActivatedAtMs:J

    cmp-long v6, v4, v2

    if-lez v6, :cond_5

    .line 871
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v4

    iget-wide v6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActivatedAtMs:J

    sub-long/2addr v4, v6

    .line 872
    const-wide/16 v6, 0xbb8

    sub-long/2addr v6, v4

    invoke-static {v0, v1, v6, v7}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v0

    .line 874
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

    .line 875
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedStateRunnable:Ljava/lang/Runnable;

    invoke-static {v2, v3, v0, v1}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v0

    invoke-virtual {p1, v4, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 876
    return-void
.end method

.method private restoreActiveStateAfterConnect()V
    .locals 4

    .line 1465
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->removePendingAmbientStatePackets()V

    .line 1466
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-eqz v0, :cond_0

    .line 1467
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_OFF:[B

    invoke-virtual {v1}, [B->clone()Ljava/lang/Object;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1468
    return-void

    .line 1470
    :cond_0
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-eqz v0, :cond_1

    .line 1471
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBlink()V

    .line 1472
    return-void

    .line 1474
    :cond_1
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    if-eqz v0, :cond_3

    .line 1475
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->activeStateColorPacket()[B

    move-result-object v0

    .line 1476
    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->rememberColorPacket([B)V

    .line 1477
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, [B->clone()Ljava/lang/Object;

    move-result-object v0

    invoke-virtual {v1, v0}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1478
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_2

    .line 1479
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    goto :goto_0

    .line 1481
    :cond_2
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    const/4 v3, 0x1

    invoke-static {v3, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildBrightnessPacket(ZII)[B

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1483
    :goto_0
    return-void

    .line 1485
    :cond_3
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_OFF:[B

    invoke-virtual {v1}, [B->clone()Ljava/lang/Object;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1486
    return-void
.end method

.method private static safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;
    .locals 1

    .line 1739
    const-string v0, ""

    :try_start_0
    invoke-virtual {p0}, Landroid/bluetooth/BluetoothDevice;->getName()Ljava/lang/String;

    move-result-object p0
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 1740
    if-nez p0, :cond_0

    goto :goto_0

    :cond_0
    move-object v0, p0

    :goto_0
    return-object v0

    .line 1741
    :catch_0
    move-exception p0

    .line 1742
    return-object v0
.end method

.method private static scanRecordContainsAmbientUuid([B)Z
    .locals 5

    .line 1716
    const/4 v0, 0x0

    if-nez p0, :cond_0

    .line 1717
    return v0

    .line 1719
    :cond_0
    const/4 v1, 0x0

    :goto_0
    add-int/lit8 v2, v1, 0x1

    array-length v3, p0

    if-ge v2, v3, :cond_4

    .line 1720
    aget-byte v1, p0, v1

    and-int/lit16 v1, v1, 0xff

    .line 1721
    aget-byte v3, p0, v2

    and-int/lit16 v3, v3, 0xff

    .line 1722
    if-eqz v1, :cond_1

    const/16 v4, 0x30

    if-ne v1, v4, :cond_2

    :cond_1
    const/16 v1, 0xae

    if-eq v3, v1, :cond_3

    const/16 v1, 0xaf

    if-ne v3, v1, :cond_2

    goto :goto_1

    .line 1719
    :cond_2
    move v1, v2

    goto :goto_0

    .line 1723
    :cond_3
    :goto_1
    const/4 p0, 0x1

    return p0

    .line 1726
    :cond_4
    return v0
.end method

.method private scheduleReconnect()V
    .locals 2

    .line 1358
    const-wide/16 v0, 0x1388

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    .line 1359
    return-void
.end method

.method private scheduleReconnect(J)V
    .locals 4

    .line 1362
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

    .line 1365
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1366
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectScheduled:Z

    .line 1367
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

    .line 1368
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectRunnable:Ljava/lang/Runnable;

    const-wide/16 v2, 0x0

    invoke-static {v2, v3, p1, p2}, Ljava/lang/Math;->max(JJ)J

    move-result-wide p1

    invoke-virtual {v0, v1, p1, p2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 1369
    return-void

    .line 1363
    :cond_1
    :goto_0
    return-void
.end method

.method private sendAmbientFrame([B[B)V
    .locals 2

    .line 1191
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->removePendingAmbientStatePackets()V

    .line 1192
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->size()I

    move-result v0

    const/16 v1, 0x12

    if-le v0, v1, :cond_0

    .line 1193
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->poll()Ljava/lang/Object;

    .line 1195
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {p1}, [B->clone()Ljava/lang/Object;

    move-result-object p1

    invoke-virtual {v0, p1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1196
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {p2}, [B->clone()Ljava/lang/Object;

    move-result-object p2

    invoke-virtual {p1, p2}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1197
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectIfNeeded()V

    .line 1198
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->flushNext()V

    .line 1199
    return-void
.end method

.method private sendPacket([B)V
    .locals 2

    .line 1281
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isColorPacket([B)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 1282
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->rememberColorPacket([B)V

    .line 1284
    :cond_0
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isBrightnessPacket([B)Z

    move-result v0

    if-eqz v0, :cond_1

    .line 1285
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->coalescePendingBrightnessPackets()V

    .line 1287
    :cond_1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->size()I

    move-result v0

    const/16 v1, 0x14

    if-le v0, v1, :cond_2

    .line 1288
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->poll()Ljava/lang/Object;

    .line 1290
    :cond_2
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {p1}, [B->clone()Ljava/lang/Object;

    move-result-object p1

    invoke-virtual {v0, p1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1291
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectIfNeeded()V

    .line 1292
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->flushNext()V

    .line 1293
    return-void
.end method

.method private setAmbientOverride(Lorg/json/JSONObject;)V
    .locals 11

    .line 787
    const-string v0, "mode"

    const-string v1, "manual"

    invoke-virtual {p1, v0, v1}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    .line 788
    const-string v2, "profile"

    invoke-virtual {v2, v0}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    move-result v3

    if-eqz v3, :cond_0

    .line 789
    invoke-virtual {p1, v2}, Lorg/json/JSONObject;->optJSONObject(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setAmbientProfile(Lorg/json/JSONObject;)V

    .line 790
    return-void

    .line 792
    :cond_0
    const-string v2, "auto"

    invoke-virtual {v2, v0}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    move-result v2

    if-eqz v2, :cond_1

    .line 793
    const-string p1, "auto command"

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clearManualOverride(Ljava/lang/String;)V

    .line 794
    return-void

    .line 796
    :cond_1
    invoke-virtual {v1, v0}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    move-result v0

    if-nez v0, :cond_2

    .line 797
    return-void

    .line 799
    :cond_2
    const-string v0, "id"

    const-string v1, ""

    invoke-virtual {p1, v0, v1}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    .line 800
    iget-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v2, :cond_3

    invoke-virtual {v0}, Ljava/lang/String;->length()I

    move-result v2

    if-lez v2, :cond_3

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideId:Ljava/lang/String;

    invoke-virtual {v0, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v2

    if-eqz v2, :cond_3

    .line 801
    return-void

    .line 803
    :cond_3
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v2

    .line 804
    const-string v4, "expiresAt"

    invoke-virtual {p1, v4, v1}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->parseIsoTimeMs(Ljava/lang/String;)J

    move-result-wide v4

    .line 805
    cmp-long v1, v4, v2

    if-gtz v1, :cond_4

    .line 806
    const-string p1, "stale command"

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clearManualOverride(Ljava/lang/String;)V

    .line 807
    return-void

    .line 809
    :cond_4
    const-string v1, "zone1"

    invoke-virtual {p1, v1}, Lorg/json/JSONObject;->optJSONObject(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v1

    .line 810
    const-string v6, "zone2"

    invoke-virtual {p1, v6}, Lorg/json/JSONObject;->optJSONObject(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    .line 811
    if-eqz v1, :cond_7

    if-nez p1, :cond_5

    goto/16 :goto_0

    .line 814
    :cond_5
    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideId:Ljava/lang/String;

    .line 815
    const-string v6, "enabled"

    const/4 v7, 0x1

    invoke-virtual {v1, v6, v7}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v8

    iput-boolean v8, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Enabled:Z

    .line 816
    invoke-virtual {p1, v6, v7}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v6

    iput-boolean v6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Enabled:Z

    .line 817
    const/4 v6, 0x0

    const/16 v8, 0xff

    invoke-static {v1, v6, v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v9

    iput v9, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Red:I

    .line 818
    invoke-static {v1, v7, v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v9

    iput v9, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Green:I

    .line 819
    const/4 v9, 0x2

    invoke-static {v1, v9, v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v10

    iput v10, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Blue:I

    .line 820
    invoke-static {p1, v6, v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v6

    iput v6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Red:I

    .line 821
    invoke-static {p1, v7, v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v6

    iput v6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Green:I

    .line 822
    invoke-static {p1, v9, v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v6

    iput v6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Blue:I

    .line 823
    const/16 v6, 0x14

    const-string v8, "brightness"

    const/16 v9, 0x64

    invoke-static {v1, v8, v6, v9}, Lcom/navdy/hud/app/ambient/AmbientLightController;->zoneValue(Lorg/json/JSONObject;Ljava/lang/String;II)I

    move-result v1

    iput v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Brightness:I

    .line 824
    const/16 v1, 0x28

    invoke-static {p1, v8, v1, v9}, Lcom/navdy/hud/app/ambient/AmbientLightController;->zoneValue(Lorg/json/JSONObject;Ljava/lang/String;II)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Brightness:I

    .line 825
    const-wide/32 v8, 0x124f80

    add-long/2addr v8, v2

    invoke-static {v4, v5, v8, v9}, Ljava/lang/Math;->min(JJ)J

    move-result-wide v4

    iput-wide v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiresAtMs:J

    .line 826
    iput-boolean v7, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    .line 827
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->cancelOffroadTimers()V

    .line 828
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiryRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 829
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiryRunnable:Ljava/lang/Runnable;

    iget-wide v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiresAtMs:J

    sub-long/2addr v4, v2

    .line 830
    const-wide/16 v2, 0x1

    invoke-static {v2, v3, v4, v5}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v2

    .line 829
    invoke-virtual {p1, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 831
    new-instance p1, Ljava/lang/StringBuilder;

    invoke-direct {p1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "manual ambient override id="

    invoke-virtual {p1, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    const-string v0, "NavdyAmbient"

    invoke-static {v0, p1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 832
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez p1, :cond_6

    .line 833
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->applyVehicleStateTargets()V

    .line 835
    :cond_6
    return-void

    .line 812
    :cond_7
    :goto_0
    return-void
.end method

.method private setAmbientProfile(Lorg/json/JSONObject;)V
    .locals 2

    .line 680
    if-nez p1, :cond_0

    .line 681
    return-void

    .line 683
    :cond_0
    invoke-virtual {p1}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mProfile:Lorg/json/JSONObject;

    invoke-virtual {v1}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-nez v0, :cond_1

    .line 684
    return-void

    .line 686
    :cond_1
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mProfile:Lorg/json/JSONObject;

    .line 687
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    .line 688
    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v0

    invoke-virtual {p1}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object p1

    .line 687
    const-string v1, "navdy_ambient_profile_json"

    invoke-static {v0, v1, p1}, Landroid/provider/Settings$System;->putString(Landroid/content/ContentResolver;Ljava/lang/String;Ljava/lang/String;)Z

    .line 689
    const/4 p1, 0x0

    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    .line 690
    const-wide/16 v0, 0x0

    iput-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiresAtMs:J

    .line 691
    const-string p1, ""

    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideId:Ljava/lang/String;

    .line 692
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiryRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 693
    const-string p1, "NavdyAmbient"

    const-string v0, "ambient profile saved"

    invoke-static {p1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 694
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileMasterEnabled()Z

    move-result p1

    if-nez p1, :cond_2

    .line 695
    const-string p1, "profile disabled"

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    goto :goto_0

    .line 696
    :cond_2
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez p1, :cond_3

    .line 697
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->applyVehicleStateTargets()V

    .line 699
    :cond_3
    :goto_0
    return-void
.end method

.method private setGearText(Ljava/lang/String;)V
    .locals 3

    .line 879
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalizeGear(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    .line 880
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastGear:Ljava/lang/String;

    invoke-virtual {p1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 881
    return-void

    .line 883
    :cond_0
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastGear:Ljava/lang/String;

    .line 884
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

    .line 886
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isReverse(Ljava/lang/String;)Z

    move-result v0

    const/4 v1, 0x1

    if-eqz v0, :cond_2

    .line 887
    const-string p1, "reverseOff"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result p1

    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    .line 888
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez p1, :cond_1

    .line 889
    return-void

    .line 891
    :cond_1
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 892
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBrightnessSync()V

    .line 893
    const-string p1, "reverse"

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    .line 894
    return-void

    .line 897
    :cond_2
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isDriveGear(Ljava/lang/String;)Z

    move-result p1

    if-eqz p1, :cond_5

    .line 898
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    .line 899
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    .line 900
    if-eqz p1, :cond_4

    .line 901
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    if-eqz p1, :cond_3

    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz p1, :cond_3

    .line 902
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    goto :goto_0

    .line 904
    :cond_3
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->applyVehicleStateTargets()V

    goto :goto_0

    .line 906
    :cond_4
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    if-nez p1, :cond_5

    .line 907
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    .line 908
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 909
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    .line 910
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone1Brightness()I

    move-result p1

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result v0

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v1

    invoke-direct {p0, p1, v0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    .line 913
    :cond_5
    :goto_0
    return-void
.end method

.method private setOverspeed(Z)V
    .locals 2

    .line 1054
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-ne v0, p1, :cond_0

    .line 1055
    return-void

    .line 1057
    :cond_0
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    .line 1058
    if-eqz p1, :cond_1

    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    goto :goto_0

    :cond_1
    const-wide/16 v0, 0x0

    :goto_0
    iput-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActivatedAtMs:J

    .line 1059
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

    .line 1060
    if-eqz p1, :cond_2

    .line 1061
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz p1, :cond_4

    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez p1, :cond_4

    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-nez p1, :cond_4

    .line 1062
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBlink()V

    goto :goto_1

    .line 1065
    :cond_2
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez p1, :cond_3

    .line 1066
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->beginRestoreFade()V

    goto :goto_1

    .line 1068
    :cond_3
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 1071
    :cond_4
    :goto_1
    return-void
.end method

.method private setVehicleState(ZZ)V
    .locals 7

    .line 923
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    .line 924
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

    .line 925
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

    .line 926
    :goto_3
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    .line 927
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    .line 928
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    .line 929
    iput-boolean p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    .line 930
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->updateCpuWakeLock()V

    .line 931
    if-nez v3, :cond_4

    if-eqz v4, :cond_5

    .line 932
    :cond_4
    new-instance v5, Ljava/lang/StringBuilder;

    invoke-direct {v5}, Ljava/lang/StringBuilder;-><init>()V

    const-string v6, "vehicle state onroad="

    invoke-virtual {v5, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v5

    invoke-virtual {v5, p1}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v5

    const-string v6, " doorOpen="

    invoke-virtual {v5, v6}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v5

    invoke-virtual {v5, p2}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v5

    invoke-virtual {v5}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v5

    const-string v6, "NavdyAmbient"

    invoke-static {v6, v5}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 935
    :cond_5
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileMasterEnabled()Z

    move-result v5

    if-nez v5, :cond_6

    iget-boolean v5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-nez v5, :cond_6

    .line 936
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->cancelOffroadTimers()V

    .line 937
    const-string p1, "profile disabled"

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    .line 938
    return-void

    .line 941
    :cond_6
    if-eqz p1, :cond_9

    .line 942
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mExitCourtesyActive:Z

    .line 943
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->cancelOffroadTimers()V

    .line 944
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    .line 945
    if-eqz v3, :cond_7

    .line 946
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    goto :goto_4

    .line 947
    :cond_7
    if-eqz v4, :cond_8

    .line 948
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->applyVehicleStateTargets()V

    .line 950
    :cond_8
    :goto_4
    return-void

    .line 953
    :cond_9
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBrightnessSync()V

    .line 954
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mRequestedOverspeed:Z

    .line 955
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedStateRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, v5}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 956
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-eqz p1, :cond_a

    .line 957
    invoke-direct {p0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setOverspeed(Z)V

    .line 960
    :cond_a
    if-eqz p2, :cond_10

    .line 961
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mExitCourtesyActive:Z

    .line 962
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 963
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 964
    const-string p1, "offroadDoor"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result p1

    if-nez p1, :cond_b

    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-nez p1, :cond_b

    .line 965
    const-string p1, "offroad door profile disabled"

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    .line 966
    return-void

    .line 968
    :cond_b
    if-nez v4, :cond_c

    if-eqz v3, :cond_d

    .line 969
    :cond_c
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    .line 970
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 971
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxRunnable:Ljava/lang/Runnable;

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileDoorMaxOnMs()J

    move-result-wide v0

    invoke-virtual {p1, p2, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 973
    :cond_d
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    if-nez p1, :cond_f

    if-nez v4, :cond_e

    if-eqz v3, :cond_f

    .line 974
    :cond_e
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->offroadDoorZone1Brightness()I

    move-result p1

    .line 975
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->offroadDoorZone2Brightness()I

    move-result p2

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v0

    .line 974
    invoke-direct {p0, p1, p2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    .line 977
    :cond_f
    return-void

    .line 980
    :cond_10
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz p1, :cond_11

    .line 981
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->cancelOffroadTimers()V

    .line 982
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone1Brightness()I

    move-result p1

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result p2

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v0

    invoke-direct {p0, p1, p2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    .line 983
    return-void

    .line 986
    :cond_11
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 987
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    .line 988
    if-eqz v4, :cond_12

    if-eqz v0, :cond_12

    .line 989
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 990
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 991
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileDoorCloseDelayMs()J

    move-result-wide v0

    invoke-virtual {p1, p2, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    goto :goto_5

    .line 992
    :cond_12
    if-eqz v0, :cond_14

    if-eqz v3, :cond_14

    .line 993
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 994
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 995
    const-string p1, "exitCourtesy"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result p1

    if-eqz p1, :cond_13

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileExitCourtesyMs()J

    move-result-wide p1

    const-wide/16 v3, 0x0

    cmp-long v0, p1, v3

    if-lez v0, :cond_13

    .line 996
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mExitCourtesyActive:Z

    .line 997
    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->exitCourtesyZone2Brightness()I

    move-result p2

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v0

    invoke-direct {p0, p1, p2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    .line 998
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileExitCourtesyMs()J

    move-result-wide v0

    invoke-virtual {p1, p2, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    goto :goto_5

    .line 1000
    :cond_13
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mExitCourtesyActive:Z

    .line 1001
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide p1

    invoke-direct {p0, v2, v2, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    goto :goto_5

    .line 1003
    :cond_14
    if-nez v0, :cond_15

    .line 1004
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1005
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1006
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    const-wide/32 v0, 0xea60

    invoke-virtual {p1, p2, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 1008
    :cond_15
    :goto_5
    return-void
.end method

.method private startAmbientFade(IIJ)V
    .locals 2

    .line 1137
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1138
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->removePendingAmbientStatePackets()V

    .line 1139
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1:I

    .line 1140
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2:I

    .line 1141
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Red:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1Red:I

    .line 1142
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Green:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1Green:I

    .line 1143
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Blue:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1Blue:I

    .line 1144
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Red:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2Red:I

    .line 1145
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Green:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2Green:I

    .line 1146
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Blue:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2Blue:I

    .line 1147
    const/4 v0, 0x0

    const/16 v1, 0x64

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    .line 1148
    invoke-static {p2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    .line 1149
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->activeStateColorPacket()[B

    move-result-object p1

    .line 1150
    const/4 p2, 0x5

    const/16 v0, 0xff

    invoke-static {p1, p2, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1Red:I

    .line 1151
    const/4 p2, 0x6

    invoke-static {p1, p2, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1Green:I

    .line 1152
    const/4 p2, 0x7

    invoke-static {p1, p2, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1Blue:I

    .line 1153
    const/16 p2, 0x8

    invoke-static {p1, p2, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2Red:I

    .line 1154
    const/16 p2, 0x9

    invoke-static {p1, p2, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2Green:I

    .line 1155
    const/16 p2, 0xa

    invoke-static {p1, p2, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2Blue:I

    .line 1156
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide p1

    iput-wide p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartedAtMs:J

    .line 1157
    const-wide/16 p1, 0x0

    invoke-static {p1, p2, p3, p4}, Ljava/lang/Math;->max(JJ)J

    move-result-wide p3

    iput-wide p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeDurationMs:J

    .line 1158
    iget p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    if-gtz p3, :cond_0

    iget p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    if-lez p3, :cond_1

    .line 1159
    :cond_0
    const/4 p3, 0x1

    iput-boolean p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 1161
    :cond_1
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientFrameStepMs()I

    move-result p3

    int-to-long p3, p3

    iget-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeDurationMs:J

    invoke-static {p3, p4, v0, v1}, Ljava/lang/Math;->min(JJ)J

    move-result-wide p3

    .line 1162
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeRunnable:Ljava/lang/Runnable;

    invoke-static {p1, p2, p3, p4}, Ljava/lang/Math;->max(JJ)J

    move-result-wide p1

    invoke-virtual {v0, v1, p1, p2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 1163
    return-void
.end method

.method private startBlink()V
    .locals 2

    .line 1074
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-eqz v0, :cond_0

    goto :goto_0

    .line 1077
    :cond_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 1078
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 1079
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    .line 1080
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBlinkRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 1081
    return-void

    .line 1075
    :cond_1
    :goto_0
    return-void
.end method

.method private startBrightnessSync()V
    .locals 4

    .line 1104
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1105
    const/4 v0, 0x1

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->syncAmbientBrightness(Z)V

    .line 1106
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    const-wide/16 v2, 0x1388

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 1107
    return-void
.end method

.method private stopBlink()V
    .locals 2

    .line 1084
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBlinkRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1085
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningAnimationStarted:Z

    .line 1086
    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLowLightWarning:Z

    .line 1087
    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDayWarningDimmed:Z

    .line 1088
    return-void
.end method

.method private stopBrightnessSync()V
    .locals 2

    .line 1110
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1111
    const/4 v0, -0x1

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 1112
    return-void
.end method

.method private stopScan()V
    .locals 2

    .line 1420
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    if-eqz v0, :cond_1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    if-nez v0, :cond_0

    goto :goto_0

    .line 1423
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanCallback:Landroid/bluetooth/BluetoothAdapter$LeScanCallback;

    invoke-virtual {v0, v1}, Landroid/bluetooth/BluetoothAdapter;->stopLeScan(Landroid/bluetooth/BluetoothAdapter$LeScanCallback;)V

    .line 1424
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    .line 1425
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStopScanRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1426
    const-string v0, "NavdyAmbient"

    const-string v1, "ambient scan stop"

    invoke-static {v0, v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 1427
    return-void

    .line 1421
    :cond_1
    :goto_0
    return-void
.end method

.method private syncAmbientBrightness(Z)V
    .locals 4

    .line 1115
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_6

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez v0, :cond_6

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-eqz v0, :cond_0

    goto :goto_1

    .line 1118
    :cond_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone1Brightness()I

    move-result v0

    .line 1119
    iget-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningAnimationStarted:Z

    if-eqz v1, :cond_1

    .line 1120
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 1121
    return-void

    .line 1123
    :cond_1
    if-nez p1, :cond_2

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    if-ltz v1, :cond_2

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    sub-int v1, v0, v1

    .line 1124
    invoke-static {v1}, Ljava/lang/Math;->abs(I)I

    move-result v1

    const/4 v2, 0x2

    if-ge v1, v2, :cond_2

    .line 1125
    return-void

    .line 1127
    :cond_2
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 1128
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

    .line 1129
    iget-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eqz v1, :cond_3

    const-string v1, "onroadDoor"

    const/4 v2, 0x1

    invoke-direct {p0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result v1

    if-eqz v1, :cond_3

    .line 1130
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onroadDoorZone2Brightness()I

    move-result v1

    goto :goto_0

    :cond_3
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result v1

    .line 1131
    :goto_0
    if-nez p1, :cond_4

    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    if-ne v0, p1, :cond_4

    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    if-eq v1, p1, :cond_5

    .line 1132
    :cond_4
    const-wide/16 v2, 0x3e8

    invoke-direct {p0, v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    .line 1134
    :cond_5
    return-void

    .line 1116
    :cond_6
    :goto_1
    return-void
.end method

.method private updateCpuWakeLock()V
    .locals 3

    .line 1011
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    if-nez v0, :cond_0

    .line 1012
    return-void

    .line 1014
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

    .line 1015
    :goto_0
    const-string v1, "NavdyAmbient"

    if-eqz v0, :cond_2

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    invoke-virtual {v2}, Landroid/os/PowerManager$WakeLock;->isHeld()Z

    move-result v2

    if-nez v2, :cond_2

    .line 1016
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    invoke-virtual {v0}, Landroid/os/PowerManager$WakeLock;->acquire()V

    .line 1017
    const-string v0, "offroad ambient CPU wake lock acquired"

    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    goto :goto_1

    .line 1018
    :cond_2
    if-nez v0, :cond_3

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    invoke-virtual {v0}, Landroid/os/PowerManager$WakeLock;->isHeld()Z

    move-result v0

    if-eqz v0, :cond_3

    .line 1019
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    invoke-virtual {v0}, Landroid/os/PowerManager$WakeLock;->release()V

    .line 1020
    const-string v0, "offroad ambient CPU wake lock released"

    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 1022
    :cond_3
    :goto_1
    return-void
.end method

.method private static usesPacedWrite([B)Z
    .locals 1

    .line 1584
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

.method private warningColorPacket()[B
    .locals 11

    .line 1268
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_0

    .line 1269
    iget v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Red:I

    iget v5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Green:I

    iget v6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Blue:I

    const/16 v1, 0xff

    const/4 v2, 0x0

    const/4 v3, 0x0

    invoke-static/range {v1 .. v6}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildColorPacket(IIIIII)[B

    move-result-object v0

    return-object v0

    .line 1272
    :cond_0
    const-string v0, "overspeed"

    const-string v1, "zone1"

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileZone(Ljava/lang/String;Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v0

    .line 1273
    iget-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    const-string v2, "zone2"

    const/4 v3, 0x1

    if-eqz v1, :cond_1

    const-string v1, "onroadDoor"

    invoke-direct {p0, v1, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result v4

    if-eqz v4, :cond_1

    .line 1274
    goto :goto_0

    :cond_1
    const-string v1, "driving"

    :goto_0
    invoke-direct {p0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileZone(Ljava/lang/String;Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v1

    .line 1275
    nop

    .line 1276
    const/4 v2, 0x0

    const/16 v4, 0xff

    invoke-static {v0, v2, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v5

    invoke-static {v0, v3, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v6

    const/4 v7, 0x2

    invoke-static {v0, v7, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v0

    .line 1277
    invoke-static {v1, v2, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v8

    invoke-static {v1, v3, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v9

    invoke-static {v1, v7, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v10

    .line 1275
    move v7, v0

    invoke-static/range {v5 .. v10}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildColorPacket(IIIIII)[B

    move-result-object v0

    return-object v0
.end method

.method private warningZone2Brightness()I
    .locals 2

    .line 1213
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eqz v0, :cond_0

    const-string v0, "onroadDoor"

    const/4 v1, 0x1

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 1214
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onroadDoorZone2Brightness()I

    move-result v0

    goto :goto_0

    :cond_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result v0

    .line 1213
    :goto_0
    return v0
.end method

.method private writeAck()V
    .locals 3

    .line 1503
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    if-eqz v0, :cond_1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    if-nez v0, :cond_0

    goto :goto_0

    .line 1506
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_ACK:[B

    invoke-virtual {v0, v1}, Landroid/bluetooth/BluetoothGattCharacteristic;->setValue([B)Z

    .line 1507
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->configureWriteCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)V

    .line 1508
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v0, v1}, Landroid/bluetooth/BluetoothGatt;->writeCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result v0

    .line 1509
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

    .line 1510
    return-void

    .line 1504
    :cond_1
    :goto_0
    return-void
.end method

.method private static zoneValue(Lorg/json/JSONObject;Ljava/lang/String;II)I
    .locals 0

    .line 654
    if-nez p0, :cond_0

    goto :goto_0

    :cond_0
    invoke-virtual {p0, p1, p2}, Lorg/json/JSONObject;->optInt(Ljava/lang/String;I)I

    move-result p0

    const/4 p1, 0x0

    invoke-static {p0, p1, p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p2

    :goto_0
    return p2
.end method
