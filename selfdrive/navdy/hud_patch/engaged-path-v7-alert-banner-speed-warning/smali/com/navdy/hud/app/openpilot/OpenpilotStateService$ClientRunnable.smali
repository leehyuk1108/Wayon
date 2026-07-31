.class final Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable;
.super Ljava/lang/Object;
.source "OpenpilotStateService.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Lcom/navdy/hud/app/openpilot/OpenpilotStateService;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x1a
    name = "ClientRunnable"
.end annotation


# instance fields
.field private final mContext:Landroid/content/Context;

.field private final mMainHandler:Landroid/os/Handler;

.field private final mSocket:Ljava/net/Socket;


# direct methods
.method constructor <init>(Landroid/content/Context;Landroid/os/Handler;Ljava/net/Socket;)V
    .locals 0

    .line 92
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 93
    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable;->mContext:Landroid/content/Context;

    .line 94
    iput-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable;->mMainHandler:Landroid/os/Handler;

    .line 95
    iput-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable;->mSocket:Ljava/net/Socket;

    .line 96
    return-void
.end method

.method static synthetic access$000(Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable;)Landroid/content/Context;
    .locals 0

    .line 87
    iget-object p0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable;->mContext:Landroid/content/Context;

    return-object p0
.end method

.method private dispatchPayload(Ljava/lang/String;)V
    .locals 5

    .line 122
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable;->mMainHandler:Landroid/os/Handler;

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable;->mContext:Landroid/content/Context;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacksAndMessages(Ljava/lang/Object;)V

    new-instance v1, Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable$1;

    invoke-direct {v1, p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable$1;-><init>(Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable;Ljava/lang/String;)V

    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable;->mContext:Landroid/content/Context;

    invoke-static {}, Landroid/os/SystemClock;->uptimeMillis()J

    move-result-wide v3

    invoke-virtual {v0, v1, v2, v3, v4}, Landroid/os/Handler;->postAtTime(Ljava/lang/Runnable;Ljava/lang/Object;J)Z

    .line 128
    return-void
.end method


# virtual methods
.method public run()V
    .locals 7

    .line 101
    const-string v0, "NavdyOpenpilotService"

    :try_start_0
    new-instance v1, Ljava/io/BufferedReader;

    new-instance v2, Ljava/io/InputStreamReader;

    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable;->mSocket:Ljava/net/Socket;

    .line 102
    invoke-virtual {v3}, Ljava/net/Socket;->getInputStream()Ljava/io/InputStream;

    move-result-object v3

    const-string v4, "UTF-8"

    invoke-direct {v2, v3, v4}, Ljava/io/InputStreamReader;-><init>(Ljava/io/InputStream;Ljava/lang/String;)V

    invoke-direct {v1, v2}, Ljava/io/BufferedReader;-><init>(Ljava/io/Reader;)V

    new-instance v5, Ljava/io/BufferedWriter;

    new-instance v2, Ljava/io/OutputStreamWriter;

    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable;->mSocket:Ljava/net/Socket;

    invoke-virtual {v3}, Ljava/net/Socket;->getOutputStream()Ljava/io/OutputStream;

    move-result-object v3

    const-string v4, "UTF-8"

    invoke-direct {v2, v3, v4}, Ljava/io/OutputStreamWriter;-><init>(Ljava/io/OutputStream;Ljava/lang/String;)V

    invoke-direct {v5, v2}, Ljava/io/BufferedWriter;-><init>(Ljava/io/Writer;)V

    .line 104
    :goto_0
    invoke-virtual {v1}, Ljava/io/BufferedReader;->readLine()Ljava/lang/String;

    move-result-object v2

    if-eqz v2, :cond_1

    .line 105
    invoke-virtual {v2}, Ljava/lang/String;->length()I

    move-result v3

    if-nez v3, :cond_0

    .line 106
    goto :goto_0

    .line 109
    :cond_0
    invoke-direct {p0, v2}, Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable;->dispatchPayload(Ljava/lang/String;)V

    new-instance v3, Ljava/lang/StringBuilder;

    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V

    const-string v4, "{\"cameraSpeedKph\":"

    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-static {}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->getLastCameraSpeedLimit()I

    move-result v4

    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    const-string v4, "}\n"

    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v3

    invoke-virtual {v5, v3}, Ljava/io/BufferedWriter;->write(Ljava/lang/String;)V

    invoke-virtual {v5}, Ljava/io/BufferedWriter;->flush()V
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    goto :goto_0

    .line 115
    :cond_1
    :try_start_1
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable;->mSocket:Ljava/net/Socket;
    :try_end_1
    .catchall {:try_start_1 .. :try_end_1} :catchall_1

    goto :goto_1

    .line 111
    :catchall_0
    move-exception v1

    .line 112
    :try_start_2
    const-string v2, "socket client failed"

    invoke-static {v0, v2, v1}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I
    :try_end_2
    .catchall {:try_start_2 .. :try_end_2} :catchall_2

    .line 115
    :try_start_3
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable;->mSocket:Ljava/net/Socket;

    :goto_1
    invoke-virtual {v0}, Ljava/net/Socket;->close()V
    :try_end_3
    .catchall {:try_start_3 .. :try_end_3} :catchall_1

    .line 117
    goto :goto_2

    .line 116
    :catchall_1
    move-exception v0

    .line 118
    nop

    .line 119
    :goto_2
    return-void

    .line 114
    :catchall_2
    move-exception v0

    .line 115
    :try_start_4
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateService$ClientRunnable;->mSocket:Ljava/net/Socket;

    invoke-virtual {v1}, Ljava/net/Socket;->close()V
    :try_end_4
    .catchall {:try_start_4 .. :try_end_4} :catchall_3

    .line 117
    goto :goto_3

    .line 116
    :catchall_3
    move-exception v1

    .line 118
    :goto_3
    throw v0
.end method
