.class public Lcom/navdy/hud/app/device/PowerManager;
.super Ljava/lang/Object;
.source "PowerManager.java"


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        Lcom/navdy/hud/app/device/PowerManager$RunState;
    }
.end annotation


# static fields
.field public static final BOOT_POWER_MODE:Ljava/lang/String;

.field private static final COOLING_DEVICE:Ljava/lang/String; = "/sys/devices/virtual/thermal/cooling_device0/cur_state"

.field private static final COOLING_MONITOR_INTERVAL:J

.field private static final DEFAULT_INSTANT_ON_TIMEOUT:J

.field private static final INSTANT_ON:Ljava/lang/String; = "persist.sys.instanton"

.field private static final INSTANT_ON_TIMEOUT:J

.field private static final INSTANT_ON_TIMEOUT_PROPERTRY:Ljava/lang/String; = "persist.sys.instanton.timeout"

.field public static final LAST_LOW_VOLTAGE_EVENT:Ljava/lang/String; = "last_low_voltage_event"

.field public static final NORMAL_MODE:Ljava/lang/String; = "normal"

.field public static final POWER_MODE_PROPERTY:Ljava/lang/String; = "sys.power.mode"

.field public static final QUIET_MODE:Ljava/lang/String; = "quiet"

.field public static final RECHARGE_TIME:J

.field private static final sLogger:Lcom/navdy/service/library/log/Logger;


# instance fields
.field private awake:Z

.field private bus:Lcom/squareup/otto/Bus;

.field private checkCoolingState:Ljava/lang/Runnable;

.field private handler:Landroid/os/Handler;

.field private lastLowVoltage:J

.field private mIPowerManagerShutdownMethod:Ljava/lang/reflect/Method;

.field private mPowerManager:Ljava/lang/Object;

.field private oldCoolingState:Ljava/lang/String;

.field private powerManager:Landroid/os/PowerManager;

.field private preferences:Landroid/content/SharedPreferences;

.field private quietModeTimeout:Ljava/lang/Runnable;

.field private runState:Lcom/navdy/hud/app/device/PowerManager$RunState;


# direct methods
.method static constructor <clinit>()V
    .locals 4

    .prologue
    .line 44
    new-instance v0, Lcom/navdy/service/library/log/Logger;

    const-class v1, Lcom/navdy/hud/app/device/PowerManager;

    invoke-direct {v0, v1}, Lcom/navdy/service/library/log/Logger;-><init>(Ljava/lang/Class;)V

    sput-object v0, Lcom/navdy/hud/app/device/PowerManager;->sLogger:Lcom/navdy/service/library/log/Logger;

    .line 52
    const-string/jumbo v0, "sys.power.mode"

    invoke-static {v0}, Lcom/navdy/hud/app/util/os/SystemProperties;->get(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    sput-object v0, Lcom/navdy/hud/app/device/PowerManager;->BOOT_POWER_MODE:Ljava/lang/String;

    .line 63
    sget-object v0, Ljava/util/concurrent/TimeUnit;->SECONDS:Ljava/util/concurrent/TimeUnit;

    const-wide/16 v2, 0xf

    invoke-virtual {v0, v2, v3}, Ljava/util/concurrent/TimeUnit;->toMillis(J)J

    move-result-wide v0

    sput-wide v0, Lcom/navdy/hud/app/device/PowerManager;->COOLING_MONITOR_INTERVAL:J

    .line 72
    sget-object v0, Ljava/util/concurrent/TimeUnit;->HOURS:Ljava/util/concurrent/TimeUnit;

    const-wide/16 v2, 0x4

    invoke-virtual {v0, v2, v3}, Ljava/util/concurrent/TimeUnit;->toMillis(J)J

    move-result-wide v0

    sput-wide v0, Lcom/navdy/hud/app/device/PowerManager;->DEFAULT_INSTANT_ON_TIMEOUT:J

    .line 74
    const-string/jumbo v0, "persist.sys.instanton.timeout"

    sget-wide v2, Lcom/navdy/hud/app/device/PowerManager;->DEFAULT_INSTANT_ON_TIMEOUT:J

    .line 75
    invoke-static {v0, v2, v3}, Lcom/navdy/hud/app/util/os/SystemProperties;->getLong(Ljava/lang/String;J)J

    move-result-wide v0

    sput-wide v0, Lcom/navdy/hud/app/device/PowerManager;->INSTANT_ON_TIMEOUT:J

    .line 80
    sget-object v0, Ljava/util/concurrent/TimeUnit;->DAYS:Ljava/util/concurrent/TimeUnit;

    const-wide/16 v2, 0x7

    invoke-virtual {v0, v2, v3}, Ljava/util/concurrent/TimeUnit;->toMillis(J)J

    move-result-wide v0

    sput-wide v0, Lcom/navdy/hud/app/device/PowerManager;->RECHARGE_TIME:J

    return-void
.end method

.method public constructor <init>(Lcom/squareup/otto/Bus;Landroid/content/Context;Landroid/content/SharedPreferences;)V
    .locals 4
    .param p1, "bus"    # Lcom/squareup/otto/Bus;
    .param p2, "context"    # Landroid/content/Context;
    .param p3, "preferences"    # Landroid/content/SharedPreferences;

    .prologue
    const/4 v2, 0x0

    .line 85
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 65
    const-string/jumbo v0, "quiet"

    sget-object v1, Lcom/navdy/hud/app/device/PowerManager;->BOOT_POWER_MODE:Ljava/lang/String;

    invoke-virtual {v0, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1

    const/4 v0, 0x1

    :goto_0
    iput-boolean v0, p0, Lcom/navdy/hud/app/device/PowerManager;->awake:Z

    .line 68
    new-instance v0, Landroid/os/Handler;

    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object v1

    invoke-direct {v0, v1}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    iput-object v0, p0, Lcom/navdy/hud/app/device/PowerManager;->handler:Landroid/os/Handler;

    .line 138
    new-instance v0, Lcom/navdy/hud/app/device/PowerManager$Anon1;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/device/PowerManager$Anon1;-><init>(Lcom/navdy/hud/app/device/PowerManager;)V

    iput-object v0, p0, Lcom/navdy/hud/app/device/PowerManager;->checkCoolingState:Ljava/lang/Runnable;

    .line 204
    new-instance v0, Lcom/navdy/hud/app/device/PowerManager$Anon2;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/device/PowerManager$Anon2;-><init>(Lcom/navdy/hud/app/device/PowerManager;)V

    iput-object v0, p0, Lcom/navdy/hud/app/device/PowerManager;->quietModeTimeout:Ljava/lang/Runnable;

    .line 263
    iput-object v2, p0, Lcom/navdy/hud/app/device/PowerManager;->mIPowerManagerShutdownMethod:Ljava/lang/reflect/Method;

    .line 264
    iput-object v2, p0, Lcom/navdy/hud/app/device/PowerManager;->mPowerManager:Ljava/lang/Object;

    .line 86
    iput-object p1, p0, Lcom/navdy/hud/app/device/PowerManager;->bus:Lcom/squareup/otto/Bus;

    .line 87
    invoke-virtual {p1, p0}, Lcom/squareup/otto/Bus;->register(Ljava/lang/Object;)V

    .line 89
    const-string/jumbo v0, "power"

    invoke-virtual {p2, v0}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Landroid/os/PowerManager;

    iput-object v0, p0, Lcom/navdy/hud/app/device/PowerManager;->powerManager:Landroid/os/PowerManager;

    .line 91
    iput-object p3, p0, Lcom/navdy/hud/app/device/PowerManager;->preferences:Landroid/content/SharedPreferences;

    .line 92
    const-string v0, "last_low_voltage_event"

    const-wide/16 v2, -0x1

    invoke-interface {p3, v0, v2, v3}, Landroid/content/SharedPreferences;->getLong(Ljava/lang/String;J)J

    move-result-wide v0

    iput-wide v0, p0, Lcom/navdy/hud/app/device/PowerManager;->lastLowVoltage:J

    .line 94
    invoke-direct {p0}, Lcom/navdy/hud/app/device/PowerManager;->setupShutdown()V

    .line 96
    const-string/jumbo v1, "sys.power.mode"

    invoke-virtual {p0}, Lcom/navdy/hud/app/device/PowerManager;->inQuietMode()Z

    move-result v0

    if-eqz v0, :cond_2

    const-string/jumbo v0, "quiet"

    :goto_1
    invoke-static {v1, v0}, Lcom/navdy/hud/app/util/os/SystemProperties;->set(Ljava/lang/String;Ljava/lang/String;)V

    .line 98
    invoke-virtual {p0}, Lcom/navdy/hud/app/device/PowerManager;->inQuietMode()Z

    move-result v0

    if-nez v0, :cond_0

    .line 99
    sget-object v0, Lcom/navdy/hud/app/device/PowerManager$RunState;->Booting:Lcom/navdy/hud/app/device/PowerManager$RunState;

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/device/PowerManager;->startOverheatMonitoring(Lcom/navdy/hud/app/device/PowerManager$RunState;)V

    .line 102
    :cond_0
    sget-object v0, Lcom/navdy/hud/app/device/PowerManager;->sLogger:Lcom/navdy/service/library/log/Logger;

    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string/jumbo v2, "quietMode:"

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {p0}, Lcom/navdy/hud/app/device/PowerManager;->inQuietMode()Z

    move-result v2

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, v1}, Lcom/navdy/service/library/log/Logger;->i(Ljava/lang/String;)V

    .line 103
    return-void

    .line 65
    :cond_1
    const/4 v0, 0x0

    goto :goto_0

    .line 96
    :cond_2
    const-string v0, "normal"

    goto :goto_1
.end method

.method static synthetic access$Anon000(Lcom/navdy/hud/app/device/PowerManager;)Z
    .locals 1
    .param p0, "x0"    # Lcom/navdy/hud/app/device/PowerManager;

    .prologue
    .line 43
    invoke-direct {p0}, Lcom/navdy/hud/app/device/PowerManager;->updateCoolingState()Z

    move-result v0

    return v0
.end method

.method static synthetic access$Anon100(Lcom/navdy/hud/app/device/PowerManager;)Ljava/lang/Runnable;
    .locals 1
    .param p0, "x0"    # Lcom/navdy/hud/app/device/PowerManager;

    .prologue
    .line 43
    iget-object v0, p0, Lcom/navdy/hud/app/device/PowerManager;->checkCoolingState:Ljava/lang/Runnable;

    return-object v0
.end method

.method static synthetic access$Anon200()J
    .locals 2

    .prologue
    .line 43
    sget-wide v0, Lcom/navdy/hud/app/device/PowerManager;->COOLING_MONITOR_INTERVAL:J

    return-wide v0
.end method

.method static synthetic access$Anon300(Lcom/navdy/hud/app/device/PowerManager;)Landroid/os/Handler;
    .locals 1
    .param p0, "x0"    # Lcom/navdy/hud/app/device/PowerManager;

    .prologue
    .line 43
    iget-object v0, p0, Lcom/navdy/hud/app/device/PowerManager;->handler:Landroid/os/Handler;

    return-object v0
.end method

.method static synthetic access$Anon400()Lcom/navdy/service/library/log/Logger;
    .locals 1

    .prologue
    .line 43
    sget-object v0, Lcom/navdy/hud/app/device/PowerManager;->sLogger:Lcom/navdy/service/library/log/Logger;

    return-object v0
.end method

.method static synthetic access$Anon500(Lcom/navdy/hud/app/device/PowerManager;)Lcom/squareup/otto/Bus;
    .locals 1
    .param p0, "x0"    # Lcom/navdy/hud/app/device/PowerManager;

    .prologue
    .line 43
    iget-object v0, p0, Lcom/navdy/hud/app/device/PowerManager;->bus:Lcom/squareup/otto/Bus;

    return-object v0
.end method

.method private androidSleep()V
    .locals 8

    .prologue
    const/4 v5, 0x1

    .line 227
    sget-object v3, Lcom/navdy/hud/app/device/PowerManager;->sLogger:Lcom/navdy/service/library/log/Logger;

    const-string v4, "androidSleep()"

    invoke-virtual {v3, v4}, Lcom/navdy/service/library/log/Logger;->d(Ljava/lang/String;)V

    .line 229
    invoke-static {}, Lcom/navdy/hud/app/framework/toast/ToastManager;->getInstance()Lcom/navdy/hud/app/framework/toast/ToastManager;

    move-result-object v3

    invoke-virtual {v3, v5}, Lcom/navdy/hud/app/framework/toast/ToastManager;->disableToasts(Z)V

    .line 233
    const-class v1, Landroid/os/PowerManager;

    .line 235
    .local v1, "powerManagerClass":Ljava/lang/Class;
    :try_start_0
    const-string v3, "goToSleep"

    const/4 v4, 0x1

    new-array v4, v4, [Ljava/lang/Class;

    const/4 v5, 0x0

    sget-object v6, Ljava/lang/Long;->TYPE:Ljava/lang/Class;

    aput-object v6, v4, v5

    invoke-virtual {v1, v3, v4}, Ljava/lang/Class;->getMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    move-result-object v2

    .line 236
    .local v2, "sleepMethod":Ljava/lang/reflect/Method;
    iget-object v3, p0, Lcom/navdy/hud/app/device/PowerManager;->powerManager:Landroid/os/PowerManager;

    const/4 v4, 0x1

    new-array v4, v4, [Ljava/lang/Object;

    const/4 v5, 0x0

    invoke-static {}, Landroid/os/SystemClock;->uptimeMillis()J

    move-result-wide v6

    invoke-static {v6, v7}, Ljava/lang/Long;->valueOf(J)Ljava/lang/Long;

    move-result-object v6

    aput-object v6, v4, v5

    invoke-virtual {v2, v3, v4}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 240
    .end local v2    # "sleepMethod":Ljava/lang/reflect/Method;
    :goto_0
    return-void

    .line 237
    :catch_0
    move-exception v0

    .line 238
    .local v0, "e":Ljava/lang/Exception;
    sget-object v3, Lcom/navdy/hud/app/device/PowerManager;->sLogger:Lcom/navdy/service/library/log/Logger;

    new-instance v4, Ljava/lang/StringBuilder;

    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    const-string v5, "error invoking PowerManager.goToSleep(): "

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    invoke-virtual {v4, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    move-result-object v4

    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v4

    invoke-virtual {v3, v4}, Lcom/navdy/service/library/log/Logger;->e(Ljava/lang/String;)V

    goto :goto_0
.end method

.method private androidWakeup()V
    .locals 8

    .prologue
    const/4 v4, 0x0

    .line 213
    invoke-static {}, Lcom/navdy/hud/app/framework/toast/ToastManager;->getInstance()Lcom/navdy/hud/app/framework/toast/ToastManager;

    move-result-object v3

    invoke-virtual {v3, v4}, Lcom/navdy/hud/app/framework/toast/ToastManager;->disableToasts(Z)V

    .line 217
    const-class v1, Landroid/os/PowerManager;

    .line 219
    .local v1, "powerManagerClass":Ljava/lang/Class;
    :try_start_0
    const-string/jumbo v3, "wakeUp"

    const/4 v4, 0x1

    new-array v4, v4, [Ljava/lang/Class;

    const/4 v5, 0x0

    sget-object v6, Ljava/lang/Long;->TYPE:Ljava/lang/Class;

    aput-object v6, v4, v5

    invoke-virtual {v1, v3, v4}, Ljava/lang/Class;->getMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    move-result-object v2

    .line 220
    .local v2, "wakeupMethod":Ljava/lang/reflect/Method;
    iget-object v3, p0, Lcom/navdy/hud/app/device/PowerManager;->powerManager:Landroid/os/PowerManager;

    const/4 v4, 0x1

    new-array v4, v4, [Ljava/lang/Object;

    const/4 v5, 0x0

    invoke-static {}, Landroid/os/SystemClock;->uptimeMillis()J

    move-result-wide v6

    invoke-static {v6, v7}, Ljava/lang/Long;->valueOf(J)Ljava/lang/Long;

    move-result-object v6

    aput-object v6, v4, v5

    invoke-virtual {v2, v3, v4}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 224
    .end local v2    # "wakeupMethod":Ljava/lang/reflect/Method;
    :goto_0
    return-void

    .line 221
    :catch_0
    move-exception v0

    .line 222
    .local v0, "e":Ljava/lang/Exception;
    sget-object v3, Lcom/navdy/hud/app/device/PowerManager;->sLogger:Lcom/navdy/service/library/log/Logger;

    new-instance v4, Ljava/lang/StringBuilder;

    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    const-string v5, "error invoking PowerManager.wakeUp(): "

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    invoke-virtual {v4, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    move-result-object v4

    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v4

    invoke-virtual {v3, v4}, Lcom/navdy/service/library/log/Logger;->e(Ljava/lang/String;)V

    goto :goto_0
.end method

.method public static isAwake()Z
    .locals 2

    .prologue
    .line 166
    const-string/jumbo v0, "sys.power.mode"

    const-string v1, ""

    invoke-static {v0, v1}, Lcom/navdy/hud/app/util/os/SystemProperties;->get(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    const-string/jumbo v1, "quiet"

    invoke-virtual {v0, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_0

    const/4 v0, 0x1

    :goto_0
    return v0

    :cond_0
    const/4 v0, 0x0

    goto :goto_0
.end method

.method private isCoolingActive(Ljava/lang/String;)Z
    .locals 1
    .param p1, "coolingState"    # Ljava/lang/String;

    .prologue
    .line 113
    if-eqz p1, :cond_0

    const-string v0, "0"

    invoke-virtual {p1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_0

    const/4 v0, 0x1

    :goto_0
    return v0

    :cond_0
    const/4 v0, 0x0

    goto :goto_0
.end method

.method private setupShutdown()V
    .locals 11

    .prologue
    .line 309
    :try_start_0
    const-string v7, "android.os.ServiceManager"

    invoke-static {v7}, Ljava/lang/Class;->forName(Ljava/lang/String;)Ljava/lang/Class;

    move-result-object v6

    .line 310
    .local v6, "serviceManagerClass":Ljava/lang/Class;
    const-string v7, "getService"

    const/4 v8, 0x1

    new-array v8, v8, [Ljava/lang/Class;

    const/4 v9, 0x0

    const-class v10, Ljava/lang/String;

    aput-object v10, v8, v9

    invoke-virtual {v6, v7, v8}, Ljava/lang/Class;->getDeclaredMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    move-result-object v2

    .line 311
    .local v2, "getServiceMethod":Ljava/lang/reflect/Method;
    const/4 v7, 0x0

    const/4 v8, 0x1

    new-array v8, v8, [Ljava/lang/Object;

    const/4 v9, 0x0

    const-string/jumbo v10, "power"

    aput-object v10, v8, v9

    invoke-virtual {v2, v7, v8}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v5

    check-cast v5, Landroid/os/IBinder;

    .line 312
    .local v5, "powerBinder":Landroid/os/IBinder;
    const-string v7, "android.os.IPowerManager$Stub"

    invoke-static {v7}, Ljava/lang/Class;->forName(Ljava/lang/String;)Ljava/lang/Class;

    move-result-object v4

    .line 313
    .local v4, "iPowerManagerStubClass":Ljava/lang/Class;
    const-string v7, "asInterface"

    const/4 v8, 0x1

    new-array v8, v8, [Ljava/lang/Class;

    const/4 v9, 0x0

    const-class v10, Landroid/os/IBinder;

    aput-object v10, v8, v9

    invoke-virtual {v4, v7, v8}, Ljava/lang/Class;->getDeclaredMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    move-result-object v0

    .line 314
    .local v0, "asInterfaceMethod":Ljava/lang/reflect/Method;
    const/4 v7, 0x0

    const/4 v8, 0x1

    new-array v8, v8, [Ljava/lang/Object;

    const/4 v9, 0x0

    aput-object v5, v8, v9

    invoke-virtual {v0, v7, v8}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v7

    iput-object v7, p0, Lcom/navdy/hud/app/device/PowerManager;->mPowerManager:Ljava/lang/Object;
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 324
    :try_start_1
    const-string v7, "android.os.IPowerManager"

    invoke-static {v7}, Ljava/lang/Class;->forName(Ljava/lang/String;)Ljava/lang/Class;

    move-result-object v3

    .line 325
    .local v3, "iPowerManagerClass":Ljava/lang/Class;
    const-string/jumbo v7, "shutdown"

    const/4 v8, 0x2

    new-array v8, v8, [Ljava/lang/Class;

    const/4 v9, 0x0

    sget-object v10, Ljava/lang/Boolean;->TYPE:Ljava/lang/Class;

    aput-object v10, v8, v9

    const/4 v9, 0x1

    sget-object v10, Ljava/lang/Boolean;->TYPE:Ljava/lang/Class;

    aput-object v10, v8, v9

    invoke-virtual {v3, v7, v8}, Ljava/lang/Class;->getDeclaredMethod(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;

    move-result-object v7

    iput-object v7, p0, Lcom/navdy/hud/app/device/PowerManager;->mIPowerManagerShutdownMethod:Ljava/lang/reflect/Method;
    :try_end_1
    .catch Ljava/lang/Exception; {:try_start_1 .. :try_end_1} :catch_1

    .line 330
    .end local v0    # "asInterfaceMethod":Ljava/lang/reflect/Method;
    .end local v2    # "getServiceMethod":Ljava/lang/reflect/Method;
    .end local v3    # "iPowerManagerClass":Ljava/lang/Class;
    .end local v4    # "iPowerManagerStubClass":Ljava/lang/Class;
    .end local v5    # "powerBinder":Landroid/os/IBinder;
    .end local v6    # "serviceManagerClass":Ljava/lang/Class;
    :goto_0
    return-void

    .line 315
    :catch_0
    move-exception v1

    .line 316
    .local v1, "e":Ljava/lang/Exception;
    sget-object v7, Lcom/navdy/hud/app/device/PowerManager;->sLogger:Lcom/navdy/service/library/log/Logger;

    const-string v8, "exception invoking IPowerManager.Stub.asInterface()"

    invoke-virtual {v7, v8, v1}, Lcom/navdy/service/library/log/Logger;->e(Ljava/lang/String;Ljava/lang/Throwable;)V

    goto :goto_0

    .line 326
    .end local v1    # "e":Ljava/lang/Exception;
    .restart local v0    # "asInterfaceMethod":Ljava/lang/reflect/Method;
    .restart local v2    # "getServiceMethod":Ljava/lang/reflect/Method;
    .restart local v4    # "iPowerManagerStubClass":Ljava/lang/Class;
    .restart local v5    # "powerBinder":Landroid/os/IBinder;
    .restart local v6    # "serviceManagerClass":Ljava/lang/Class;
    :catch_1
    move-exception v1

    .line 327
    .restart local v1    # "e":Ljava/lang/Exception;
    sget-object v7, Lcom/navdy/hud/app/device/PowerManager;->sLogger:Lcom/navdy/service/library/log/Logger;

    const-string v8, "exception getting IPowerManager.shutdown() method"

    invoke-virtual {v7, v8, v1}, Lcom/navdy/service/library/log/Logger;->e(Ljava/lang/String;Ljava/lang/Throwable;)V

    goto :goto_0
.end method

.method private startOverheatMonitoring(Lcom/navdy/hud/app/device/PowerManager$RunState;)V
    .locals 2
    .param p1, "state"    # Lcom/navdy/hud/app/device/PowerManager$RunState;

    .prologue
    .line 153
    iput-object p1, p0, Lcom/navdy/hud/app/device/PowerManager;->runState:Lcom/navdy/hud/app/device/PowerManager$RunState;

    .line 154
    iget-object v0, p0, Lcom/navdy/hud/app/device/PowerManager;->handler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/device/PowerManager;->checkCoolingState:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 155
    iget-object v0, p0, Lcom/navdy/hud/app/device/PowerManager;->handler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/device/PowerManager;->checkCoolingState:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z

    .line 156
    return-void
.end method

.method private updateCoolingState()Z
    .locals 5

    .prologue
    .line 119
    :try_start_0
    const-string v2, "/sys/devices/virtual/thermal/cooling_device0/cur_state"

    invoke-static {v2}, Lcom/navdy/service/library/util/IOUtils;->convertFileToString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v2}, Ljava/lang/String;->trim()Ljava/lang/String;

    move-result-object v1

    .line 120
    .local v1, "newState":Ljava/lang/String;
    iget-object v2, p0, Lcom/navdy/hud/app/device/PowerManager;->oldCoolingState:Ljava/lang/String;

    invoke-virtual {v1, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v2

    if-nez v2, :cond_1

    .line 121
    sget-object v2, Lcom/navdy/hud/app/device/PowerManager;->sLogger:Lcom/navdy/service/library/log/Logger;

    new-instance v3, Ljava/lang/StringBuilder;

    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V

    const-string v4, "Cooling state changed from:"

    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    iget-object v4, p0, Lcom/navdy/hud/app/device/PowerManager;->oldCoolingState:Ljava/lang/String;

    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    const-string v4, " to:"

    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    invoke-virtual {v3, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v3

    invoke-virtual {v2, v3}, Lcom/navdy/service/library/log/Logger;->i(Ljava/lang/String;)V

    .line 125
    iget-object v2, p0, Lcom/navdy/hud/app/device/PowerManager;->oldCoolingState:Ljava/lang/String;

    invoke-direct {p0, v2}, Lcom/navdy/hud/app/device/PowerManager;->isCoolingActive(Ljava/lang/String;)Z

    move-result v2

    if-nez v2, :cond_0

    invoke-direct {p0, v1}, Lcom/navdy/hud/app/device/PowerManager;->isCoolingActive(Ljava/lang/String;)Z

    move-result v2

    if-eqz v2, :cond_0

    .line 126
    iget-object v2, p0, Lcom/navdy/hud/app/device/PowerManager;->runState:Lcom/navdy/hud/app/device/PowerManager$RunState;

    invoke-virtual {v2}, Lcom/navdy/hud/app/device/PowerManager$RunState;->name()Ljava/lang/String;

    move-result-object v2

    invoke-static {v2}, Lcom/navdy/hud/app/analytics/AnalyticsSupport;->recordCpuOverheat(Ljava/lang/String;)V

    .line 128
    :cond_0
    iput-object v1, p0, Lcom/navdy/hud/app/device/PowerManager;->oldCoolingState:Ljava/lang/String;

    .line 130
    :cond_1
    sget-object v2, Lcom/navdy/hud/app/device/PowerManager$RunState;->Running:Lcom/navdy/hud/app/device/PowerManager$RunState;

    iput-object v2, p0, Lcom/navdy/hud/app/device/PowerManager;->runState:Lcom/navdy/hud/app/device/PowerManager$RunState;
    :try_end_0
    .catch Ljava/io/IOException; {:try_start_0 .. :try_end_0} :catch_0

    .line 135
    const/4 v2, 0x1

    .end local v1    # "newState":Ljava/lang/String;
    :goto_0
    return v2

    .line 131
    :catch_0
    move-exception v0

    .line 132
    .local v0, "exception":Ljava/io/IOException;
    sget-object v2, Lcom/navdy/hud/app/device/PowerManager;->sLogger:Lcom/navdy/service/library/log/Logger;

    const-string v3, "Failed to read cooling device state - stopping monitoring"

    invoke-virtual {v2, v3, v0}, Lcom/navdy/service/library/log/Logger;->e(Ljava/lang/String;Ljava/lang/Throwable;)V

    .line 133
    const/4 v2, 0x0

    goto :goto_0
.end method


# virtual methods
.method public androidShutdown(Lcom/navdy/hud/app/event/Shutdown$Reason;Z)V
    .locals 8
    .param p1, "reason"    # Lcom/navdy/hud/app/event/Shutdown$Reason;
    .param p2, "forceFullShutdown"    # Z
    .annotation build Landroid/annotation/SuppressLint;
        value = {
            "ApplySharedPref"
        }
    .end annotation

    .prologue
    invoke-virtual {p1}, Ljava/lang/Enum;->name()Ljava/lang/String;
    move-result-object v0
    invoke-static {v0}, Lcom/navdy/hud/app/ambient/LowVoltagePolicy;->suppress(Ljava/lang/String;)Z
    move-result v0
    if-eqz v0, :power_reason_allowed
    return-void
    :power_reason_allowed
    const/4 v1, 0x1

    const/4 v2, 0x0

    .line 269
    sget-object v3, Lcom/navdy/hud/app/device/PowerManager;->sLogger:Lcom/navdy/service/library/log/Logger;

    new-instance v4, Ljava/lang/StringBuilder;

    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    const-string v5, "androidShutdown: "

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    invoke-virtual {v4, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/Object;)Ljava/lang/StringBuilder;

    move-result-object v4

    const-string v5, " forceFullShutdown:"

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    invoke-virtual {v4, p2}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v4

    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v4

    invoke-virtual {v3, v4}, Lcom/navdy/service/library/log/Logger;->d(Ljava/lang/String;)V

    .line 271
    invoke-static {}, Lcom/navdy/hud/app/device/dial/DialManager;->getInstance()Lcom/navdy/hud/app/device/dial/DialManager;

    move-result-object v3

    invoke-virtual {v3, v2}, Lcom/navdy/hud/app/device/dial/DialManager;->requestDialReboot(Z)V

    .line 274
    sget-object v3, Lcom/navdy/hud/app/event/Shutdown$Reason;->LOW_VOLTAGE:Lcom/navdy/hud/app/event/Shutdown$Reason;

    if-eq p1, v3, :cond_0

    sget-object v3, Lcom/navdy/hud/app/event/Shutdown$Reason;->CRITICAL_VOLTAGE:Lcom/navdy/hud/app/event/Shutdown$Reason;

    if-ne p1, v3, :cond_1

    .line 276
    :cond_0
    iget-object v3, p0, Lcom/navdy/hud/app/device/PowerManager;->preferences:Landroid/content/SharedPreferences;

    invoke-interface {v3}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object v3

    const-string v4, "last_low_voltage_event"

    .line 277
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v6

    invoke-interface {v3, v4, v6, v7}, Landroid/content/SharedPreferences$Editor;->putLong(Ljava/lang/String;J)Landroid/content/SharedPreferences$Editor;

    move-result-object v3

    .line 278
    invoke-interface {v3}, Landroid/content/SharedPreferences$Editor;->commit()Z

    .line 281
    :cond_1
    if-nez p2, :cond_2

    :goto_0
    invoke-static {p1, v1}, Lcom/navdy/hud/app/analytics/AnalyticsSupport;->recordShutdown(Lcom/navdy/hud/app/event/Shutdown$Reason;Z)V

    .line 283
    const-string v1, "0"

    const-string v2, "/sys/dlpc/led_enable"

    invoke-static {v1, v2}, Lcom/navdy/hud/app/device/light/LED;->writeToSysfs(Ljava/lang/String;Ljava/lang/String;)V

    .line 285
    iget-object v1, p0, Lcom/navdy/hud/app/device/PowerManager;->mPowerManager:Ljava/lang/Object;

    if-eqz v1, :cond_4

    iget-object v1, p0, Lcom/navdy/hud/app/device/PowerManager;->mIPowerManagerShutdownMethod:Ljava/lang/reflect/Method;

    if-eqz v1, :cond_4

    .line 288
    if-eqz p2, :cond_3

    .line 289
    :try_start_0
    iget-object v1, p0, Lcom/navdy/hud/app/device/PowerManager;->mIPowerManagerShutdownMethod:Ljava/lang/reflect/Method;

    iget-object v2, p0, Lcom/navdy/hud/app/device/PowerManager;->mPowerManager:Ljava/lang/Object;

    const/4 v3, 0x2

    new-array v3, v3, [Ljava/lang/Object;

    const/4 v4, 0x0

    const/4 v5, 0x0

    invoke-static {v5}, Ljava/lang/Boolean;->valueOf(Z)Ljava/lang/Boolean;

    move-result-object v5

    aput-object v5, v3, v4

    const/4 v4, 0x1

    const/4 v5, 0x0

    invoke-static {v5}, Ljava/lang/Boolean;->valueOf(Z)Ljava/lang/Boolean;

    move-result-object v5

    aput-object v5, v3, v4

    invoke-virtual {v1, v2, v3}, Ljava/lang/reflect/Method;->invoke(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;

    .line 299
    :goto_1
    return-void

    :cond_2
    move v1, v2

    .line 281
    goto :goto_0

    .line 291
    :cond_3
    iget-object v1, p0, Lcom/navdy/hud/app/device/PowerManager;->powerManager:Landroid/os/PowerManager;

    const-string/jumbo v2, "quiet"

    invoke-virtual {v1, v2}, Landroid/os/PowerManager;->reboot(Ljava/lang/String;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    goto :goto_1

    .line 293
    :catch_0
    move-exception v0

    .line 294
    .local v0, "e":Ljava/lang/Exception;
    sget-object v1, Lcom/navdy/hud/app/device/PowerManager;->sLogger:Lcom/navdy/service/library/log/Logger;

    const-string v2, "exception invoking IPowerManager.shutdown()"

    invoke-virtual {v1, v2, v0}, Lcom/navdy/service/library/log/Logger;->e(Ljava/lang/String;Ljava/lang/Throwable;)V

    goto :goto_1

    .line 297
    .end local v0    # "e":Ljava/lang/Exception;
    :cond_4
    sget-object v1, Lcom/navdy/hud/app/device/PowerManager;->sLogger:Lcom/navdy/service/library/log/Logger;

    const-string/jumbo v2, "shutdown was not properly initialized"

    invoke-virtual {v1, v2}, Lcom/navdy/service/library/log/Logger;->e(Ljava/lang/String;)V

    goto :goto_1
.end method

.method public enterSleepMode()V
    .locals 4

    .prologue
    .line 193
    iget-object v0, p0, Lcom/navdy/hud/app/device/PowerManager;->handler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/device/PowerManager;->quietModeTimeout:Ljava/lang/Runnable;

    sget-wide v2, Lcom/navdy/hud/app/device/PowerManager;->INSTANT_ON_TIMEOUT:J

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 194
    invoke-static {}, Lcom/navdy/hud/app/device/light/LightManager;->getInstance()Lcom/navdy/hud/app/device/light/LightManager;

    move-result-object v0

    invoke-static {v0}, Lcom/navdy/hud/app/device/light/HUDLightUtils;->turnOffFrontLED(Lcom/navdy/hud/app/device/light/LightManager;)V

    .line 195
    invoke-direct {p0}, Lcom/navdy/hud/app/device/PowerManager;->androidSleep()V

    .line 196
    return-void
.end method

.method public inQuietMode()Z
    .locals 1

    .prologue
    .line 159
    iget-boolean v0, p0, Lcom/navdy/hud/app/device/PowerManager;->awake:Z

    if-nez v0, :cond_0

    const/4 v0, 0x1

    :goto_0
    return v0

    :cond_0
    const/4 v0, 0x0

    goto :goto_0
.end method

.method public onKey(Landroid/view/KeyEvent;)V
    .locals 1
    .param p1, "event"    # Landroid/view/KeyEvent;
    .annotation runtime Lcom/squareup/otto/Subscribe;
    .end annotation

    .prologue
    .line 201
    sget-object v0, Lcom/navdy/hud/app/analytics/AnalyticsSupport$WakeupReason;->DIAL:Lcom/navdy/hud/app/analytics/AnalyticsSupport$WakeupReason;

    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/device/PowerManager;->wakeUp(Lcom/navdy/hud/app/analytics/AnalyticsSupport$WakeupReason;)V

    .line 202
    return-void
.end method

.method public quietModeEnabled()Z
    .locals 12

    .prologue
    const/4 v6, 0x0

    const/4 v5, 0x1

    .line 244
    invoke-static {}, Ljava/lang/System;->currentTimeMillis()J

    move-result-wide v2

    .line 245
    .local v2, "now":J
    iget-wide v8, p0, Lcom/navdy/hud/app/device/PowerManager;->lastLowVoltage:J

    sub-long v0, v2, v8

    .line 247
    .local v0, "delta":J
    iget-wide v8, p0, Lcom/navdy/hud/app/device/PowerManager;->lastLowVoltage:J

    const-wide/16 v10, -0x1

    cmp-long v7, v8, v10

    if-eqz v7, :cond_1

    sget-wide v8, Lcom/navdy/hud/app/device/PowerManager;->RECHARGE_TIME:J

    cmp-long v7, v0, v8

    if-gez v7, :cond_1

    move v4, v5

    .line 248
    .local v4, "recharging":Z
    :goto_0
    if-eqz v4, :cond_0

    .line 249
    sget-object v7, Lcom/navdy/hud/app/device/PowerManager;->sLogger:Lcom/navdy/service/library/log/Logger;

    new-instance v8, Ljava/lang/StringBuilder;

    invoke-direct {v8}, Ljava/lang/StringBuilder;-><init>()V

    const-string v9, "disabling quiet mode since we had a low voltage event "

    invoke-virtual {v8, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v8

    sget-object v9, Ljava/util/concurrent/TimeUnit;->MILLISECONDS:Ljava/util/concurrent/TimeUnit;

    .line 250
    invoke-virtual {v9, v0, v1}, Ljava/util/concurrent/TimeUnit;->toHours(J)J

    move-result-wide v10

    invoke-virtual {v8, v10, v11}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    move-result-object v8

    const-string v9, " hours ago"

    invoke-virtual {v8, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v8

    invoke-virtual {v8}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v8

    .line 249
    invoke-virtual {v7, v8}, Lcom/navdy/service/library/log/Logger;->d(Ljava/lang/String;)V

    .line 252
    :cond_0
    const-string/jumbo v7, "persist.sys.instanton"

    invoke-static {v7, v5}, Lcom/navdy/hud/app/util/os/SystemProperties;->getBoolean(Ljava/lang/String;Z)Z

    move-result v7

    if-eqz v7, :cond_2

    if-nez v4, :cond_2

    :goto_1
    return v5

    .end local v4    # "recharging":Z
    :cond_1
    move v4, v6

    .line 247
    goto :goto_0

    .restart local v4    # "recharging":Z
    :cond_2
    move v5, v6

    .line 252
    goto :goto_1
.end method

.method public wakeUp(Lcom/navdy/hud/app/analytics/AnalyticsSupport$WakeupReason;)V
    .locals 2
    .param p1, "reason"    # Lcom/navdy/hud/app/analytics/AnalyticsSupport$WakeupReason;

    .prologue
    .line 170
    iget-boolean v0, p0, Lcom/navdy/hud/app/device/PowerManager;->awake:Z

    if-nez v0, :cond_0

    .line 171
    sget-object v0, Lcom/navdy/hud/app/device/PowerManager;->sLogger:Lcom/navdy/service/library/log/Logger;

    const-string/jumbo v1, "waking up"

    invoke-virtual {v0, v1}, Lcom/navdy/service/library/log/Logger;->d(Ljava/lang/String;)V

    .line 172
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/device/PowerManager;->awake:Z

    .line 174
    const-string/jumbo v0, "sys.power.mode"

    const-string v1, "normal"

    invoke-static {v0, v1}, Lcom/navdy/hud/app/util/os/SystemProperties;->set(Ljava/lang/String;Ljava/lang/String;)V

    .line 175
    iget-object v0, p0, Lcom/navdy/hud/app/device/PowerManager;->handler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/device/PowerManager;->quietModeTimeout:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 177
    invoke-static {}, Lcom/navdy/hud/app/device/light/LightManager;->getInstance()Lcom/navdy/hud/app/device/light/LightManager;

    move-result-object v0

    invoke-static {v0}, Lcom/navdy/hud/app/device/light/HUDLightUtils;->resetFrontLED(Lcom/navdy/hud/app/device/light/LightManager;)V

    .line 180
    const-string v0, "1"

    const-string v1, "/sys/dlpc/led_enable"

    invoke-static {v0, v1}, Lcom/navdy/hud/app/device/light/LED;->writeToSysfs(Ljava/lang/String;Ljava/lang/String;)V

    .line 182
    invoke-direct {p0}, Lcom/navdy/hud/app/device/PowerManager;->androidWakeup()V

    .line 184
    sget-object v0, Lcom/navdy/hud/app/device/PowerManager$RunState;->Waking:Lcom/navdy/hud/app/device/PowerManager$RunState;

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/device/PowerManager;->startOverheatMonitoring(Lcom/navdy/hud/app/device/PowerManager$RunState;)V

    .line 188
    iget-object v0, p0, Lcom/navdy/hud/app/device/PowerManager;->bus:Lcom/squareup/otto/Bus;

    new-instance v1, Lcom/navdy/hud/app/event/Wakeup;

    invoke-direct {v1, p1}, Lcom/navdy/hud/app/event/Wakeup;-><init>(Lcom/navdy/hud/app/analytics/AnalyticsSupport$WakeupReason;)V

    invoke-virtual {v0, v1}, Lcom/squareup/otto/Bus;->post(Ljava/lang/Object;)V

    .line 190
    :cond_0
    return-void
.end method
