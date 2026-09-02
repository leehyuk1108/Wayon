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

.field private final mWarningStepStartRunnable:Ljava/lang/Runnable;

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

    .line 530
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

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningStepStartRunnable:Ljava/lang/Runnable;

    .line 309
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$9;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$9;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    .line 322
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$10;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$10;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    .line 334
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$11;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$11;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mFlushAfterAckRunnable:Ljava/lang/Runnable;

    .line 342
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$12;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$12;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    .line 353
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$13;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$13;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeRunnable:Ljava/lang/Runnable;

    .line 383
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$14;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$14;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    .line 397
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$15;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$15;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxRunnable:Ljava/lang/Runnable;

    .line 408
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$16;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$16;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    .line 422
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$17;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$17;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiryRunnable:Ljava/lang/Runnable;

    .line 431
    new-instance v0, Lcom/navdy/hud/app/ambient/AmbientLightController$18;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController$18;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataWatchdogRunnable:Ljava/lang/Runnable;

    .line 492
    const/16 v0, 0xff

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Red:I

    .line 493
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Green:I

    .line 494
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Blue:I

    .line 495
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Red:I

    .line 496
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Green:I

    .line 497
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Blue:I

    .line 512
    const/4 v1, -0x1

    iput v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 513
    const-string v1, ""

    iput-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastGear:Ljava/lang/String;

    .line 517
    iput-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideId:Ljava/lang/String;

    .line 518
    const/4 v1, 0x1

    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Enabled:Z

    .line 519
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Enabled:Z

    .line 520
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Red:I

    .line 521
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Green:I

    .line 522
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Blue:I

    .line 523
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Red:I

    .line 524
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Green:I

    .line 525
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Blue:I

    .line 526
    const/16 v0, 0x14

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Brightness:I

    .line 527
    const/16 v0, 0x28

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Brightness:I

    .line 528
    new-instance v0, Lorg/json/JSONObject;

    invoke-direct {v0}, Lorg/json/JSONObject;-><init>()V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mProfile:Lorg/json/JSONObject;

    .line 531
    invoke-virtual {p1}, Landroid/content/Context;->getApplicationContext()Landroid/content/Context;

    move-result-object p1

    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    .line 532
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->loadAmbientProfile()V

    .line 533
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    const-string v0, "power"

    invoke-virtual {p1, v0}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object p1

    check-cast p1, Landroid/os/PowerManager;

    .line 534
    if-nez p1, :cond_0

    const/4 p1, 0x0

    goto :goto_0

    .line 535
    :cond_0
    const-string v0, "NavdyAmbient:OffroadController"

    invoke-virtual {p1, v1, v0}, Landroid/os/PowerManager;->newWakeLock(ILjava/lang/String;)Landroid/os/PowerManager$WakeLock;

    move-result-object p1

    :goto_0
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    .line 536
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    if-eqz p1, :cond_1

    .line 537
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    const/4 v0, 0x0

    invoke-virtual {p1, v0}, Landroid/os/PowerManager$WakeLock;->setReferenceCounted(Z)V

    .line 539
    :cond_1
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    iput-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastVehicleDataAtMs:J

    .line 540
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataWatchdogRunnable:Ljava/lang/Runnable;

    const-wide/16 v1, 0xbb8

    invoke-virtual {p1, v0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 541
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

.method static synthetic access$10000(Lcom/navdy/hud/app/ambient/AmbientLightController;II)V
    .locals 0

    .line 30
    invoke-direct {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestCameraSpeed(II)V

    return-void
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
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    return p0
.end method

.method static synthetic access$4902(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    return p1
.end method

.method static synthetic access$500(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    return p0
.end method

.method static synthetic access$5000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    return p0
.end method

.method static synthetic access$5002(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    return p1
.end method

.method static synthetic access$502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    return p1
.end method

.method static synthetic access$5100(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    return-void
.end method

.method static synthetic access$5200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 30
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBlinkRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$5300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    return p0
.end method

.method static synthetic access$5400(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V
    .locals 0

    .line 30
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->syncAmbientBrightness(Z)V

    return-void
.end method

.method static synthetic access$5500(Lcom/navdy/hud/app/ambient/AmbientLightController;)J
    .locals 2

    .line 30
    iget-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartedAtMs:J

    return-wide v0
.end method

.method static synthetic access$5600(Lcom/navdy/hud/app/ambient/AmbientLightController;)J
    .locals 2

    .line 30
    iget-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeDurationMs:J

    return-wide v0
.end method

.method static synthetic access$5700(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1:I

    return p0
.end method

.method static synthetic access$5800(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    return p0
.end method

.method static synthetic access$5900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2:I

    return p0
.end method

.method static synthetic access$6000(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

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
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1Red:I

    return p0
.end method

.method static synthetic access$6200(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1Red:I

    return p0
.end method

.method static synthetic access$6300(IIF)I
    .locals 0

    .line 30
    invoke-static {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->interpolate(IIF)I

    move-result p0

    return p0
.end method

.method static synthetic access$6400(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1Green:I

    return p0
.end method

.method static synthetic access$6500(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1Green:I

    return p0
.end method

.method static synthetic access$6600(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1Blue:I

    return p0
.end method

.method static synthetic access$6700(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1Blue:I

    return p0
.end method

.method static synthetic access$6800(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2Red:I

    return p0
.end method

.method static synthetic access$6900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2Red:I

    return p0
.end method

.method static synthetic access$700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 30
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$7000(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2Green:I

    return p0
.end method

.method static synthetic access$7100(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2Green:I

    return p0
.end method

.method static synthetic access$7200(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2Blue:I

    return p0
.end method

.method static synthetic access$7300(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    iget p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2Blue:I

    return p0
.end method

.method static synthetic access$7400(Lcom/navdy/hud/app/ambient/AmbientLightController;IIIIIIIIZ)V
    .locals 0

    .line 30
    invoke-direct/range {p0 .. p9}, Lcom/navdy/hud/app/ambient/AmbientLightController;->applyAmbientFrame(IIIIIIIIZ)V

    return-void
.end method

.method static synthetic access$7500(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientFrameStepMs()I

    move-result p0

    return p0
.end method

.method static synthetic access$7600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    return p0
.end method

.method static synthetic access$7602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    return p1
.end method

.method static synthetic access$7702(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mExitCourtesyActive:Z

    return p1
.end method

.method static synthetic access$7800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    return p0
.end method

.method static synthetic access$7900(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone1Brightness()I

    move-result p0

    return p0
.end method

.method static synthetic access$800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    return p0
.end method

.method static synthetic access$8000(Lcom/navdy/hud/app/ambient/AmbientLightController;)I
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result p0

    return p0
.end method

.method static synthetic access$802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    return p1
.end method

.method static synthetic access$8100(Lcom/navdy/hud/app/ambient/AmbientLightController;)J
    .locals 2

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v0

    return-wide v0
.end method

.method static synthetic access$8200(Lcom/navdy/hud/app/ambient/AmbientLightController;IIJ)V
    .locals 0

    .line 30
    invoke-direct {p0, p1, p2, p3, p4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    return-void
.end method

.method static synthetic access$8302(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    return p1
.end method

.method static synthetic access$8400(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V
    .locals 0

    .line 30
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    return-void
.end method

.method static synthetic access$8500(Lcom/navdy/hud/app/ambient/AmbientLightController;)J
    .locals 2

    .line 30
    iget-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiresAtMs:J

    return-wide v0
.end method

.method static synthetic access$8600(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V
    .locals 0

    .line 30
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clearManualOverride(Ljava/lang/String;)V

    return-void
.end method

.method static synthetic access$8700(Lcom/navdy/hud/app/ambient/AmbientLightController;)J
    .locals 2

    .line 30
    iget-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastVehicleDataAtMs:J

    return-wide v0
.end method

.method static synthetic access$8800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Z
    .locals 0

    .line 30
    iget-boolean p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    return p0
.end method

.method static synthetic access$8802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z
    .locals 0

    .line 30
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    return p1
.end method

.method static synthetic access$8900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 30
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedStateRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;
    .locals 0

    .line 30
    iget-object p0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    return-object p0
.end method

.method static synthetic access$9002(Lcom/navdy/hud/app/ambient/AmbientLightController;J)J
    .locals 0

    .line 30
    iput-wide p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActivatedAtMs:J

    return-wide p1
.end method

.method static synthetic access$9100(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    return-void
.end method

.method static synthetic access$9200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBrightnessSync()V

    return-void
.end method

.method static synthetic access$9300(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->cancelOffroadTimers()V

    return-void
.end method

.method static synthetic access$9400(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->updateCpuWakeLock()V

    return-void
.end method

.method static synthetic access$9500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 30
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->noteVehicleDataReceived()V

    return-void
.end method

.method static synthetic access$9600(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V
    .locals 0

    .line 30
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setGearText(Ljava/lang/String;)V

    return-void
.end method

.method static synthetic access$9700(Lcom/navdy/hud/app/ambient/AmbientLightController;ZZ)V
    .locals 0

    .line 30
    invoke-direct {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setVehicleState(ZZ)V

    return-void
.end method

.method static synthetic access$9800(Lcom/navdy/hud/app/ambient/AmbientLightController;Lorg/json/JSONObject;)V
    .locals 0

    .line 30
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setAmbientOverride(Lorg/json/JSONObject;)V

    return-void
.end method

.method static synthetic access$9900(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V
    .locals 0

    .line 30
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestOverspeed(Z)V

    return-void
.end method

.method private activeOnroadZone1Brightness()I
    .locals 2

    .line 1262
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eqz v0, :cond_0

    const-string v0, "onroadDoor"

    const/4 v1, 0x1

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 1263
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onroadDoorZone1Brightness()I

    move-result v0

    goto :goto_0

    :cond_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone1Brightness()I

    move-result v0

    .line 1262
    :goto_0
    return v0
.end method

.method private activeOnroadZone2Brightness()I
    .locals 2

    .line 1267
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eqz v0, :cond_0

    const-string v0, "onroadDoor"

    const/4 v1, 0x1

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 1268
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onroadDoorZone2Brightness()I

    move-result v0

    goto :goto_0

    :cond_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result v0

    .line 1267
    :goto_0
    return v0
.end method

.method private activeStateColorPacket()[B
    .locals 2

    .line 783
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_0

    .line 784
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalColorPacket()[B

    move-result-object v0

    return-object v0

    .line 786
    :cond_0
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mExitCourtesyActive:Z

    if-eqz v0, :cond_1

    .line 787
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->exitCourtesyColorPacket()[B

    move-result-object v0

    return-object v0

    .line 789
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

    .line 790
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->offroadDoorColorPacket()[B

    move-result-object v0

    return-object v0

    .line 792
    :cond_2
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_3

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eqz v0, :cond_3

    const-string v0, "onroadDoor"

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result v0

    if-eqz v0, :cond_3

    .line 793
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onroadDoorColorPacket()[B

    move-result-object v0

    return-object v0

    .line 795
    :cond_3
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->drivingColorPacket()[B

    move-result-object v0

    return-object v0
.end method

.method private applyAmbientFrame(IIIIIIIIZ)V
    .locals 2

    .line 1185
    const/4 v0, 0x0

    const/16 v1, 0x64

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    .line 1186
    invoke-static {p2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2:I

    .line 1187
    const/16 p1, 0xff

    invoke-static {p3, v0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Red:I

    .line 1188
    invoke-static {p4, v0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Green:I

    .line 1189
    invoke-static {p5, v0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Blue:I

    .line 1190
    invoke-static {p6, v0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Red:I

    .line 1191
    invoke-static {p7, v0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Green:I

    .line 1192
    invoke-static {p8, v0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Blue:I

    .line 1193
    if-eqz p9, :cond_0

    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    if-nez p1, :cond_0

    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2:I

    if-nez p1, :cond_0

    .line 1194
    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 1195
    sget-object p1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_OFF:[B

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    goto :goto_0

    .line 1197
    :cond_0
    const/4 p1, 0x1

    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 1198
    iget p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Red:I

    iget p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Green:I

    iget p4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Blue:I

    iget p5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Red:I

    iget p6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Green:I

    iget p7, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Blue:I

    .line 1199
    invoke-static/range {p2 .. p7}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildColorPacket(IIIIII)[B

    move-result-object p2

    iget p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    iget p4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2:I

    .line 1202
    invoke-static {p1, p3, p4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildBrightnessPacket(ZII)[B

    move-result-object p1

    .line 1198
    invoke-direct {p0, p2, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendAmbientFrame([B[B)V

    .line 1204
    :goto_0
    return-void
.end method

.method private applyVehicleStateTargets()V
    .locals 4

    .line 1037
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileMasterEnabled()Z

    move-result v0

    if-nez v0, :cond_0

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-nez v0, :cond_0

    .line 1038
    const-string v0, "profile disabled"

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    goto/16 :goto_3

    .line 1039
    :cond_0
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez v0, :cond_6

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-eqz v0, :cond_1

    goto :goto_1

    .line 1041
    :cond_1
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_2

    .line 1042
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mExitCourtesyActive:Z

    .line 1043
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->activeOnroadZone1Brightness()I

    move-result v0

    .line 1044
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->activeOnroadZone2Brightness()I

    move-result v1

    .line 1045
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v2

    .line 1043
    invoke-direct {p0, v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    goto :goto_3

    .line 1046
    :cond_2
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eqz v0, :cond_5

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    if-nez v0, :cond_5

    .line 1047
    const-string v0, "offroadDoor"

    const/4 v1, 0x1

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result v0

    if-nez v0, :cond_4

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_3

    goto :goto_0

    .line 1051
    :cond_3
    const-string v0, "offroad door profile disabled"

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    goto :goto_3

    .line 1048
    :cond_4
    :goto_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->offroadDoorZone1Brightness()I

    move-result v0

    .line 1049
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->offroadDoorZone2Brightness()I

    move-result v1

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v2

    .line 1048
    invoke-direct {p0, v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    goto :goto_3

    .line 1053
    :cond_5
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_8

    .line 1054
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone1Brightness()I

    move-result v0

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result v1

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v2

    invoke-direct {p0, v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    goto :goto_3

    .line 1040
    :cond_6
    :goto_1
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-eqz v0, :cond_7

    const-string v0, "reverse"

    goto :goto_2

    :cond_7
    const-string v0, "comma data timeout"

    :goto_2
    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    .line 1056
    :cond_8
    :goto_3
    return-void
.end method

.method private beginRestoreFade()V
    .locals 4

    .line 1106
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBlinkRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1107
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-eqz v0, :cond_0

    goto :goto_0

    .line 1111
    :cond_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 1112
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->activeOnroadZone1Brightness()I

    move-result v0

    .line 1113
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->activeOnroadZone2Brightness()I

    move-result v1

    .line 1114
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v2

    .line 1112
    invoke-direct {p0, v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    .line 1115
    return-void

    .line 1108
    :cond_1
    :goto_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 1109
    return-void
.end method

.method private static buildBrightnessPacket(ZI)[B
    .locals 1

    .line 1640
    const/16 v0, 0x28

    invoke-static {p0, p1, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildBrightnessPacket(ZII)[B

    move-result-object p0

    return-object p0
.end method

.method private static buildBrightnessPacket(ZII)[B
    .locals 2

    .line 1644
    const/16 v0, 0x64

    const/4 v1, 0x0

    if-eqz p0, :cond_0

    invoke-static {p1, v1, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    goto :goto_0

    :cond_0
    const/4 p1, 0x0

    .line 1645
    :goto_0
    if-eqz p0, :cond_1

    invoke-static {p2, v1, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p2

    goto :goto_1

    :cond_1
    const/4 p2, 0x0

    .line 1646
    :goto_1
    if-eqz p0, :cond_2

    const/16 p0, 0x48

    goto :goto_2

    :cond_2
    const/4 p0, 0x0

    .line 1647
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

    .line 1652
    nop

    .line 1654
    const/4 v0, 0x0

    const/16 v1, 0xff

    invoke-static {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v4

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v5

    invoke-static {p2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v6

    .line 1655
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

    .line 1652
    const/16 p1, 0x8d

    invoke-static {p1, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildPacket(I[I)[B

    move-result-object p0

    return-object p0
.end method

.method private static buildPacket(I[I)[B
    .locals 8

    .line 1669
    array-length v0, p1

    .line 1670
    add-int/lit8 v1, v0, 0x4

    new-array v2, v1, [B

    .line 1671
    const/16 v3, 0x2e

    const/4 v4, 0x0

    aput-byte v3, v2, v4

    .line 1672
    int-to-byte v3, p0

    const/4 v5, 0x1

    aput-byte v3, v2, v5

    .line 1673
    const/4 v3, 0x2

    int-to-byte v6, v0

    aput-byte v6, v2, v3

    .line 1674
    add-int/2addr p0, v0

    .line 1675
    nop

    :goto_0
    if-ge v4, v0, :cond_0

    .line 1676
    aget v3, p1, v4

    and-int/lit16 v3, v3, 0xff

    .line 1677
    add-int/lit8 v6, v4, 0x3

    int-to-byte v7, v3

    aput-byte v7, v2, v6

    .line 1678
    add-int/2addr p0, v3

    .line 1675
    add-int/lit8 v4, v4, 0x1

    goto :goto_0

    .line 1680
    :cond_0
    sub-int/2addr v1, v5

    not-int p0, p0

    and-int/lit16 p0, p0, 0xff

    int-to-byte p0, p0

    aput-byte p0, v2, v1

    .line 1681
    return-object v2
.end method

.method private static bytesToHex([B)Ljava/lang/String;
    .locals 7

    .line 1761
    new-instance v0, Ljava/lang/StringBuilder;

    array-length v1, p0

    mul-int/lit8 v1, v1, 0x2

    invoke-direct {v0, v1}, Ljava/lang/StringBuilder;-><init>(I)V

    .line 1762
    array-length v1, p0

    const/4 v2, 0x0

    const/4 v3, 0x0

    :goto_0
    if-ge v3, v1, :cond_0

    aget-byte v4, p0, v3

    .line 1763
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

    .line 1762
    add-int/lit8 v3, v3, 0x1

    goto :goto_0

    .line 1765
    :cond_0
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method private cancelOffroadTimers()V
    .locals 2

    .line 1059
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1060
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1061
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1062
    return-void
.end method

.method private static clamp(III)I
    .locals 0

    .line 1685
    invoke-static {p2, p0}, Ljava/lang/Math;->min(II)I

    move-result p0

    invoke-static {p1, p0}, Ljava/lang/Math;->max(II)I

    move-result p0

    return p0
.end method

.method private clearManualOverride(Ljava/lang/String;)V
    .locals 2

    .line 850
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-nez v0, :cond_0

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideId:Ljava/lang/String;

    invoke-virtual {v0}, Ljava/lang/String;->length()I

    move-result v0

    if-nez v0, :cond_0

    .line 851
    return-void

    .line 853
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

    .line 854
    const/4 p1, 0x0

    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    .line 855
    const-wide/16 v0, 0x0

    iput-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiresAtMs:J

    .line 856
    const-string v0, ""

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideId:Ljava/lang/String;

    .line 857
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiryRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 858
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-eqz v0, :cond_1

    .line 859
    const-string p1, "reverse"

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    goto :goto_0

    .line 860
    :cond_1
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-nez v0, :cond_2

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-nez v0, :cond_2

    .line 861
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v0

    invoke-direct {p0, p1, p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    goto :goto_0

    .line 863
    :cond_2
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->applyVehicleStateTargets()V

    .line 865
    :goto_0
    return-void
.end method

.method private closeGatt()V
    .locals 2

    .line 1461
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    .line 1462
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnectTimeoutRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1463
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    if-eqz v0, :cond_0

    .line 1465
    :try_start_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    invoke-virtual {v0}, Landroid/bluetooth/BluetoothGatt;->close()V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 1467
    goto :goto_0

    .line 1466
    :catch_0
    move-exception v0

    .line 1468
    :goto_0
    const/4 v0, 0x0

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    .line 1470
    :cond_0
    return-void
.end method

.method private coalescePendingBrightnessPackets()V
    .locals 3

    .line 1596
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->isEmpty()Z

    move-result v0

    if-eqz v0, :cond_0

    .line 1597
    return-void

    .line 1599
    :cond_0
    new-instance v0, Ljava/util/ArrayDeque;

    invoke-direct {v0}, Ljava/util/ArrayDeque;-><init>()V

    .line 1600
    :goto_0
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1}, Ljava/util/ArrayDeque;->isEmpty()Z

    move-result v1

    if-nez v1, :cond_2

    .line 1601
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1}, Ljava/util/ArrayDeque;->poll()Ljava/lang/Object;

    move-result-object v1

    check-cast v1, [B

    .line 1602
    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isBrightnessPacket([B)Z

    move-result v2

    if-nez v2, :cond_1

    .line 1603
    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1605
    :cond_1
    goto :goto_0

    .line 1606
    :cond_2
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1, v0}, Ljava/util/ArrayDeque;->addAll(Ljava/util/Collection;)Z

    .line 1607
    return-void
.end method

.method private static colorPacketValue([BII)I
    .locals 1

    .line 1660
    if-eqz p0, :cond_0

    if-ltz p1, :cond_0

    array-length v0, p0

    add-int/lit8 v0, v0, -0x1

    if-ge p1, v0, :cond_0

    .line 1661
    aget-byte p0, p0, p1

    and-int/lit16 p2, p0, 0xff

    goto :goto_0

    :cond_0
    nop

    .line 1660
    :goto_0
    return p2
.end method

.method private static colorValue(Lorg/json/JSONObject;II)I
    .locals 2

    .line 670
    if-eqz p0, :cond_1

    const-string v0, "rgb"

    invoke-virtual {p0, v0}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v1

    if-nez v1, :cond_0

    goto :goto_0

    .line 673
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

    .line 671
    :cond_1
    :goto_0
    return p2
.end method

.method private static configureWriteCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)V
    .locals 1

    .line 1689
    invoke-virtual {p0}, Landroid/bluetooth/BluetoothGattCharacteristic;->getProperties()I

    move-result v0

    .line 1690
    and-int/lit8 v0, v0, 0x4

    if-eqz v0, :cond_0

    .line 1691
    const/4 v0, 0x1

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGattCharacteristic;->setWriteType(I)V

    goto :goto_0

    .line 1693
    :cond_0
    const/4 v0, 0x2

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGattCharacteristic;->setWriteType(I)V

    .line 1695
    :goto_0
    return-void
.end method

.method private connectBondedCandidate()Z
    .locals 4

    .line 1419
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    invoke-virtual {v0}, Landroid/bluetooth/BluetoothAdapter;->getBondedDevices()Ljava/util/Set;

    move-result-object v0

    .line 1420
    const/4 v1, 0x0

    if-nez v0, :cond_0

    .line 1421
    return v1

    .line 1423
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

    .line 1424
    if-eqz v2, :cond_1

    const/4 v3, 0x0

    invoke-static {v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->matchesAmbientDevice(Landroid/bluetooth/BluetoothDevice;[B)Z

    move-result v3

    if-eqz v3, :cond_1

    .line 1425
    invoke-direct {p0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectDevice(Landroid/bluetooth/BluetoothDevice;)V

    .line 1426
    const/4 v0, 0x1

    return v0

    .line 1428
    :cond_1
    goto :goto_0

    .line 1429
    :cond_2
    return v1
.end method

.method private connectDevice(Landroid/bluetooth/BluetoothDevice;)V
    .locals 4

    .line 1433
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->closeGatt()V

    .line 1434
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    .line 1435
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectScheduled:Z

    .line 1436
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectRunnable:Ljava/lang/Runnable;

    invoke-virtual {v1, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1437
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    .line 1438
    invoke-virtual {v1}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v1

    invoke-virtual {p1}, Landroid/bluetooth/BluetoothDevice;->getAddress()Ljava/lang/String;

    move-result-object v2

    .line 1437
    const-string v3, "navdy_ambient_device_address"

    invoke-static {v1, v3, v2}, Landroid/provider/Settings$System;->putString(Landroid/content/ContentResolver;Ljava/lang/String;Ljava/lang/String;)Z

    .line 1439
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

    .line 1440
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;

    invoke-virtual {p1, v1, v0, v2}, Landroid/bluetooth/BluetoothDevice;->connectGatt(Landroid/content/Context;ZLandroid/bluetooth/BluetoothGattCallback;)Landroid/bluetooth/BluetoothGatt;

    move-result-object p1

    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    .line 1441
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    if-nez p1, :cond_0

    .line 1442
    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    .line 1443
    const-wide/16 v0, 0x1388

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    goto :goto_0

    .line 1445
    :cond_0
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnectTimeoutRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1446
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnectTimeoutRunnable:Ljava/lang/Runnable;

    const-wide/16 v1, 0x2710

    invoke-virtual {p1, v0, v1, v2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 1448
    :goto_0
    return-void
.end method

.method private connectIfNeeded()V
    .locals 5

    .line 1359
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    if-nez v0, :cond_7

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnecting:Z

    if-nez v0, :cond_7

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    if-nez v0, :cond_7

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectScheduled:Z

    if-eqz v0, :cond_0

    goto/16 :goto_2

    .line 1362
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    if-nez v0, :cond_1

    .line 1363
    invoke-static {}, Landroid/bluetooth/BluetoothAdapter;->getDefaultAdapter()Landroid/bluetooth/BluetoothAdapter;

    move-result-object v0

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    .line 1365
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

    .line 1370
    :cond_2
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSkipRememberedOnce:Z

    if-nez v0, :cond_3

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectRememberedCandidate()Z

    move-result v0

    if-eqz v0, :cond_3

    .line 1371
    return-void

    .line 1373
    :cond_3
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSkipRememberedOnce:Z

    .line 1374
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectBondedCandidate()Z

    move-result v0

    if-eqz v0, :cond_4

    .line 1375
    return-void

    .line 1377
    :cond_4
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSeenScanDevices:Ljava/util/Set;

    invoke-interface {v0}, Ljava/util/Set;->clear()V

    .line 1378
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanCallback:Landroid/bluetooth/BluetoothAdapter$LeScanCallback;

    invoke-virtual {v0, v4}, Landroid/bluetooth/BluetoothAdapter;->startLeScan(Landroid/bluetooth/BluetoothAdapter$LeScanCallback;)Z

    move-result v0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    .line 1379
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

    .line 1380
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    if-eqz v0, :cond_5

    .line 1381
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStopScanRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1382
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStopScanRunnable:Ljava/lang/Runnable;

    const-wide/16 v2, 0x2710

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    goto :goto_0

    .line 1384
    :cond_5
    invoke-direct {p0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    .line 1386
    :goto_0
    return-void

    .line 1366
    :cond_6
    :goto_1
    const-string v0, "bluetooth disabled"

    invoke-static {v3, v0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 1367
    invoke-direct {p0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    .line 1368
    return-void

    .line 1360
    :cond_7
    :goto_2
    return-void
.end method

.method private connectRememberedCandidate()Z
    .locals 4

    .line 1403
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    .line 1404
    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v0

    .line 1403
    const-string v1, "navdy_ambient_device_address"

    invoke-static {v0, v1}, Landroid/provider/Settings$System;->getString(Landroid/content/ContentResolver;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    .line 1405
    const/4 v1, 0x0

    if-eqz v0, :cond_1

    invoke-static {v0}, Landroid/bluetooth/BluetoothAdapter;->checkBluetoothAddress(Ljava/lang/String;)Z

    move-result v2

    if-nez v2, :cond_0

    goto :goto_0

    .line 1409
    :cond_0
    :try_start_0
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    invoke-virtual {v2, v0}, Landroid/bluetooth/BluetoothAdapter;->getRemoteDevice(Ljava/lang/String;)Landroid/bluetooth/BluetoothDevice;

    move-result-object v0

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectDevice(Landroid/bluetooth/BluetoothDevice;)V

    .line 1410
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSkipRememberedOnce:Z
    :try_end_0
    .catch Ljava/lang/IllegalArgumentException; {:try_start_0 .. :try_end_0} :catch_0

    .line 1411
    return v0

    .line 1412
    :catch_0
    move-exception v0

    .line 1413
    const-string v2, "NavdyAmbient"

    const-string v3, "bad remembered ambient address"

    invoke-static {v2, v3, v0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 1414
    return v1

    .line 1406
    :cond_1
    :goto_0
    return v1
.end method

.method private drivingColorPacket()[B
    .locals 3

    .line 767
    const-string v0, "zone1"

    const-string v1, "zone2"

    const-string v2, "driving"

    invoke-direct {p0, v2, v0, v2, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileColorPacket(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)[B

    move-result-object v0

    return-object v0
.end method

.method private static enableNotifications(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z
    .locals 5

    .line 1698
    const/4 v0, 0x0

    if-eqz p0, :cond_4

    if-nez p1, :cond_0

    goto :goto_2

    .line 1701
    :cond_0
    const/4 v1, 0x1

    invoke-virtual {p0, p1, v1}, Landroid/bluetooth/BluetoothGatt;->setCharacteristicNotification(Landroid/bluetooth/BluetoothGattCharacteristic;Z)Z

    move-result v2

    .line 1702
    sget-object v3, Lcom/navdy/hud/app/ambient/AmbientLightController;->CLIENT_CONFIG_UUID:Ljava/util/UUID;

    invoke-virtual {p1, v3}, Landroid/bluetooth/BluetoothGattCharacteristic;->getDescriptor(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattDescriptor;

    move-result-object p1

    .line 1703
    const-string v3, "NavdyAmbient"

    if-eqz v2, :cond_2

    if-nez p1, :cond_1

    goto :goto_0

    .line 1707
    :cond_1
    sget-object v0, Landroid/bluetooth/BluetoothGattDescriptor;->ENABLE_NOTIFICATION_VALUE:[B

    invoke-virtual {p1, v0}, Landroid/bluetooth/BluetoothGattDescriptor;->setValue([B)Z

    .line 1708
    invoke-virtual {p0, p1}, Landroid/bluetooth/BluetoothGatt;->writeDescriptor(Landroid/bluetooth/BluetoothGattDescriptor;)Z

    move-result p0

    .line 1709
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

    .line 1710
    return p0

    .line 1704
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

    .line 1705
    return v0

    .line 1699
    :cond_4
    :goto_2
    return v0
.end method

.method private exitCourtesyColorPacket()[B
    .locals 4

    .line 779
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

    .line 1284
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_0

    .line 1285
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result v0

    goto :goto_0

    .line 1286
    :cond_0
    const-string v0, "zone2"

    const/16 v1, 0x64

    const-string v2, "exitCourtesy"

    invoke-direct {p0, v2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileBrightness(Ljava/lang/String;Ljava/lang/String;I)I

    move-result v0

    .line 1284
    :goto_0
    return v0
.end method

.method private static findNotifyCharacteristic(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 1

    .line 1725
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->SERVICE_UUID:Ljava/util/UUID;

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;

    move-result-object v0

    .line 1726
    if-nez v0, :cond_0

    .line 1727
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->LEGACY_SERVICE_UUID:Ljava/util/UUID;

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;

    move-result-object v0

    .line 1729
    :cond_0
    if-nez v0, :cond_1

    .line 1730
    const/4 p0, 0x0

    return-object p0

    .line 1732
    :cond_1
    sget-object p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->NOTIFY_UUID:Ljava/util/UUID;

    invoke-virtual {v0, p0}, Landroid/bluetooth/BluetoothGattService;->getCharacteristic(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p0

    return-object p0
.end method

.method private static findWriteCharacteristic(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;
    .locals 1

    .line 1714
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->SERVICE_UUID:Ljava/util/UUID;

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;

    move-result-object v0

    .line 1715
    if-nez v0, :cond_0

    .line 1716
    sget-object v0, Lcom/navdy/hud/app/ambient/AmbientLightController;->LEGACY_SERVICE_UUID:Ljava/util/UUID;

    invoke-virtual {p0, v0}, Landroid/bluetooth/BluetoothGatt;->getService(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattService;

    move-result-object v0

    .line 1718
    :cond_0
    if-nez v0, :cond_1

    .line 1719
    const/4 p0, 0x0

    return-object p0

    .line 1721
    :cond_1
    sget-object p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->WRITE_UUID:Ljava/util/UUID;

    invoke-virtual {v0, p0}, Landroid/bluetooth/BluetoothGattService;->getCharacteristic(Ljava/util/UUID;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p0

    return-object p0
.end method

.method private flushNext()V
    .locals 6

    .line 1327
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

    .line 1330
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->poll()Ljava/lang/Object;

    move-result-object v0

    check-cast v0, [B

    .line 1331
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v1, v0}, Landroid/bluetooth/BluetoothGattCharacteristic;->setValue([B)Z

    .line 1332
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->configureWriteCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)V

    .line 1333
    const/4 v1, 0x1

    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    .line 1334
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    invoke-virtual {v2, v3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1335
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    invoke-virtual {v2, v3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1336
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    const-wide/16 v4, 0x4b0

    invoke-virtual {v2, v3, v4, v5}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 1337
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getWriteType()I

    move-result v2

    if-ne v2, v1, :cond_1

    .line 1338
    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->usesPacedWrite([B)Z

    move-result v1

    if-eqz v1, :cond_1

    .line 1339
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    const-wide/16 v3, 0x78

    invoke-virtual {v1, v2, v3, v4}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 1341
    :cond_1
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v1, v2}, Landroid/bluetooth/BluetoothGatt;->writeCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result v1

    .line 1342
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

    .line 1343
    if-nez v1, :cond_2

    .line 1344
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteTimeoutRunnable:Ljava/lang/Runnable;

    invoke-virtual {v1, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1345
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWritePaceRunnable:Ljava/lang/Runnable;

    invoke-virtual {v1, v2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1346
    const/4 v1, 0x0

    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriting:Z

    .line 1347
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v2, v0}, Ljava/util/ArrayDeque;->offerFirst(Ljava/lang/Object;)Z

    .line 1348
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mConnected:Z

    .line 1349
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyReady:Z

    .line 1350
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStartQueued:Z

    .line 1351
    const/4 v0, 0x0

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 1352
    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mNotifyCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 1353
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->closeGatt()V

    .line 1354
    const-wide/16 v0, 0x1388

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    .line 1356
    :cond_2
    return-void

    .line 1328
    :cond_3
    :goto_0
    return-void
.end method

.method public static declared-synchronized get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;
    .locals 2

    const-class v0, Lcom/navdy/hud/app/ambient/AmbientLightController;

    monitor-enter v0

    .line 544
    :try_start_0
    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->sInstance:Lcom/navdy/hud/app/ambient/AmbientLightController;

    if-nez v1, :cond_0

    .line 545
    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {v1, p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;-><init>(Landroid/content/Context;)V

    sput-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->sInstance:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 547
    :cond_0
    sget-object p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->sInstance:Lcom/navdy/hud/app/ambient/AmbientLightController;
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    monitor-exit v0

    return-object p0

    .line 543
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

    .line 1218
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

    .line 1219
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1220
    const/4 p1, 0x0

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    .line 1221
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2:I

    .line 1222
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    .line 1223
    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    .line 1224
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 1225
    sget-object p1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_OFF:[B

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->sendPacket([B)V

    .line 1226
    return-void
.end method

.method private static interpolate(IIF)I
    .locals 1

    .line 1665
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

    .line 1619
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

    .line 1625
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

    .line 1799
    const-string v0, "p"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "park"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    .line 1800
    const-string v0, "n"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "neutral"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    .line 1801
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

    .line 1799
    :goto_1
    return p0
.end method

.method private static isReverse(Ljava/lang/String;)Z
    .locals 1

    .line 1795
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

    .line 1610
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

    .line 677
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    .line 678
    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v0

    .line 677
    const-string v1, "navdy_ambient_profile_json"

    invoke-static {v0, v1}, Landroid/provider/Settings$System;->getString(Landroid/content/ContentResolver;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    .line 679
    if-eqz v0, :cond_1

    invoke-virtual {v0}, Ljava/lang/String;->length()I

    move-result v1

    if-nez v1, :cond_0

    goto :goto_1

    .line 684
    :cond_0
    :try_start_0
    new-instance v1, Lorg/json/JSONObject;

    invoke-direct {v1, v0}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    iput-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mProfile:Lorg/json/JSONObject;
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 688
    goto :goto_0

    .line 685
    :catch_0
    move-exception v0

    .line 686
    const-string v1, "NavdyAmbient"

    const-string v2, "bad stored ambient profile"

    invoke-static {v1, v2, v0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 687
    new-instance v0, Lorg/json/JSONObject;

    invoke-direct {v0}, Lorg/json/JSONObject;-><init>()V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mProfile:Lorg/json/JSONObject;

    .line 689
    :goto_0
    return-void

    .line 680
    :cond_1
    :goto_1
    new-instance v0, Lorg/json/JSONObject;

    invoke-direct {v0}, Lorg/json/JSONObject;-><init>()V

    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mProfile:Lorg/json/JSONObject;

    .line 681
    return-void
.end method

.method private logSeenScanDevice(Landroid/bluetooth/BluetoothDevice;I)V
    .locals 3

    .line 1473
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;

    move-result-object v0

    .line 1474
    invoke-virtual {v0}, Ljava/lang/String;->length()I

    move-result v1

    if-nez v1, :cond_0

    .line 1475
    return-void

    .line 1477
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

    .line 1478
    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mSeenScanDevices:Ljava/util/Set;

    invoke-interface {v2, v1}, Ljava/util/Set;->add(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_1

    .line 1479
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

    .line 1481
    :cond_1
    return-void
.end method

.method private static matchesAmbientDevice(Landroid/bluetooth/BluetoothDevice;[B)Z
    .locals 2

    .line 1736
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;

    move-result-object p0

    sget-object v0, Ljava/util/Locale;->US:Ljava/util/Locale;

    invoke-virtual {p0, v0}, Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)Ljava/lang/String;

    move-result-object p0

    .line 1737
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

    .line 1738
    const-string v0, "slave"

    invoke-virtual {p0, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-eqz v0, :cond_0

    goto :goto_0

    .line 1741
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

    .line 1742
    const-string v0, "carled"

    invoke-virtual {p0, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v0

    if-nez v0, :cond_1

    const-string v0, "pocket"

    invoke-virtual {p0, v0}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result p0

    if-nez p0, :cond_1

    .line 1743
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scanRecordContainsAmbientUuid([B)Z

    move-result p0

    if-eqz p0, :cond_2

    :cond_1
    const/4 v1, 0x1

    .line 1741
    :cond_2
    return v1

    .line 1739
    :cond_3
    :goto_0
    return v1
.end method

.method private needsConnection()Z
    .locals 1

    .line 1484
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

    .line 1290
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-nez v0, :cond_0

    .line 1291
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->drivingColorPacket()[B

    move-result-object v0

    return-object v0

    .line 1293
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

    .line 1234
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_1

    .line 1235
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Enabled:Z

    if-eqz v0, :cond_0

    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Brightness:I

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    :goto_0
    return v0

    .line 1237
    :cond_1
    const-string v0, "driving"

    const-string v1, "zone1"

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileZone(Ljava/lang/String;Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v2

    .line 1238
    const-string v3, "automaticBrightness"

    const/4 v4, 0x1

    invoke-virtual {v2, v3, v4}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v2

    if-nez v2, :cond_2

    .line 1239
    const/16 v2, 0x14

    invoke-direct {p0, v0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileBrightness(Ljava/lang/String;Ljava/lang/String;I)I

    move-result v0

    return v0

    .line 1241
    :cond_2
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientBrightness()I

    move-result v0

    return v0
.end method

.method private normalZone2Brightness()I
    .locals 3

    .line 1245
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_1

    .line 1246
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Enabled:Z

    if-eqz v0, :cond_0

    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Brightness:I

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    :goto_0
    return v0

    .line 1248
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

    .line 1778
    invoke-virtual {p0}, Ljava/lang/String;->trim()Ljava/lang/String;

    move-result-object p0

    sget-object v0, Ljava/util/Locale;->US:Ljava/util/Locale;

    invoke-virtual {p0, v0}, Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)Ljava/lang/String;

    move-result-object p0

    .line 1779
    const-string v0, ".reverse"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 1780
    const-string p0, "reverse"

    return-object p0

    .line 1782
    :cond_0
    const-string v0, ".park"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_1

    .line 1783
    const-string p0, "park"

    return-object p0

    .line 1785
    :cond_1
    const-string v0, ".neutral"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_2

    .line 1786
    const-string p0, "neutral"

    return-object p0

    .line 1788
    :cond_2
    const-string v0, ".drive"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_3

    .line 1789
    const-string p0, "drive"

    return-object p0

    .line 1791
    :cond_3
    return-object p0
.end method

.method private noteVehicleDataReceived()V
    .locals 4

    .line 928
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    iput-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastVehicleDataAtMs:J

    .line 929
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    .line 930
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataWatchdogRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 931
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataWatchdogRunnable:Ljava/lang/Runnable;

    const-wide/16 v2, 0xbb8

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 932
    return-void
.end method

.method private offroadDoorColorPacket()[B
    .locals 3

    .line 775
    const-string v0, "zone1"

    const-string v1, "zone2"

    const-string v2, "offroadDoor"

    invoke-direct {p0, v2, v0, v2, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileColorPacket(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)[B

    move-result-object v0

    return-object v0
.end method

.method private offroadDoorZone1Brightness()I
    .locals 3

    .line 1272
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_0

    .line 1273
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone1Brightness()I

    move-result v0

    goto :goto_0

    .line 1274
    :cond_0
    const-string v0, "zone1"

    const/16 v1, 0x14

    const-string v2, "offroadDoor"

    invoke-direct {p0, v2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileBrightness(Ljava/lang/String;Ljava/lang/String;I)I

    move-result v0

    .line 1272
    :goto_0
    return v0
.end method

.method private offroadDoorZone2Brightness()I
    .locals 3

    .line 1278
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_0

    .line 1279
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result v0

    goto :goto_0

    .line 1280
    :cond_0
    const-string v0, "zone2"

    const/16 v1, 0x64

    const-string v2, "offroadDoor"

    invoke-direct {p0, v2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileBrightness(Ljava/lang/String;Ljava/lang/String;I)I

    move-result v0

    .line 1278
    :goto_0
    return v0
.end method

.method public static onCameraSpeedChanged(Landroid/content/Context;II)V
    .locals 2

    .line 620
    if-nez p0, :cond_0

    .line 621
    return-void

    .line 623
    :cond_0
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;

    move-result-object p0

    .line 624
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientLightController$22;

    invoke-direct {v1, p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController$22;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;II)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 630
    return-void
.end method

.method public static onGearText(Landroid/content/Context;Ljava/lang/String;)V
    .locals 2

    .line 594
    if-eqz p0, :cond_1

    if-nez p1, :cond_0

    goto :goto_0

    .line 597
    :cond_0
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;

    move-result-object p0

    .line 598
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientLightController$20;

    invoke-direct {v1, p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController$20;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 604
    return-void

    .line 595
    :cond_1
    :goto_0
    return-void
.end method

.method public static onOpenpilotPayload(Landroid/content/Context;Ljava/lang/String;)V
    .locals 12

    .line 551
    const-string v0, "doorOpen"

    const-string v1, "onroad"

    if-eqz p0, :cond_1

    if-nez p1, :cond_0

    goto :goto_1

    .line 555
    :cond_0
    :try_start_0
    new-instance v2, Lorg/json/JSONObject;

    invoke-direct {v2, p1}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    .line 556
    const-string p1, "gear"

    const-string v3, "gearShifter"

    const-string v4, ""

    invoke-virtual {v2, v3, v4}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v3

    invoke-virtual {v2, p1, v3}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v6

    .line 557
    invoke-virtual {v2, v1}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result v7

    .line 558
    invoke-virtual {v2, v0}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result v8

    .line 559
    const/4 p1, 0x1

    invoke-virtual {v2, v1, p1}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v9

    .line 560
    const/4 p1, 0x0

    invoke-virtual {v2, v0, p1}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v10

    .line 561
    const-string p1, "ambientOverride"

    invoke-virtual {v2, p1}, Lorg/json/JSONObject;->optJSONObject(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v11

    .line 562
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;

    move-result-object v5

    .line 563
    iget-object p0, v5, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    new-instance v4, Lcom/navdy/hud/app/ambient/AmbientLightController$19;

    invoke-direct/range {v4 .. v11}, Lcom/navdy/hud/app/ambient/AmbientLightController$19;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;Ljava/lang/String;ZZZZLorg/json/JSONObject;)V

    invoke-virtual {p0, v4}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 584
    goto :goto_0

    .line 582
    :catch_0
    move-exception v0

    move-object p0, v0

    .line 583
    const-string p1, "NavdyAmbient"

    const-string v0, "bad openpilot payload"

    invoke-static {p1, v0, p0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 585
    :goto_0
    return-void

    .line 552
    :cond_1
    :goto_1
    return-void
.end method

.method public static onOpenpilotPayload(Landroid/content/Context;Lorg/json/JSONObject;)V
    .locals 0

    .line 588
    if-eqz p1, :cond_0

    .line 589
    invoke-virtual {p1}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-static {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onOpenpilotPayload(Landroid/content/Context;Ljava/lang/String;)V

    .line 591
    :cond_0
    return-void
.end method

.method public static onOverspeedChanged(Landroid/content/Context;Z)V
    .locals 2

    .line 607
    if-nez p0, :cond_0

    .line 608
    return-void

    .line 610
    :cond_0
    invoke-static {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->get(Landroid/content/Context;)Lcom/navdy/hud/app/ambient/AmbientLightController;

    move-result-object p0

    .line 611
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    new-instance v1, Lcom/navdy/hud/app/ambient/AmbientLightController$21;

    invoke-direct {v1, p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController$21;-><init>(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)V

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 617
    return-void
.end method

.method private onroadDoorColorPacket()[B
    .locals 3

    .line 771
    const-string v0, "zone1"

    const-string v1, "zone2"

    const-string v2, "onroadDoor"

    invoke-direct {p0, v2, v0, v2, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileColorPacket(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)[B

    move-result-object v0

    return-object v0
.end method

.method private onroadDoorZone1Brightness()I
    .locals 3

    .line 1252
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_0

    .line 1253
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone1Brightness()I

    move-result v0

    goto :goto_0

    :cond_0
    const-string v0, "zone1"

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone1Brightness()I

    move-result v1

    const-string v2, "onroadDoor"

    invoke-direct {p0, v2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileBrightness(Ljava/lang/String;Ljava/lang/String;I)I

    move-result v0

    .line 1252
    :goto_0
    return v0
.end method

.method private onroadDoorZone2Brightness()I
    .locals 3

    .line 1257
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_0

    .line 1258
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result v0

    goto :goto_0

    :cond_0
    const-string v0, "zone2"

    const/16 v1, 0x64

    const-string v2, "onroadDoor"

    invoke-direct {p0, v2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileBrightness(Ljava/lang/String;Ljava/lang/String;I)I

    move-result v0

    .line 1257
    :goto_0
    return v0
.end method

.method private static parseIsoTimeMs(Ljava/lang/String;)J
    .locals 7

    .line 644
    const-wide/16 v0, 0x0

    if-eqz p0, :cond_3

    invoke-virtual {p0}, Ljava/lang/String;->length()I

    move-result v2

    if-nez v2, :cond_0

    goto :goto_2

    .line 647
    :cond_0
    const-string v2, "yyyy-MM-dd\'T\'HH:mm:ss.SSS\'Z\'"

    const-string v3, "yyyy-MM-dd\'T\'HH:mm:ss\'Z\'"

    filled-new-array {v2, v3}, [Ljava/lang/String;

    move-result-object v2

    .line 651
    const/4 v3, 0x0

    :goto_0
    const/4 v4, 0x2

    if-ge v3, v4, :cond_2

    aget-object v4, v2, v3

    .line 653
    :try_start_0
    new-instance v5, Ljava/text/SimpleDateFormat;

    sget-object v6, Ljava/util/Locale;->US:Ljava/util/Locale;

    invoke-direct {v5, v4, v6}, Ljava/text/SimpleDateFormat;-><init>(Ljava/lang/String;Ljava/util/Locale;)V

    .line 654
    const-string v4, "UTC"

    invoke-static {v4}, Ljava/util/TimeZone;->getTimeZone(Ljava/lang/String;)Ljava/util/TimeZone;

    move-result-object v4

    invoke-virtual {v5, v4}, Ljava/text/SimpleDateFormat;->setTimeZone(Ljava/util/TimeZone;)V

    .line 655
    invoke-virtual {v5, p0}, Ljava/text/SimpleDateFormat;->parse(Ljava/lang/String;)Ljava/util/Date;

    move-result-object v4

    .line 656
    if-eqz v4, :cond_1

    .line 657
    invoke-virtual {v4}, Ljava/util/Date;->getTime()J

    move-result-wide v0
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    return-wide v0

    .line 660
    :cond_1
    goto :goto_1

    .line 659
    :catch_0
    move-exception v4

    .line 651
    :goto_1
    add-int/lit8 v3, v3, 0x1

    goto :goto_0

    .line 662
    :cond_2
    return-wide v0

    .line 645
    :cond_3
    :goto_2
    return-wide v0
.end method

.method private profileBrightness(Ljava/lang/String;Ljava/lang/String;I)I
    .locals 1

    .line 732
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

    .line 759
    invoke-direct {p0, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileZone(Ljava/lang/String;Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    .line 760
    invoke-direct {p0, p3, p4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileZone(Ljava/lang/String;Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p2

    .line 761
    nop

    .line 762
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

    .line 763
    invoke-static {p2, p3, p4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result p3

    invoke-static {p2, v2, p4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v4

    invoke-static {p2, v3, p4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v5

    .line 761
    move v2, p1

    move v3, p3

    invoke-static/range {v0 .. v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildColorPacket(IIIIII)[B

    move-result-object p1

    return-object p1
.end method

.method private profileDoorCloseDelayMs()J
    .locals 8

    .line 745
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

    .line 749
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

    .line 753
    nop

    .line 754
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

    .line 753
    const-wide/16 v2, 0x0

    invoke-static {v2, v3, v0, v1}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v0

    const-wide/16 v2, 0x3e8

    mul-long v0, v0, v2

    return-wide v0
.end method

.method private profileFadeMs()J
    .locals 8

    .line 741
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

    .line 728
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileSection(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    const-string v0, "enabled"

    invoke-virtual {p1, v0, p2}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result p1

    return p1
.end method

.method private profileMasterEnabled()Z
    .locals 3

    .line 724
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mProfile:Lorg/json/JSONObject;

    const-string v1, "enabled"

    const/4 v2, 0x1

    invoke-virtual {v0, v1, v2}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v0

    return v0
.end method

.method private profileSection(Ljava/lang/String;)Lorg/json/JSONObject;
    .locals 1

    .line 714
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mProfile:Lorg/json/JSONObject;

    invoke-virtual {v0, p1}, Lorg/json/JSONObject;->optJSONObject(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    .line 715
    if-nez p1, :cond_0

    new-instance p1, Lorg/json/JSONObject;

    invoke-direct {p1}, Lorg/json/JSONObject;-><init>()V

    :cond_0
    return-object p1
.end method

.method private profileTimingMs(Ljava/lang/String;JJJ)J
    .locals 1

    .line 736
    nop

    .line 737
    const-string v0, "timing"

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileSection(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v0

    invoke-virtual {v0, p1, p2, p3}, Lorg/json/JSONObject;->optLong(Ljava/lang/String;J)J

    move-result-wide p1

    invoke-static {p6, p7, p1, p2}, Ljava/lang/Math;->min(JJ)J

    move-result-wide p1

    .line 736
    invoke-static {p4, p5, p1, p2}, Ljava/lang/Math;->max(JJ)J

    move-result-wide p1

    return-wide p1
.end method

.method private profileZone(Ljava/lang/String;Ljava/lang/String;)Lorg/json/JSONObject;
    .locals 0

    .line 719
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileSection(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    invoke-virtual {p1, p2}, Lorg/json/JSONObject;->optJSONObject(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    .line 720
    if-nez p1, :cond_0

    new-instance p1, Lorg/json/JSONObject;

    invoke-direct {p1}, Lorg/json/JSONObject;-><init>()V

    :cond_0
    return-object p1
.end method

.method private queueStartPacket()V
    .locals 2

    .line 1488
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStartQueued:Z

    if-eqz v0, :cond_0

    .line 1489
    return-void

    .line 1491
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_START:[B

    invoke-virtual {v1}, [B->clone()Ljava/lang/Object;

    move-result-object v1

    check-cast v1, [B

    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offerFirst(Ljava/lang/Object;)Z

    .line 1492
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStartQueued:Z

    .line 1493
    return-void
.end method

.method private readAckSettleIntervalMs()I
    .locals 3

    .line 1590
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

    .line 1544
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readScreenBrightness()I

    move-result v0

    .line 1545
    const/4 v1, 0x1

    const/16 v2, 0x10

    if-gt v0, v2, :cond_0

    .line 1546
    return v1

    .line 1548
    :cond_0
    const/16 v3, 0x29

    const/16 v4, 0x8

    if-gt v0, v3, :cond_1

    .line 1549
    nop

    .line 1550
    nop

    .line 1551
    sub-int/2addr v0, v2

    mul-int/lit8 v0, v0, 0x7

    add-int/lit8 v0, v0, 0xc

    div-int/lit8 v0, v0, 0x19

    add-int/2addr v0, v1

    .line 1554
    invoke-static {v0, v1, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v0

    return v0

    .line 1556
    :cond_1
    const/16 v1, 0x64

    const/16 v2, 0x32

    if-gt v0, v1, :cond_2

    .line 1557
    nop

    .line 1558
    nop

    .line 1559
    sub-int/2addr v0, v3

    mul-int/lit8 v0, v0, 0x2a

    add-int/lit8 v0, v0, 0x1d

    div-int/lit8 v0, v0, 0x3b

    add-int/2addr v0, v4

    .line 1562
    invoke-static {v0, v4, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v0

    return v0

    .line 1564
    :cond_2
    return v2
.end method

.method private readAmbientFrameStepMs()I
    .locals 2

    .line 1586
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

    .line 1572
    const-string v0, "timing"

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileSection(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v0

    .line 1573
    const-string v1, "transitionUpdatesPerSecond"

    invoke-virtual {v0, v1}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result v2

    const/16 v3, 0xfa

    const/16 v4, 0x21

    if-eqz v2, :cond_0

    .line 1574
    const/16 v2, 0x1e

    invoke-virtual {v0, v1, v2}, Lorg/json/JSONObject;->optInt(Ljava/lang/String;I)I

    move-result v0

    const/4 v1, 0x5

    invoke-static {v0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result v0

    .line 1575
    const/16 v1, 0x3e8

    div-int/2addr v1, v0

    .line 1576
    invoke-static {v3, v1}, Ljava/lang/Math;->min(II)I

    move-result v0

    .line 1575
    invoke-static {v4, v0}, Ljava/lang/Math;->max(II)I

    move-result v0

    return v0

    .line 1578
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

    .line 1568
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

    .line 1631
    const/4 v0, 0x5

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Red:I

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result v0

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Red:I

    .line 1632
    const/4 v0, 0x6

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Green:I

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result v0

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Green:I

    .line 1633
    const/4 v0, 0x7

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Blue:I

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result v0

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Blue:I

    .line 1634
    const/16 v0, 0x8

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Red:I

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result v0

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Red:I

    .line 1635
    const/16 v0, 0x9

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Green:I

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result v0

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Green:I

    .line 1636
    const/16 v0, 0xa

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Blue:I

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Blue:I

    .line 1637
    return-void
.end method

.method private removePendingAmbientStatePackets()V
    .locals 4

    .line 1520
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->isEmpty()Z

    move-result v0

    if-eqz v0, :cond_0

    .line 1521
    return-void

    .line 1523
    :cond_0
    new-instance v0, Ljava/util/ArrayDeque;

    invoke-direct {v0}, Ljava/util/ArrayDeque;-><init>()V

    .line 1524
    :goto_0
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1}, Ljava/util/ArrayDeque;->isEmpty()Z

    move-result v1

    if-nez v1, :cond_3

    .line 1525
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1}, Ljava/util/ArrayDeque;->poll()Ljava/lang/Object;

    move-result-object v1

    check-cast v1, [B

    .line 1526
    if-eqz v1, :cond_2

    array-length v2, v1

    const/4 v3, 0x2

    if-lt v2, v3, :cond_1

    const/4 v2, 0x1

    aget-byte v2, v1, v2

    const/16 v3, -0x73

    if-eq v2, v3, :cond_2

    .line 1527
    :cond_1
    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1529
    :cond_2
    goto :goto_0

    .line 1530
    :cond_3
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v1, v0}, Ljava/util/ArrayDeque;->addAll(Ljava/util/Collection;)Z

    .line 1531
    return-void
.end method

.method private requestCameraSpeed(II)V
    .locals 0

    .line 633
    if-lez p2, :cond_2

    if-gt p1, p2, :cond_0

    goto :goto_0

    .line 635
    :cond_0
    add-int/lit8 p2, p2, 0x2

    if-lt p1, p2, :cond_1

    .line 636
    const/4 p1, 0x1

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestOverspeed(Z)V

    goto :goto_1

    .line 639
    :cond_1
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestOverspeed(Z)V

    goto :goto_1

    .line 634
    :cond_2
    :goto_0
    const/4 p1, 0x0

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->requestOverspeed(Z)V

    .line 641
    :goto_1
    return-void
.end method

.method private requestOverspeed(Z)V
    .locals 8

    .line 868
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

    .line 870
    :cond_0
    const/4 p1, 0x0

    .line 872
    :cond_1
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mRequestedOverspeed:Z

    if-ne v0, p1, :cond_2

    .line 873
    return-void

    .line 875
    :cond_2
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mRequestedOverspeed:Z

    .line 876
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedStateRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 877
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-ne v0, p1, :cond_3

    .line 878
    return-void

    .line 881
    :cond_3
    if-eqz p1, :cond_4

    const-wide/16 v0, 0x3e8

    goto :goto_0

    :cond_4
    const-wide/16 v0, 0x7d0

    .line 882
    :goto_0
    const-wide/16 v2, 0x0

    if-nez p1, :cond_5

    iget-wide v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActivatedAtMs:J

    cmp-long v6, v4, v2

    if-lez v6, :cond_5

    .line 883
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v4

    iget-wide v6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActivatedAtMs:J

    sub-long/2addr v4, v6

    .line 884
    const-wide/16 v6, 0xbb8

    sub-long/2addr v6, v4

    invoke-static {v0, v1, v6, v7}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v0

    .line 886
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

    .line 887
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedStateRunnable:Ljava/lang/Runnable;

    invoke-static {v2, v3, v0, v1}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v0

    invoke-virtual {p1, v4, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 888
    return-void
.end method

.method private restoreActiveStateAfterConnect()V
    .locals 4

    .line 1496
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->removePendingAmbientStatePackets()V

    .line 1497
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-eqz v0, :cond_0

    .line 1498
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_OFF:[B

    invoke-virtual {v1}, [B->clone()Ljava/lang/Object;

    move-result-object v1

    check-cast v1, [B

    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1499
    return-void

    .line 1501
    :cond_0
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-eqz v0, :cond_1

    .line 1502
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBlink()V

    .line 1503
    return-void

    .line 1505
    :cond_1
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    if-eqz v0, :cond_3

    .line 1506
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->activeStateColorPacket()[B

    move-result-object v0

    .line 1507
    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->rememberColorPacket([B)V

    .line 1508
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, [B->clone()Ljava/lang/Object;

    move-result-object v0

    check-cast v0, [B

    invoke-virtual {v1, v0}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1509
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_2

    .line 1510
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    goto :goto_0

    .line 1512
    :cond_2
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    iget v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    const/4 v3, 0x1

    invoke-static {v3, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildBrightnessPacket(ZII)[B

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1514
    :goto_0
    return-void

    .line 1516
    :cond_3
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_OFF:[B

    invoke-virtual {v1}, [B->clone()Ljava/lang/Object;

    move-result-object v1

    check-cast v1, [B

    invoke-virtual {v0, v1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1517
    return-void
.end method

.method private static safeName(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;
    .locals 1

    .line 1770
    const-string v0, ""

    :try_start_0
    invoke-virtual {p0}, Landroid/bluetooth/BluetoothDevice;->getName()Ljava/lang/String;

    move-result-object p0
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 1771
    if-nez p0, :cond_0

    goto :goto_0

    :cond_0
    move-object v0, p0

    :goto_0
    return-object v0

    .line 1772
    :catch_0
    move-exception p0

    .line 1773
    return-object v0
.end method

.method private static scanRecordContainsAmbientUuid([B)Z
    .locals 5

    .line 1747
    const/4 v0, 0x0

    if-nez p0, :cond_0

    .line 1748
    return v0

    .line 1750
    :cond_0
    const/4 v1, 0x0

    :goto_0
    add-int/lit8 v2, v1, 0x1

    array-length v3, p0

    if-ge v2, v3, :cond_4

    .line 1751
    aget-byte v1, p0, v1

    and-int/lit16 v1, v1, 0xff

    .line 1752
    aget-byte v3, p0, v2

    and-int/lit16 v3, v3, 0xff

    .line 1753
    if-eqz v1, :cond_1

    const/16 v4, 0x30

    if-ne v1, v4, :cond_2

    :cond_1
    const/16 v1, 0xae

    if-eq v3, v1, :cond_3

    const/16 v1, 0xaf

    if-ne v3, v1, :cond_2

    goto :goto_1

    .line 1750
    :cond_2
    move v1, v2

    goto :goto_0

    .line 1754
    :cond_3
    :goto_1
    const/4 p0, 0x1

    return p0

    .line 1757
    :cond_4
    return v0
.end method

.method private scheduleReconnect()V
    .locals 2

    .line 1389
    const-wide/16 v0, 0x1388

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->scheduleReconnect(J)V

    .line 1390
    return-void
.end method

.method private scheduleReconnect(J)V
    .locals 4

    .line 1393
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

    .line 1396
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1397
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectScheduled:Z

    .line 1398
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

    .line 1399
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReconnectRunnable:Ljava/lang/Runnable;

    const-wide/16 v2, 0x0

    invoke-static {v2, v3, p1, p2}, Ljava/lang/Math;->max(JJ)J

    move-result-wide p1

    invoke-virtual {v0, v1, p1, p2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 1400
    return-void

    .line 1394
    :cond_1
    :goto_0
    return-void
.end method

.method private sendAmbientFrame([B[B)V
    .locals 2

    .line 1207
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->removePendingAmbientStatePackets()V

    .line 1208
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->size()I

    move-result v0

    const/16 v1, 0x12

    if-le v0, v1, :cond_0

    .line 1209
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->poll()Ljava/lang/Object;

    .line 1211
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {p1}, [B->clone()Ljava/lang/Object;

    move-result-object p1

    check-cast p1, [B

    invoke-virtual {v0, p1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1212
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {p2}, [B->clone()Ljava/lang/Object;

    move-result-object p2

    check-cast p2, [B

    invoke-virtual {p1, p2}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1213
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectIfNeeded()V

    .line 1214
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->flushNext()V

    .line 1215
    return-void
.end method

.method private sendPacket([B)V
    .locals 2

    .line 1312
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isColorPacket([B)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 1313
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->rememberColorPacket([B)V

    .line 1315
    :cond_0
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isBrightnessPacket([B)Z

    move-result v0

    if-eqz v0, :cond_1

    .line 1316
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->coalescePendingBrightnessPackets()V

    .line 1318
    :cond_1
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->size()I

    move-result v0

    const/16 v1, 0x14

    if-le v0, v1, :cond_2

    .line 1319
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {v0}, Ljava/util/ArrayDeque;->poll()Ljava/lang/Object;

    .line 1321
    :cond_2
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mQueue:Ljava/util/ArrayDeque;

    invoke-virtual {p1}, [B->clone()Ljava/lang/Object;

    move-result-object p1

    check-cast p1, [B

    invoke-virtual {v0, p1}, Ljava/util/ArrayDeque;->offer(Ljava/lang/Object;)Z

    .line 1322
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->connectIfNeeded()V

    .line 1323
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->flushNext()V

    .line 1324
    return-void
.end method

.method private setAmbientOverride(Lorg/json/JSONObject;)V
    .locals 11

    .line 799
    const-string v0, "mode"

    const-string v1, "manual"

    invoke-virtual {p1, v0, v1}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    .line 800
    const-string v2, "profile"

    invoke-virtual {v2, v0}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    move-result v3

    if-eqz v3, :cond_0

    .line 801
    invoke-virtual {p1, v2}, Lorg/json/JSONObject;->optJSONObject(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setAmbientProfile(Lorg/json/JSONObject;)V

    .line 802
    return-void

    .line 804
    :cond_0
    const-string v2, "auto"

    invoke-virtual {v2, v0}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    move-result v2

    if-eqz v2, :cond_1

    .line 805
    const-string p1, "auto command"

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clearManualOverride(Ljava/lang/String;)V

    .line 806
    return-void

    .line 808
    :cond_1
    invoke-virtual {v1, v0}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    move-result v0

    if-nez v0, :cond_2

    .line 809
    return-void

    .line 811
    :cond_2
    const-string v0, "id"

    const-string v1, ""

    invoke-virtual {p1, v0, v1}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    .line 812
    iget-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v2, :cond_3

    invoke-virtual {v0}, Ljava/lang/String;->length()I

    move-result v2

    if-lez v2, :cond_3

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideId:Ljava/lang/String;

    invoke-virtual {v0, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v2

    if-eqz v2, :cond_3

    .line 813
    return-void

    .line 815
    :cond_3
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v2

    .line 816
    const-string v4, "expiresAt"

    invoke-virtual {p1, v4, v1}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    invoke-static {v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->parseIsoTimeMs(Ljava/lang/String;)J

    move-result-wide v4

    .line 817
    cmp-long v1, v4, v2

    if-gtz v1, :cond_4

    .line 818
    const-string p1, "stale command"

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clearManualOverride(Ljava/lang/String;)V

    .line 819
    return-void

    .line 821
    :cond_4
    const-string v1, "zone1"

    invoke-virtual {p1, v1}, Lorg/json/JSONObject;->optJSONObject(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v1

    .line 822
    const-string v6, "zone2"

    invoke-virtual {p1, v6}, Lorg/json/JSONObject;->optJSONObject(Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object p1

    .line 823
    if-eqz v1, :cond_7

    if-nez p1, :cond_5

    goto/16 :goto_0

    .line 826
    :cond_5
    iput-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideId:Ljava/lang/String;

    .line 827
    const-string v6, "enabled"

    const/4 v7, 0x1

    invoke-virtual {v1, v6, v7}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v8

    iput-boolean v8, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Enabled:Z

    .line 828
    invoke-virtual {p1, v6, v7}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v6

    iput-boolean v6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Enabled:Z

    .line 829
    const/4 v6, 0x0

    const/16 v8, 0xff

    invoke-static {v1, v6, v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v9

    iput v9, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Red:I

    .line 830
    invoke-static {v1, v7, v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v9

    iput v9, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Green:I

    .line 831
    const/4 v9, 0x2

    invoke-static {v1, v9, v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v10

    iput v10, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Blue:I

    .line 832
    invoke-static {p1, v6, v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v6

    iput v6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Red:I

    .line 833
    invoke-static {p1, v7, v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v6

    iput v6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Green:I

    .line 834
    invoke-static {p1, v9, v8}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v6

    iput v6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Blue:I

    .line 835
    const/16 v6, 0x14

    const-string v8, "brightness"

    const/16 v9, 0x64

    invoke-static {v1, v8, v6, v9}, Lcom/navdy/hud/app/ambient/AmbientLightController;->zoneValue(Lorg/json/JSONObject;Ljava/lang/String;II)I

    move-result v1

    iput v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone1Brightness:I

    .line 836
    const/16 v1, 0x28

    invoke-static {p1, v8, v1, v9}, Lcom/navdy/hud/app/ambient/AmbientLightController;->zoneValue(Lorg/json/JSONObject;Ljava/lang/String;II)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Brightness:I

    .line 837
    const-wide/32 v8, 0x124f80

    add-long/2addr v8, v2

    invoke-static {v4, v5, v8, v9}, Ljava/lang/Math;->min(JJ)J

    move-result-wide v4

    iput-wide v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiresAtMs:J

    .line 838
    iput-boolean v7, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    .line 839
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->cancelOffroadTimers()V

    .line 840
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiryRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 841
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiryRunnable:Ljava/lang/Runnable;

    iget-wide v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiresAtMs:J

    sub-long/2addr v4, v2

    .line 842
    const-wide/16 v2, 0x1

    invoke-static {v2, v3, v4, v5}, Ljava/lang/Math;->max(JJ)J

    move-result-wide v2

    .line 841
    invoke-virtual {p1, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 843
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

    .line 844
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez p1, :cond_6

    .line 845
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->applyVehicleStateTargets()V

    .line 847
    :cond_6
    return-void

    .line 824
    :cond_7
    :goto_0
    return-void
.end method

.method private setAmbientProfile(Lorg/json/JSONObject;)V
    .locals 2

    .line 692
    if-nez p1, :cond_0

    .line 693
    return-void

    .line 695
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

    .line 696
    return-void

    .line 698
    :cond_1
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mProfile:Lorg/json/JSONObject;

    .line 699
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mContext:Landroid/content/Context;

    .line 700
    invoke-virtual {v0}, Landroid/content/Context;->getContentResolver()Landroid/content/ContentResolver;

    move-result-object v0

    invoke-virtual {p1}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object p1

    .line 699
    const-string v1, "navdy_ambient_profile_json"

    invoke-static {v0, v1, p1}, Landroid/provider/Settings$System;->putString(Landroid/content/ContentResolver;Ljava/lang/String;Ljava/lang/String;)Z

    .line 701
    const/4 p1, 0x0

    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    .line 702
    const-wide/16 v0, 0x0

    iput-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiresAtMs:J

    .line 703
    const-string p1, ""

    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideId:Ljava/lang/String;

    .line 704
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideExpiryRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 705
    const-string p1, "NavdyAmbient"

    const-string v0, "ambient profile saved"

    invoke-static {p1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 706
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileMasterEnabled()Z

    move-result p1

    if-nez p1, :cond_2

    .line 707
    const-string p1, "profile disabled"

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    goto :goto_0

    .line 708
    :cond_2
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez p1, :cond_3

    .line 709
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->applyVehicleStateTargets()V

    .line 711
    :cond_3
    :goto_0
    return-void
.end method

.method private setGearText(Ljava/lang/String;)V
    .locals 3

    .line 891
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalizeGear(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    .line 892
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastGear:Ljava/lang/String;

    invoke-virtual {p1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 893
    return-void

    .line 895
    :cond_0
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastGear:Ljava/lang/String;

    .line 896
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

    .line 898
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isReverse(Ljava/lang/String;)Z

    move-result v0

    const/4 v1, 0x1

    if-eqz v0, :cond_2

    .line 899
    const-string p1, "reverseOff"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result p1

    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    .line 900
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez p1, :cond_1

    .line 901
    return-void

    .line 903
    :cond_1
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 904
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBrightnessSync()V

    .line 905
    const-string p1, "reverse"

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    .line 906
    return-void

    .line 909
    :cond_2
    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->isDriveGear(Ljava/lang/String;)Z

    move-result p1

    if-eqz p1, :cond_5

    .line 910
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    .line 911
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    .line 912
    if-eqz p1, :cond_4

    .line 913
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    if-eqz p1, :cond_3

    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz p1, :cond_3

    .line 914
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    goto :goto_0

    .line 916
    :cond_3
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->applyVehicleStateTargets()V

    goto :goto_0

    .line 918
    :cond_4
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    if-nez p1, :cond_5

    .line 919
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    .line 920
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 921
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    .line 922
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone1Brightness()I

    move-result p1

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result v0

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v1

    invoke-direct {p0, p1, v0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    .line 925
    :cond_5
    :goto_0
    return-void
.end method

.method private setOverspeed(Z)V
    .locals 2

    .line 1065
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-ne v0, p1, :cond_0

    .line 1066
    return-void

    .line 1068
    :cond_0
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    .line 1069
    if-eqz p1, :cond_1

    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v0

    goto :goto_0

    :cond_1
    const-wide/16 v0, 0x0

    :goto_0
    iput-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActivatedAtMs:J

    .line 1070
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

    .line 1071
    if-eqz p1, :cond_2

    .line 1072
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz p1, :cond_4

    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez p1, :cond_4

    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-nez p1, :cond_4

    .line 1073
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBlink()V

    goto :goto_1

    .line 1076
    :cond_2
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez p1, :cond_3

    .line 1077
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->beginRestoreFade()V

    goto :goto_1

    .line 1079
    :cond_3
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 1082
    :cond_4
    :goto_1
    return-void
.end method

.method private setVehicleState(ZZ)V
    .locals 7

    .line 935
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    .line 936
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

    .line 937
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

    .line 938
    :goto_3
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleStateKnown:Z

    .line 939
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    .line 940
    iput-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    .line 941
    iput-boolean p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    .line 942
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->updateCpuWakeLock()V

    .line 943
    if-nez v3, :cond_4

    if-eqz v4, :cond_5

    .line 944
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

    .line 947
    :cond_5
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileMasterEnabled()Z

    move-result v5

    if-nez v5, :cond_6

    iget-boolean v5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-nez v5, :cond_6

    .line 948
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->cancelOffroadTimers()V

    .line 949
    const-string p1, "profile disabled"

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    .line 950
    return-void

    .line 953
    :cond_6
    if-eqz p1, :cond_9

    .line 954
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mExitCourtesyActive:Z

    .line 955
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->cancelOffroadTimers()V

    .line 956
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    .line 957
    if-eqz v3, :cond_7

    .line 958
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startBrightnessSync()V

    goto :goto_4

    .line 959
    :cond_7
    if-eqz v4, :cond_8

    .line 960
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->applyVehicleStateTargets()V

    .line 962
    :cond_8
    :goto_4
    return-void

    .line 965
    :cond_9
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBrightnessSync()V

    .line 966
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mRequestedOverspeed:Z

    .line 967
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedStateRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, v5}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 968
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOverspeedActive:Z

    if-eqz p1, :cond_a

    .line 969
    invoke-direct {p0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->setOverspeed(Z)V

    .line 972
    :cond_a
    if-eqz p2, :cond_10

    .line 973
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mExitCourtesyActive:Z

    .line 974
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 975
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 976
    const-string p1, "offroadDoor"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result p1

    if-nez p1, :cond_b

    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-nez p1, :cond_b

    .line 977
    const-string p1, "offroad door profile disabled"

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->hardAmbientOff(Ljava/lang/String;)V

    .line 978
    return-void

    .line 980
    :cond_b
    if-nez v4, :cond_c

    if-eqz v3, :cond_d

    .line 981
    :cond_c
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    .line 982
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 983
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxRunnable:Ljava/lang/Runnable;

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileDoorMaxOnMs()J

    move-result-wide v0

    invoke-virtual {p1, p2, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 985
    :cond_d
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    if-nez p1, :cond_f

    if-nez v4, :cond_e

    if-eqz v3, :cond_f

    .line 986
    :cond_e
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->offroadDoorZone1Brightness()I

    move-result p1

    .line 987
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->offroadDoorZone2Brightness()I

    move-result p2

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v0

    .line 986
    invoke-direct {p0, p1, p2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    .line 989
    :cond_f
    return-void

    .line 992
    :cond_10
    iget-boolean p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz p1, :cond_11

    .line 993
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->cancelOffroadTimers()V

    .line 994
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone1Brightness()I

    move-result p1

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result p2

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v0

    invoke-direct {p0, p1, p2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    .line 995
    return-void

    .line 998
    :cond_11
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 999
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorMaxExpired:Z

    .line 1000
    if-eqz v4, :cond_12

    if-eqz v0, :cond_12

    .line 1001
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1002
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1003
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileDoorCloseDelayMs()J

    move-result-wide v0

    invoke-virtual {p1, p2, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    goto :goto_5

    .line 1004
    :cond_12
    if-eqz v0, :cond_14

    if-eqz v3, :cond_14

    .line 1005
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1006
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1007
    const-string p1, "exitCourtesy"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result p1

    if-eqz p1, :cond_13

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileExitCourtesyMs()J

    move-result-wide p1

    const-wide/16 v3, 0x0

    cmp-long v0, p1, v3

    if-lez v0, :cond_13

    .line 1008
    iput-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mExitCourtesyActive:Z

    .line 1009
    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->exitCourtesyZone2Brightness()I

    move-result p2

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v0

    invoke-direct {p0, p1, p2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    .line 1010
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileExitCourtesyMs()J

    move-result-wide v0

    invoke-virtual {p1, p2, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    goto :goto_5

    .line 1012
    :cond_13
    iput-boolean v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mExitCourtesyActive:Z

    .line 1013
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide p1

    invoke-direct {p0, v2, v2, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    goto :goto_5

    .line 1015
    :cond_14
    if-nez v0, :cond_15

    .line 1016
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1017
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDoorCloseRunnable:Ljava/lang/Runnable;

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1018
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOffroadDelayedOffRunnable:Ljava/lang/Runnable;

    const-wide/32 v0, 0xea60

    invoke-virtual {p1, p2, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 1020
    :cond_15
    :goto_5
    return-void
.end method

.method private startAmbientFade(IIJ)V
    .locals 6

    .line 1150
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->activeStateColorPacket()[B

    move-result-object v5

    move-object v0, p0

    move v1, p1

    move v2, p2

    move-wide v3, p3

    invoke-direct/range {v0 .. v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ[B)V

    .line 1151
    return-void
.end method

.method private startAmbientFade(IIJ[B)V
    .locals 2

    .line 1154
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1155
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->removePendingAmbientStatePackets()V

    .line 1156
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1:I

    .line 1157
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2:I

    .line 1158
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Red:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1Red:I

    .line 1159
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Green:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1Green:I

    .line 1160
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone1Blue:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone1Blue:I

    .line 1161
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Red:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2Red:I

    .line 1162
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Green:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2Green:I

    .line 1163
    iget v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCurrentZone2Blue:I

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartZone2Blue:I

    .line 1164
    const/4 v0, 0x0

    const/16 v1, 0x64

    invoke-static {p1, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    .line 1165
    invoke-static {p2, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->clamp(III)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    .line 1166
    const/4 p1, 0x5

    const/16 p2, 0xff

    invoke-static {p5, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1Red:I

    .line 1167
    const/4 p1, 0x6

    invoke-static {p5, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1Green:I

    .line 1168
    const/4 p1, 0x7

    invoke-static {p5, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1Blue:I

    .line 1169
    const/16 p1, 0x8

    invoke-static {p5, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2Red:I

    .line 1170
    const/16 p1, 0x9

    invoke-static {p5, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2Green:I

    .line 1171
    const/16 p1, 0xa

    invoke-static {p5, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorPacketValue([BII)I

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2Blue:I

    .line 1172
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide p1

    iput-wide p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeStartedAtMs:J

    .line 1173
    const-wide/16 p1, 0x0

    invoke-static {p1, p2, p3, p4}, Ljava/lang/Math;->max(JJ)J

    move-result-wide p3

    iput-wide p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeDurationMs:J

    .line 1174
    iget p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    if-gtz p3, :cond_0

    iget p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    if-lez p3, :cond_1

    .line 1175
    :cond_0
    const/4 p3, 0x1

    iput-boolean p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 1177
    :cond_1
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientFrameStepMs()I

    move-result p3

    int-to-long p3, p3

    iget-wide v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeDurationMs:J

    invoke-static {p3, p4, v0, v1}, Ljava/lang/Math;->min(JJ)J

    move-result-wide p3

    .line 1178
    iget-object p5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientFadeRunnable:Ljava/lang/Runnable;

    invoke-static {p1, p2, p3, p4}, Ljava/lang/Math;->max(JJ)J

    move-result-wide p1

    invoke-virtual {p5, v0, p1, p2}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 1179
    return-void
.end method

.method private startBlink()V
    .locals 7

    .line 1085
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez v0, :cond_1

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-eqz v0, :cond_0

    move-object v1, p0

    goto :goto_0

    .line 1088
    :cond_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBlink()V

    .line 1089
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->stopBrightnessSync()V

    .line 1090
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientActive:Z

    .line 1091
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->readAmbientBrightness()I

    move-result v2

    .line 1092
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFadeMs()J

    move-result-wide v4

    .line 1093
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->warningZone2Brightness()I

    move-result v3

    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->warningColorPacket()[B

    move-result-object v6

    move-object v1, p0

    invoke-direct/range {v1 .. v6}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ[B)V

    .line 1094
    iget-object v0, v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v2, v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningStepStartRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v2, v4, v5}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 1095
    return-void

    .line 1085
    :cond_1
    move-object v1, p0

    .line 1086
    :goto_0
    return-void
.end method

.method private startBrightnessSync()V
    .locals 4

    .line 1118
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1119
    const/4 v0, 0x1

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->syncAmbientBrightness(Z)V

    .line 1120
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    const-wide/16 v2, 0x1388

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 1121
    return-void
.end method

.method private stopBlink()V
    .locals 2

    .line 1098
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBlinkRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1099
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningStepStartRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1100
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningAnimationStarted:Z

    .line 1101
    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLowLightWarning:Z

    .line 1102
    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDayWarningDimmed:Z

    .line 1103
    return-void
.end method

.method private stopBrightnessSync()V
    .locals 2

    .line 1124
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mBrightnessSyncRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1125
    const/4 v0, -0x1

    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 1126
    return-void
.end method

.method private stopScan()V
    .locals 2

    .line 1451
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    if-eqz v0, :cond_1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    if-nez v0, :cond_0

    goto :goto_0

    .line 1454
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAdapter:Landroid/bluetooth/BluetoothAdapter;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanCallback:Landroid/bluetooth/BluetoothAdapter$LeScanCallback;

    invoke-virtual {v0, v1}, Landroid/bluetooth/BluetoothAdapter;->stopLeScan(Landroid/bluetooth/BluetoothAdapter$LeScanCallback;)V

    .line 1455
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mScanning:Z

    .line 1456
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mStopScanRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 1457
    const-string v0, "NavdyAmbient"

    const-string v1, "ambient scan stop"

    invoke-static {v0, v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 1458
    return-void

    .line 1452
    :cond_1
    :goto_0
    return-void
.end method

.method private syncAmbientBrightness(Z)V
    .locals 4

    .line 1129
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mOnroad:Z

    if-eqz v0, :cond_5

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mReverseActive:Z

    if-nez v0, :cond_5

    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mVehicleDataTimedOut:Z

    if-eqz v0, :cond_0

    goto :goto_0

    .line 1132
    :cond_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->activeOnroadZone1Brightness()I

    move-result v0

    .line 1133
    iget-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWarningAnimationStarted:Z

    if-eqz v1, :cond_1

    .line 1134
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 1135
    return-void

    .line 1137
    :cond_1
    if-nez p1, :cond_2

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    if-ltz v1, :cond_2

    iget v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    sub-int v1, v0, v1

    .line 1138
    invoke-static {v1}, Ljava/lang/Math;->abs(I)I

    move-result v1

    const/4 v2, 0x2

    if-ge v1, v2, :cond_2

    .line 1139
    return-void

    .line 1141
    :cond_2
    iput v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mLastAmbientBrightness:I

    .line 1142
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

    .line 1143
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->activeOnroadZone2Brightness()I

    move-result v1

    .line 1144
    if-nez p1, :cond_3

    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone1:I

    if-ne v0, p1, :cond_3

    iget p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mAmbientTargetZone2:I

    if-eq v1, p1, :cond_4

    .line 1145
    :cond_3
    const-wide/16 v2, 0x3e8

    invoke-direct {p0, v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->startAmbientFade(IIJ)V

    .line 1147
    :cond_4
    return-void

    .line 1130
    :cond_5
    :goto_0
    return-void
.end method

.method private updateCpuWakeLock()V
    .locals 3

    .line 1023
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    if-nez v0, :cond_0

    .line 1024
    return-void

    .line 1026
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

    .line 1027
    :goto_0
    const-string v1, "NavdyAmbient"

    if-eqz v0, :cond_2

    iget-object v2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    invoke-virtual {v2}, Landroid/os/PowerManager$WakeLock;->isHeld()Z

    move-result v2

    if-nez v2, :cond_2

    .line 1028
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    invoke-virtual {v0}, Landroid/os/PowerManager$WakeLock;->acquire()V

    .line 1029
    const-string v0, "offroad ambient CPU wake lock acquired"

    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    goto :goto_1

    .line 1030
    :cond_2
    if-nez v0, :cond_3

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    invoke-virtual {v0}, Landroid/os/PowerManager$WakeLock;->isHeld()Z

    move-result v0

    if-eqz v0, :cond_3

    .line 1031
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mCpuWakeLock:Landroid/os/PowerManager$WakeLock;

    invoke-virtual {v0}, Landroid/os/PowerManager$WakeLock;->release()V

    .line 1032
    const-string v0, "offroad ambient CPU wake lock released"

    invoke-static {v1, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 1034
    :cond_3
    :goto_1
    return-void
.end method

.method private static usesPacedWrite([B)Z
    .locals 1

    .line 1615
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

    .line 1299
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualOverrideActive:Z

    if-eqz v0, :cond_0

    .line 1300
    iget v4, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Red:I

    iget v5, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Green:I

    iget v6, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mManualZone2Blue:I

    const/16 v1, 0xff

    const/4 v2, 0x0

    const/4 v3, 0x0

    invoke-static/range {v1 .. v6}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildColorPacket(IIIIII)[B

    move-result-object v0

    return-object v0

    .line 1303
    :cond_0
    const-string v0, "overspeed"

    const-string v1, "zone1"

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileZone(Ljava/lang/String;Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v0

    .line 1304
    iget-boolean v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    const-string v2, "zone2"

    const/4 v3, 0x1

    if-eqz v1, :cond_1

    const-string v1, "onroadDoor"

    invoke-direct {p0, v1, v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result v4

    if-eqz v4, :cond_1

    .line 1305
    goto :goto_0

    :cond_1
    const-string v1, "driving"

    :goto_0
    invoke-direct {p0, v1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileZone(Ljava/lang/String;Ljava/lang/String;)Lorg/json/JSONObject;

    move-result-object v1

    .line 1306
    nop

    .line 1307
    const/4 v2, 0x0

    const/16 v4, 0xff

    invoke-static {v0, v2, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v5

    invoke-static {v0, v3, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v6

    const/4 v7, 0x2

    invoke-static {v0, v7, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v0

    .line 1308
    invoke-static {v1, v2, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v8

    invoke-static {v1, v3, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v9

    invoke-static {v1, v7, v4}, Lcom/navdy/hud/app/ambient/AmbientLightController;->colorValue(Lorg/json/JSONObject;II)I

    move-result v10

    .line 1306
    move v7, v0

    invoke-static/range {v5 .. v10}, Lcom/navdy/hud/app/ambient/AmbientLightController;->buildColorPacket(IIIIII)[B

    move-result-object v0

    return-object v0
.end method

.method private warningZone2Brightness()I
    .locals 2

    .line 1229
    iget-boolean v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mDoorOpen:Z

    if-eqz v0, :cond_0

    const-string v0, "onroadDoor"

    const/4 v1, 0x1

    invoke-direct {p0, v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->profileFeatureEnabled(Ljava/lang/String;Z)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 1230
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onroadDoorZone2Brightness()I

    move-result v0

    goto :goto_0

    :cond_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->normalZone2Brightness()I

    move-result v0

    .line 1229
    :goto_0
    return v0
.end method

.method private writeAck()V
    .locals 3

    .line 1534
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    if-eqz v0, :cond_1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    if-nez v0, :cond_0

    goto :goto_0

    .line 1537
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    sget-object v1, Lcom/navdy/hud/app/ambient/AmbientLightController;->PACKET_ACK:[B

    invoke-virtual {v0, v1}, Landroid/bluetooth/BluetoothGattCharacteristic;->setValue([B)Z

    .line 1538
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->configureWriteCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)V

    .line 1539
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mGatt:Landroid/bluetooth/BluetoothGatt;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController;->mWriteCharacteristic:Landroid/bluetooth/BluetoothGattCharacteristic;

    invoke-virtual {v0, v1}, Landroid/bluetooth/BluetoothGatt;->writeCharacteristic(Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result v0

    .line 1540
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

    .line 1541
    return-void

    .line 1535
    :cond_1
    :goto_0
    return-void
.end method

.method private static zoneValue(Lorg/json/JSONObject;Ljava/lang/String;II)I
    .locals 0

    .line 666
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
