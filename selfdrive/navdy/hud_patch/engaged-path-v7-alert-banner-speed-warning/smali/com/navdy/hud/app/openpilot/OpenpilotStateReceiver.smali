.class public final Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;
.super Landroid/content/BroadcastReceiver;
.source "OpenpilotStateReceiver.java"


# static fields
.field public static final ACTION_AMBIENT_TEST_DRIVE:Ljava/lang/String; = "com.navdy.AMBIENT_TEST_DRIVE"

.field public static final ACTION_AMBIENT_TEST_OVERSPEED_OFF:Ljava/lang/String; = "com.navdy.AMBIENT_TEST_OVERSPEED_OFF"

.field public static final ACTION_AMBIENT_TEST_OVERSPEED_ON:Ljava/lang/String; = "com.navdy.AMBIENT_TEST_OVERSPEED_ON"

.field public static final ACTION_AMBIENT_TEST_REVERSE:Ljava/lang/String; = "com.navdy.AMBIENT_TEST_REVERSE"

.field public static final ACTION_OPENPILOT_STATE:Ljava/lang/String; = "com.navdy.OPENPILOT_STATE"

.field private static final BSM_H:I = 0x2d

.field private static final BSM_LEFT_X:I = 0xa7

.field private static final BSM_RIGHT_X:I = 0x1b7

.field private static final BSM_W:I = 0x22

.field private static final BSM_Y:I = 0x108

.field private static final COLOR_BSM_ORANGE:I = -0x7600

.field private static final COLOR_OP_GREEN:I = -0xff19ba

.field private static final OP_READY_H:I = 0x16

.field private static final OP_READY_W:I = 0x28

.field private static final OP_READY_X:I = 0x17c

.field private static final OP_READY_Y:I = 0x113

.field private static final SET_ICON_GAP:I = 0x5

.field private static final SET_ICON_H:I = 0x1d

.field private static final SET_ICON_W:I = 0x1e

.field private static final SET_ROW_H:I = 0x1e

.field private static final SET_ROW_Y:I = 0x128

.field private static final STANDSTILL_H:I = 0x18

.field private static final STANDSTILL_W:I = 0x22

.field private static final STANDSTILL_X:I = 0xe2

.field private static final STANDSTILL_Y:I = 0x112

.field private static final TAG:Ljava/lang/String; = "NavdyOpenpilot"

.field private static final TURN_BLINK_INTERVAL_MS:J = 0x1c2L

.field private static final TURN_H:I = 0x14

.field private static final TURN_LEFT_X:I = 0x80

.field private static final TURN_RIGHT_X:I = 0x1e8

.field private static final TURN_W:I = 0x18

.field private static final TURN_Y:I = 0xf2

.field private static sCurrentSpeedTextView:Landroid/widget/TextView;

.field private static sEngagedBodyMask:Landroid/view/View;

.field private static sEngagedTopMask:Landroid/view/View;

.field private static sHaveActive:Z

.field private static sHaveBlindspot:Z

.field private static sHaveBlinker:Z

.field private static sLastActive:Z

.field private static sLastGear:Ljava/lang/String;

.field private static sLastLeftBlindspot:Z

.field private static sLastLeftBlinker:Z

.field private static sLastRightBlindspot:Z

.field private static sLastRightBlinker:Z

.field private static sLeftBlinkerRequested:Z

.field private static sLeftBsmView:Landroid/widget/ImageView;

.field private static sLeftTurnView:Landroid/widget/ImageView;

.field private static sMusicTextView:Landroid/widget/TextView;

.field private static sMusicTitle:Ljava/lang/String;

.field private static sOpReadyView:Landroid/widget/ImageView;

.field private static sOutsideTempTextView:Landroid/widget/TextView;

.field private static sOverlayView:Landroid/widget/FrameLayout;

.field private static sAlertBannerView:Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;

.field private static sPathView:Lcom/navdy/hud/app/openpilot/OpenpilotPathView;

.field private static sRightBlinkerRequested:Z

.field private static sRightBsmView:Landroid/widget/ImageView;

.field private static sRightTurnView:Landroid/widget/ImageView;

.field private static sSetSpeedIconView:Landroid/widget/ImageView;

.field private static sSetSpeedRow:Landroid/widget/LinearLayout;

.field private static sSetSpeedTextView:Landroid/widget/TextView;

.field private static sStandstillView:Landroid/widget/ImageView;

.field private static sTurnBlinkOn:Z

.field private static final sTurnBlinkRunnable:Ljava/lang/Runnable;

.field private static sTurnBlinkScheduled:Z

.field private static final sUiHandler:Landroid/os/Handler;

.field private static sWindowManager:Landroid/view/WindowManager;


# direct methods
.method static constructor <clinit>()V
    .locals 2

    .line 76
    const-string v0, ""

    sput-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLastGear:Ljava/lang/String;

    sput-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sMusicTitle:Ljava/lang/String;

    .line 89
    new-instance v0, Landroid/os/Handler;

    invoke-static {}, Landroid/os/Looper;->getMainLooper()Landroid/os/Looper;

    move-result-object v1

    invoke-direct {v0, v1}, Landroid/os/Handler;-><init>(Landroid/os/Looper;)V

    sput-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sUiHandler:Landroid/os/Handler;

    .line 94
    new-instance v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver$1;

    invoke-direct {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver$1;-><init>()V

    sput-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sTurnBlinkRunnable:Ljava/lang/Runnable;

    return-void
.end method

.method public constructor <init>()V
    .locals 0

    .line 28
    invoke-direct {p0}, Landroid/content/BroadcastReceiver;-><init>()V

    return-void
.end method

.method static synthetic access$002(Z)Z
    .locals 0

    .line 28
    sput-boolean p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sTurnBlinkScheduled:Z

    return p0
.end method

.method static synthetic access$100()Z
    .locals 1

    .line 28
    sget-boolean v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLeftBlinkerRequested:Z

    return v0
.end method

.method static synthetic access$200()Z
    .locals 1

    .line 28
    sget-boolean v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sRightBlinkerRequested:Z

    return v0
.end method

.method static synthetic access$300()Z
    .locals 1

    .line 28
    sget-boolean v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sTurnBlinkOn:Z

    return v0
.end method

.method static synthetic access$302(Z)Z
    .locals 0

    .line 28
    sput-boolean p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sTurnBlinkOn:Z

    return p0
.end method

.method static synthetic access$400()V
    .locals 0

    .line 28
    invoke-static {}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->applyTurnBlinkVisibility()V

    return-void
.end method

.method static synthetic access$500()V
    .locals 0

    .line 28
    invoke-static {}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->scheduleTurnBlink()V

    return-void
.end method

.method private static addImage(Landroid/content/Context;Landroid/widget/FrameLayout;Ljava/lang/String;IIII)Landroid/widget/ImageView;
    .locals 2

    .line 354
    new-instance v0, Landroid/widget/ImageView;

    invoke-direct {v0, p0}, Landroid/widget/ImageView;-><init>(Landroid/content/Context;)V

    .line 355
    sget-object v1, Landroid/widget/ImageView$ScaleType;->FIT_CENTER:Landroid/widget/ImageView$ScaleType;

    invoke-virtual {v0, v1}, Landroid/widget/ImageView;->setScaleType(Landroid/widget/ImageView$ScaleType;)V

    .line 356
    invoke-static {p0, v0, p2}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->setImageByName(Landroid/content/Context;Landroid/widget/ImageView;Ljava/lang/String;)V

    .line 358
    new-instance p0, Landroid/widget/FrameLayout$LayoutParams;

    invoke-direct {p0, p5, p6}, Landroid/widget/FrameLayout$LayoutParams;-><init>(II)V

    .line 359
    iput p3, p0, Landroid/widget/FrameLayout$LayoutParams;->leftMargin:I

    .line 360
    iput p4, p0, Landroid/widget/FrameLayout$LayoutParams;->topMargin:I

    .line 361
    invoke-virtual {p1, v0, p0}, Landroid/widget/FrameLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 362
    return-object v0
.end method

.method private static applyTurnBlinkVisibility()V
    .locals 4

    .line 266
    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLeftTurnView:Landroid/widget/ImageView;

    const/4 v1, 0x0

    const/16 v2, 0x8

    if-eqz v0, :cond_1

    .line 267
    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLeftTurnView:Landroid/widget/ImageView;

    sget-boolean v3, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLeftBlinkerRequested:Z

    if-eqz v3, :cond_0

    sget-boolean v3, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sTurnBlinkOn:Z

    if-eqz v3, :cond_0

    const/4 v3, 0x0

    goto :goto_0

    :cond_0
    const/16 v3, 0x8

    :goto_0
    invoke-virtual {v0, v3}, Landroid/widget/ImageView;->setVisibility(I)V

    .line 269
    :cond_1
    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sRightTurnView:Landroid/widget/ImageView;

    if-eqz v0, :cond_3

    .line 270
    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sRightTurnView:Landroid/widget/ImageView;

    sget-boolean v3, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sRightBlinkerRequested:Z

    if-eqz v3, :cond_2

    sget-boolean v3, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sTurnBlinkOn:Z

    if-eqz v3, :cond_2

    goto :goto_1

    :cond_2
    const/16 v1, 0x8

    :goto_1
    invoke-virtual {v0, v1}, Landroid/widget/ImageView;->setVisibility(I)V

    .line 272
    :cond_3
    return-void
.end method

.method private static blinkerLabel(ZZ)Ljava/lang/String;
    .locals 0

    .line 416
    if-eqz p0, :cond_0

    if-eqz p1, :cond_0

    .line 417
    const-string p0, "HAZARD"

    return-object p0

    .line 419
    :cond_0
    if-eqz p0, :cond_1

    .line 420
    const-string p0, "TURN LEFT"

    return-object p0

    .line 422
    :cond_1
    if-eqz p1, :cond_2

    .line 423
    const-string p0, "TURN RIGHT"

    return-object p0

    .line 425
    :cond_2
    const-string p0, "TURN OFF"

    return-object p0
.end method

.method private static buildOverlayLayoutParams()Landroid/view/WindowManager$LayoutParams;
    .locals 6

    .line 393
    new-instance v0, Landroid/view/WindowManager$LayoutParams;

    const/16 v4, 0x118

    const/4 v5, -0x3

    const/4 v1, -0x1

    const/4 v2, -0x1

    const/16 v3, 0x7d3

    invoke-direct/range {v0 .. v5}, Landroid/view/WindowManager$LayoutParams;-><init>(IIIII)V

    .line 401
    const/16 v1, 0x33

    iput v1, v0, Landroid/view/WindowManager$LayoutParams;->gravity:I

    .line 402
    const/4 v1, 0x0

    iput v1, v0, Landroid/view/WindowManager$LayoutParams;->x:I

    .line 403
    iput v1, v0, Landroid/view/WindowManager$LayoutParams;->y:I

    .line 404
    const-string v1, "NavdyOpenpilotStatus"

    invoke-virtual {v0, v1}, Landroid/view/WindowManager$LayoutParams;->setTitle(Ljava/lang/CharSequence;)V

    .line 405
    return-object v0
.end method

.method private static buildOverlayView(Landroid/content/Context;)Landroid/widget/FrameLayout;
    .locals 7

    .line 295
    new-instance v1, Landroid/widget/FrameLayout;

    invoke-direct {v1, p0}, Landroid/widget/FrameLayout;-><init>(Landroid/content/Context;)V

    .line 296
    const/4 v0, 0x0

    invoke-virtual {v1, v0}, Landroid/widget/FrameLayout;->setClipChildren(Z)V

    .line 297
    invoke-virtual {v1, v0}, Landroid/widget/FrameLayout;->setClipToPadding(Z)V

    new-instance v2, Landroid/view/View;

    invoke-direct {v2, p0}, Landroid/view/View;-><init>(Landroid/content/Context;)V

    sput-object v2, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sEngagedTopMask:Landroid/view/View;

    const/high16 v3, -0x1000000

    invoke-virtual {v2, v3}, Landroid/view/View;->setBackgroundColor(I)V

    new-instance v3, Landroid/widget/FrameLayout$LayoutParams;

    const/16 v4, 0x280

    const/16 v5, 0x64

    invoke-direct {v3, v4, v5}, Landroid/widget/FrameLayout$LayoutParams;-><init>(II)V

    const/16 v4, 0x78

    iput v4, v3, Landroid/widget/FrameLayout$LayoutParams;->topMargin:I

    invoke-virtual {v1, v2, v3}, Landroid/widget/FrameLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    const/16 v3, 0x8

    invoke-virtual {v2, v3}, Landroid/view/View;->setVisibility(I)V

    new-instance v2, Landroid/view/View;

    invoke-direct {v2, p0}, Landroid/view/View;-><init>(Landroid/content/Context;)V

    sput-object v2, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sEngagedBodyMask:Landroid/view/View;

    const/high16 v3, -0x1000000

    invoke-virtual {v2, v3}, Landroid/view/View;->setBackgroundColor(I)V

    new-instance v3, Landroid/widget/FrameLayout$LayoutParams;

    const/16 v4, 0x17c

    const/16 v5, 0x6c

    invoke-direct {v3, v4, v5}, Landroid/widget/FrameLayout$LayoutParams;-><init>(II)V

    const/16 v4, 0x70

    iput v4, v3, Landroid/widget/FrameLayout$LayoutParams;->leftMargin:I

    const/16 v4, 0xdc

    iput v4, v3, Landroid/widget/FrameLayout$LayoutParams;->topMargin:I

    invoke-virtual {v1, v2, v3}, Landroid/widget/FrameLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    const/16 v3, 0x8

    invoke-virtual {v2, v3}, Landroid/view/View;->setVisibility(I)V

    new-instance v2, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;

    invoke-direct {v2, p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;-><init>(Landroid/content/Context;)V

    sput-object v2, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sPathView:Lcom/navdy/hud/app/openpilot/OpenpilotPathView;

    new-instance v3, Landroid/widget/FrameLayout$LayoutParams;

    const/16 v4, 0x140

    const/16 v5, 0x64

    invoke-direct {v3, v4, v5}, Landroid/widget/FrameLayout$LayoutParams;-><init>(II)V

    const/16 v4, 0xa0

    iput v4, v3, Landroid/widget/FrameLayout$LayoutParams;->leftMargin:I

    const/16 v4, 0x78

    iput v4, v3, Landroid/widget/FrameLayout$LayoutParams;->topMargin:I

    invoke-virtual {v1, v2, v3}, Landroid/widget/FrameLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    new-instance v2, Landroid/widget/TextView;

    invoke-direct {v2, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    sput-object v2, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sCurrentSpeedTextView:Landroid/widget/TextView;

    const/4 v3, -0x1

    invoke-virtual {v2, v3}, Landroid/widget/TextView;->setTextColor(I)V

    const/4 v3, 0x0

    const/high16 v4, 0x42780000    # 62.0f

    invoke-virtual {v2, v3, v4}, Landroid/widget/TextView;->setTextSize(IF)V

    const/16 v4, 0x11

    invoke-virtual {v2, v4}, Landroid/widget/TextView;->setGravity(I)V

    invoke-virtual {v2, v3}, Landroid/widget/TextView;->setIncludeFontPadding(Z)V

    const/4 v4, 0x1

    invoke-virtual {v2, v4}, Landroid/widget/TextView;->setSingleLine(Z)V

    new-instance v4, Landroid/widget/FrameLayout$LayoutParams;

    const/16 v5, 0xaa

    const/16 v6, 0x52

    invoke-direct {v4, v5, v6}, Landroid/widget/FrameLayout$LayoutParams;-><init>(II)V

    const/16 v5, 0xeb

    iput v5, v4, Landroid/widget/FrameLayout$LayoutParams;->leftMargin:I

    const/16 v5, 0xdd

    iput v5, v4, Landroid/widget/FrameLayout$LayoutParams;->topMargin:I

    invoke-virtual {v1, v2, v4}, Landroid/widget/FrameLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    const/16 v4, 0x8

    invoke-virtual {v2, v4}, Landroid/widget/TextView;->setVisibility(I)V

    new-instance v2, Landroid/widget/TextView;

    invoke-direct {v2, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    sput-object v2, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sMusicTextView:Landroid/widget/TextView;

    const/4 v3, -0x1

    invoke-virtual {v2, v3}, Landroid/widget/TextView;->setTextColor(I)V

    const/4 v3, 0x0

    const/high16 v4, 0x41880000    # 17.0f

    invoke-virtual {v2, v3, v4}, Landroid/widget/TextView;->setTextSize(IF)V

    const/16 v4, 0x11

    invoke-virtual {v2, v4}, Landroid/widget/TextView;->setGravity(I)V

    invoke-virtual {v2, v3}, Landroid/widget/TextView;->setIncludeFontPadding(Z)V

    const/4 v4, 0x1

    invoke-virtual {v2, v4}, Landroid/widget/TextView;->setSingleLine(Z)V

    sget-object v4, Landroid/text/TextUtils$TruncateAt;->END:Landroid/text/TextUtils$TruncateAt;

    invoke-virtual {v2, v4}, Landroid/widget/TextView;->setEllipsize(Landroid/text/TextUtils$TruncateAt;)V

    new-instance v4, Landroid/widget/FrameLayout$LayoutParams;

    const/16 v5, 0x1ae

    const/16 v6, 0x1c

    invoke-direct {v4, v5, v6}, Landroid/widget/FrameLayout$LayoutParams;-><init>(II)V

    const/16 v5, 0x69

    iput v5, v4, Landroid/widget/FrameLayout$LayoutParams;->leftMargin:I

    const/16 v5, 0x148

    iput v5, v4, Landroid/widget/FrameLayout$LayoutParams;->topMargin:I

    invoke-virtual {v1, v2, v4}, Landroid/widget/FrameLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    const/16 v4, 0x8

    invoke-virtual {v2, v4}, Landroid/widget/TextView;->setVisibility(I)V

    .line 299
    const/16 v5, 0x18

    const/16 v6, 0x14

    const-string v2, "navdy_op_turn_left"

    const/16 v3, 0x80

    const/16 v4, 0xf2

    move-object v0, p0

    invoke-static/range {v0 .. v6}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->addImage(Landroid/content/Context;Landroid/widget/FrameLayout;Ljava/lang/String;IIII)Landroid/widget/ImageView;

    move-result-object p0

    sput-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLeftTurnView:Landroid/widget/ImageView;

    .line 300
    const-string v2, "navdy_op_turn_right"

    const/16 v3, 0x1e8

    invoke-static/range {v0 .. v6}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->addImage(Landroid/content/Context;Landroid/widget/FrameLayout;Ljava/lang/String;IIII)Landroid/widget/ImageView;

    move-result-object p0

    sput-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sRightTurnView:Landroid/widget/ImageView;

    .line 301
    const/16 v5, 0x22

    const/16 v6, 0x2d

    const-string v2, "navdy_op_bsm_left"

    const/16 v3, 0xa7

    const/16 v4, 0x108

    invoke-static/range {v0 .. v6}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->addImage(Landroid/content/Context;Landroid/widget/FrameLayout;Ljava/lang/String;IIII)Landroid/widget/ImageView;

    move-result-object p0

    sput-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLeftBsmView:Landroid/widget/ImageView;

    .line 302
    const-string v2, "navdy_op_bsm_right"

    const/16 v3, 0x1b7

    invoke-static/range {v0 .. v6}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->addImage(Landroid/content/Context;Landroid/widget/FrameLayout;Ljava/lang/String;IIII)Landroid/widget/ImageView;

    move-result-object p0

    sput-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sRightBsmView:Landroid/widget/ImageView;

    .line 303
    const/16 v6, 0x18

    const-string v2, "navdy_op_standstill"

    const/16 v3, 0xe2

    const/16 v4, 0x112

    invoke-static/range {v0 .. v6}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->addImage(Landroid/content/Context;Landroid/widget/FrameLayout;Ljava/lang/String;IIII)Landroid/widget/ImageView;

    move-result-object p0

    sput-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sStandstillView:Landroid/widget/ImageView;

    .line 305
    const/16 v5, 0x28

    const/16 v6, 0x16

    const-string v2, "navdy_op_steering"

    const/16 v3, 0x17c

    const/16 v4, 0x113

    invoke-static/range {v0 .. v6}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->addImage(Landroid/content/Context;Landroid/widget/FrameLayout;Ljava/lang/String;IIII)Landroid/widget/ImageView;

    move-result-object p0

    sput-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sOpReadyView:Landroid/widget/ImageView;

    .line 307
    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->buildSetSpeedRow(Landroid/content/Context;)Landroid/widget/LinearLayout;

    move-result-object p0

    sput-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedRow:Landroid/widget/LinearLayout;

    const/4 p0, 0x0

    sput-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sOutsideTempTextView:Landroid/widget/TextView;

    .line 309
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLeftBsmView:Landroid/widget/ImageView;

    const/16 v0, -0x7600

    invoke-static {p0, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->tintImage(Landroid/widget/ImageView;I)V

    .line 310
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sRightBsmView:Landroid/widget/ImageView;

    invoke-static {p0, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->tintImage(Landroid/widget/ImageView;I)V

    .line 311
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sStandstillView:Landroid/widget/ImageView;

    const v0, -0xff19ba

    invoke-static {p0, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->tintImage(Landroid/widget/ImageView;I)V

    .line 313
    new-instance p0, Landroid/widget/FrameLayout$LayoutParams;

    const/4 v0, -0x2

    const/16 v2, 0x1e

    invoke-direct {p0, v0, v2}, Landroid/widget/FrameLayout$LayoutParams;-><init>(II)V

    .line 315
    const/16 v0, 0x31

    iput v0, p0, Landroid/widget/FrameLayout$LayoutParams;->gravity:I

    .line 316
    const/16 v0, 0x128

    iput v0, p0, Landroid/widget/FrameLayout$LayoutParams;->topMargin:I

    .line 317
    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedRow:Landroid/widget/LinearLayout;

    invoke-virtual {v1, v0, p0}, Landroid/widget/FrameLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 319
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLeftTurnView:Landroid/widget/ImageView;

    const/16 v0, 0x8

    invoke-virtual {p0, v0}, Landroid/widget/ImageView;->setVisibility(I)V

    .line 320
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sRightTurnView:Landroid/widget/ImageView;

    invoke-virtual {p0, v0}, Landroid/widget/ImageView;->setVisibility(I)V

    .line 321
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLeftBsmView:Landroid/widget/ImageView;

    invoke-virtual {p0, v0}, Landroid/widget/ImageView;->setVisibility(I)V

    .line 322
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sRightBsmView:Landroid/widget/ImageView;

    invoke-virtual {p0, v0}, Landroid/widget/ImageView;->setVisibility(I)V

    .line 323
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sStandstillView:Landroid/widget/ImageView;

    invoke-virtual {p0, v0}, Landroid/widget/ImageView;->setVisibility(I)V

    .line 324
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sOpReadyView:Landroid/widget/ImageView;

    invoke-virtual {p0, v0}, Landroid/widget/ImageView;->setVisibility(I)V

    .line 325
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedRow:Landroid/widget/LinearLayout;

    invoke-virtual {p0, v0}, Landroid/widget/LinearLayout;->setVisibility(I)V

    invoke-virtual {v1}, Landroid/widget/FrameLayout;->getContext()Landroid/content/Context;

    move-result-object p0

    new-instance v2, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;

    invoke-direct {v2, p0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;-><init>(Landroid/content/Context;)V

    sput-object v2, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sAlertBannerView:Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;

    new-instance v3, Landroid/widget/FrameLayout$LayoutParams;

    const/16 v4, 0x280

    const/16 v5, 0x64

    invoke-direct {v3, v4, v5}, Landroid/widget/FrameLayout$LayoutParams;-><init>(II)V

    const/16 v4, 0x78

    iput v4, v3, Landroid/widget/FrameLayout$LayoutParams;->topMargin:I

    invoke-virtual {v1, v2, v3}, Landroid/widget/FrameLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 326
    return-object v1
.end method

.method private static buildSetSpeedRow(Landroid/content/Context;)Landroid/widget/LinearLayout;
    .locals 5

    .line 330
    new-instance v0, Landroid/widget/LinearLayout;

    invoke-direct {v0, p0}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    .line 331
    const/4 v1, 0x0

    invoke-virtual {v0, v1}, Landroid/widget/LinearLayout;->setOrientation(I)V

    .line 332
    const/16 v2, 0x11

    invoke-virtual {v0, v2}, Landroid/widget/LinearLayout;->setGravity(I)V

    .line 334
    new-instance v2, Landroid/widget/ImageView;

    invoke-direct {v2, p0}, Landroid/widget/ImageView;-><init>(Landroid/content/Context;)V

    sput-object v2, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedIconView:Landroid/widget/ImageView;

    .line 335
    sget-object v2, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedIconView:Landroid/widget/ImageView;

    sget-object v3, Landroid/widget/ImageView$ScaleType;->FIT_CENTER:Landroid/widget/ImageView$ScaleType;

    invoke-virtual {v2, v3}, Landroid/widget/ImageView;->setScaleType(Landroid/widget/ImageView$ScaleType;)V

    .line 336
    new-instance v2, Landroid/widget/LinearLayout$LayoutParams;

    const/16 v3, 0x1e

    const/16 v4, 0x1d

    invoke-direct {v2, v3, v4}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    .line 337
    const/4 v3, 0x5

    iput v3, v2, Landroid/widget/LinearLayout$LayoutParams;->rightMargin:I

    .line 338
    sget-object v3, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedIconView:Landroid/widget/ImageView;

    invoke-virtual {v0, v3, v2}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 340
    new-instance v2, Landroid/widget/TextView;

    invoke-direct {v2, p0}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    sput-object v2, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedTextView:Landroid/widget/TextView;

    .line 341
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedTextView:Landroid/widget/TextView;

    const/4 v2, -0x1

    invoke-virtual {p0, v2}, Landroid/widget/TextView;->setTextColor(I)V

    .line 342
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedTextView:Landroid/widget/TextView;

    const/high16 v3, 0x41a80000    # 21.0f

    invoke-virtual {p0, v1, v3}, Landroid/widget/TextView;->setTextSize(IF)V

    .line 343
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedTextView:Landroid/widget/TextView;

    sget-object v3, Landroid/graphics/Typeface;->DEFAULT:Landroid/graphics/Typeface;

    invoke-virtual {p0, v3, v1}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;I)V

    .line 344
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedTextView:Landroid/widget/TextView;

    const/16 v3, 0x10

    invoke-virtual {p0, v3}, Landroid/widget/TextView;->setGravity(I)V

    .line 345
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedTextView:Landroid/widget/TextView;

    invoke-virtual {p0, v1}, Landroid/widget/TextView;->setIncludeFontPadding(Z)V

    .line 346
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedTextView:Landroid/widget/TextView;

    const/4 v1, 0x1

    invoke-virtual {p0, v1}, Landroid/widget/TextView;->setSingleLine(Z)V

    .line 347
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedTextView:Landroid/widget/TextView;

    new-instance v1, Landroid/widget/LinearLayout$LayoutParams;

    const/4 v3, -0x2

    invoke-direct {v1, v3, v2}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    invoke-virtual {v0, p0, v1}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 350
    return-object v0
.end method

.method private static ensureOverlay(Landroid/content/Context;)Z
    .locals 4

    .line 276
    const-string v0, "NavdyOpenpilot"

    const/4 v1, 0x0

    :try_start_0
    sget-object v2, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sWindowManager:Landroid/view/WindowManager;

    if-nez v2, :cond_0

    .line 277
    const-string/jumbo v2, "window"

    invoke-virtual {p0, v2}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v2

    check-cast v2, Landroid/view/WindowManager;

    sput-object v2, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sWindowManager:Landroid/view/WindowManager;

    .line 279
    :cond_0
    sget-object v2, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sWindowManager:Landroid/view/WindowManager;

    if-nez v2, :cond_1

    .line 280
    const-string p0, "status overlay no window manager"

    invoke-static {v0, p0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 281
    return v1

    .line 283
    :cond_1
    sget-object v2, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sOverlayView:Landroid/widget/FrameLayout;

    if-nez v2, :cond_2

    .line 284
    invoke-static {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->buildOverlayView(Landroid/content/Context;)Landroid/widget/FrameLayout;

    move-result-object p0

    sput-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sOverlayView:Landroid/widget/FrameLayout;

    .line 285
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sWindowManager:Landroid/view/WindowManager;

    sget-object v2, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sOverlayView:Landroid/widget/FrameLayout;

    invoke-static {}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->buildOverlayLayoutParams()Landroid/view/WindowManager$LayoutParams;

    move-result-object v3

    invoke-interface {p0, v2, v3}, Landroid/view/WindowManager;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 287
    :cond_2
    const/4 p0, 0x1

    return p0

    .line 288
    :catch_0
    move-exception p0

    .line 289
    const-string v2, "status overlay failed"

    invoke-static {v0, v2, p0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 290
    return v1
.end method

.method private static formatCurrentSpeed(D)Ljava/lang/String;
    .locals 2

    invoke-static {p0, p1}, Ljava/lang/Double;->isNaN(D)Z

    move-result v0

    if-nez v0, :cond_0

    invoke-static {p0, p1}, Ljava/lang/Double;->isInfinite(D)Z

    move-result v0

    if-eqz v0, :cond_1

    :cond_0
    const-string p0, "0"

    return-object p0

    :cond_1
    const-wide/16 v0, 0x0

    cmpg-double v0, p0, v0

    if-ltz v0, :cond_0

    invoke-static {p0, p1}, Ljava/lang/Math;->round(D)J

    move-result-wide p0

    invoke-static {p0, p1}, Ljava/lang/String;->valueOf(J)Ljava/lang/String;

    move-result-object p0

    return-object p0
.end method

.method private static formatSetSpeed(D)Ljava/lang/String;
    .locals 3

    .line 409
    const-wide/16 v0, 0x0

    cmpg-double v2, p0, v0

    if-lez v2, :cond_1

    invoke-static {p0, p1}, Ljava/lang/Double;->isNaN(D)Z

    move-result v0

    if-nez v0, :cond_1

    invoke-static {p0, p1}, Ljava/lang/Double;->isInfinite(D)Z

    move-result v0

    if-eqz v0, :cond_0

    goto :goto_0

    .line 412
    :cond_0
    invoke-static {p0, p1}, Ljava/lang/Math;->round(D)J

    move-result-wide p0

    invoke-static {p0, p1}, Ljava/lang/String;->valueOf(J)Ljava/lang/String;

    move-result-object p0

    return-object p0

    .line 410
    :cond_1
    :goto_0
    const-string p0, "--"

    return-object p0
.end method

.method private static gearLabel(Ljava/lang/String;)Ljava/lang/String;
    .locals 1

    .line 442
    const-string v0, "reverse"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_7

    const-string v0, "r"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_0

    goto :goto_3

    .line 445
    :cond_0
    const-string v0, "drive"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_6

    const-string v0, "d"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_1

    goto :goto_2

    .line 448
    :cond_1
    const-string v0, "neutral"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_5

    const-string v0, "n"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_2

    goto :goto_1

    .line 451
    :cond_2
    const-string v0, "park"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_4

    const-string v0, "p"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_3

    goto :goto_0

    .line 454
    :cond_3
    sget-object v0, Ljava/util/Locale;->US:Ljava/util/Locale;

    invoke-virtual {p0, v0}, Ljava/lang/String;->toUpperCase(Ljava/util/Locale;)Ljava/lang/String;

    move-result-object p0

    return-object p0

    .line 452
    :cond_4
    :goto_0
    const-string p0, "P"

    return-object p0

    .line 449
    :cond_5
    :goto_1
    const-string p0, "N"

    return-object p0

    .line 446
    :cond_6
    :goto_2
    const-string p0, "D"

    return-object p0

    .line 443
    :cond_7
    :goto_3
    const-string p0, "R"

    return-object p0
.end method

.method public static handleOpenpilotPayload(Landroid/content/Context;Ljava/lang/String;)V
    .locals 18

    .line 149
    move-object/from16 v0, p1

    const-string v1, "engaged"

    const-string v2, "active"

    const-string v3, "NavdyOpenpilot"

    invoke-static/range {p0 .. p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onOpenpilotPayload(Landroid/content/Context;Ljava/lang/String;)V

    .line 150
    if-nez v0, :cond_0

    .line 151
    return-void

    .line 155
    :cond_0
    :try_start_0
    new-instance v4, Lorg/json/JSONObject;

    invoke-direct {v4, v0}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    .line 156
    const/4 v0, 0x0

    invoke-virtual {v4, v1, v0}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v5

    invoke-virtual {v4, v2, v5}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v5

    .line 157
    invoke-virtual {v4, v2}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result v2
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    const-string v6, "enabled"

    if-nez v2, :cond_1

    :try_start_1
    invoke-virtual {v4, v1}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result v1

    if-nez v1, :cond_1

    .line 158
    invoke-virtual {v4, v6, v0}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v5

    .line 160
    :cond_1
    invoke-virtual {v4, v6, v5}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v1

    .line 161
    const-string v2, "engageable"

    invoke-virtual {v4, v2, v0}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v2

    .line 162
    const-string v6, "opAvailable"

    const/4 v14, 0x1

    if-nez v2, :cond_3

    if-nez v1, :cond_3

    if-eqz v5, :cond_2

    goto :goto_0

    :cond_2
    const/4 v1, 0x0

    goto :goto_1

    :cond_3
    :goto_0
    const/4 v1, 0x1

    :goto_1
    invoke-virtual {v4, v6, v1}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v6

    .line 164
    const-string v1, "gear"

    const-string v2, "gearShifter"

    const-string v7, ""

    invoke-virtual {v4, v2, v7}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v4, v1, v2}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    .line 165
    const-string v2, "leftBlinker"

    invoke-virtual {v4, v2, v0}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v10

    .line 166
    const-string v2, "rightBlinker"

    invoke-virtual {v4, v2, v0}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v11

    .line 167
    const-string v2, "leftBlindspot"

    invoke-virtual {v4, v2, v0}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v12

    .line 168
    const-string v2, "rightBlindspot"

    invoke-virtual {v4, v2, v0}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v13

    .line 169
    const-string v2, "setSpeedKph"

    const-wide/16 v7, 0x0

    move-object v15, v1

    invoke-virtual {v4, v2, v7, v8}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    .line 170
    const-string/jumbo v2, "vEgoKph"

    invoke-virtual {v4, v2, v7, v8}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v7

    .line 171
    if-eqz v5, :cond_4

    invoke-static {v7, v8}, Ljava/lang/Double;->isNaN(D)Z

    move-result v2

    if-nez v2, :cond_4

    invoke-static {v7, v8}, Ljava/lang/Double;->isInfinite(D)Z

    move-result v2

    if-nez v2, :cond_4

    const-wide/high16 v16, 0x3ff0000000000000L    # 1.0

    cmpg-double v2, v7, v16

    if-gtz v2, :cond_4

    const/4 v2, 0x1

    goto :goto_2

    :cond_4
    const/4 v2, 0x0

    .line 172
    :goto_2
    move-wide/from16 v16, v7

    const-string v7, "standstill"

    const-string v8, "cruiseStandstill"

    invoke-virtual {v4, v8, v2}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v2

    invoke-virtual {v4, v7, v2}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v7

    .line 174
    new-instance v2, Ljava/lang/StringBuilder;

    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V

    const-string v4, "state active="

    invoke-virtual {v2, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    invoke-virtual {v2, v5}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v2

    const-string v4, " opAvailable="

    invoke-virtual {v2, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    invoke-virtual {v2, v6}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v2

    const-string v4, " standstill="

    invoke-virtual {v2, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    invoke-virtual {v2, v7}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object v2

    const-string v4, " setSpeedKph="

    invoke-virtual {v2, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    invoke-virtual {v2, v0, v1}, Ljava/lang/StringBuilder;->append(D)Ljava/lang/StringBuilder;

    move-result-object v2

    const-string v4, " gear="

    invoke-virtual {v2, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    .line 178
    invoke-static {v15}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->normalizeGear(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v4

    invoke-virtual {v2, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    const-string v4, " blinkers="

    invoke-virtual {v2, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    .line 179
    invoke-static {v10, v11}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sideText(ZZ)Ljava/lang/String;

    move-result-object v4

    invoke-virtual {v2, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    const-string v4, " bsm="

    invoke-virtual {v2, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    .line 180
    invoke-static {v12, v13}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sideText(ZZ)Ljava/lang/String;

    move-result-object v4

    invoke-virtual {v2, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v2

    .line 174
    invoke-static {v3, v2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 182
    invoke-virtual/range {p0 .. p0}, Landroid/content/Context;->getApplicationContext()Landroid/content/Context;

    move-result-object v4

    move-wide v8, v0

    invoke-static/range {v4 .. v13}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->updateOpenpilotOverlay(Landroid/content/Context;ZZZDZZZZ)V

    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sPathView:Lcom/navdy/hud/app/openpilot/OpenpilotPathView;

    if-eqz v0, :cond_5

    move-object/from16 v1, p1

    move v2, v5

    invoke-virtual {v0, v1, v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->updatePayload(Ljava/lang/String;Z)V

    :cond_5
    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sAlertBannerView:Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;

    if-eqz v0, :cond_alert_banner

    move-object/from16 v1, p1

    invoke-virtual {v0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->updatePayload(Ljava/lang/String;)V

    :cond_alert_banner
    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sCurrentSpeedTextView:Landroid/widget/TextView;

    if-eqz v0, :cond_7

    invoke-static/range {v16 .. v17}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->formatCurrentSpeed(D)Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    invoke-static {}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->getLastCameraSpeedLimit()I

    move-result v1

    if-lez v1, :cond_navdy_camera_speed_white

    int-to-double v8, v1

    cmpl-double v4, v16, v8

    if-lez v4, :cond_navdy_camera_speed_white

    const/high16 v1, -0x10000

    goto :goto_navdy_camera_speed_color

    :cond_navdy_camera_speed_white
    const/4 v1, -0x1

    :goto_navdy_camera_speed_color
    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setTextColor(I)V

    const/16 v1, 0x8

    if-eqz v5, :cond_6

    const/4 v1, 0x0

    :cond_6
    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setVisibility(I)V

    .line 185
    :cond_7
    sget-boolean v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sHaveActive:Z

    if-eqz v0, :cond_8

    sget-boolean v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLastActive:Z

    if-eq v0, v5, :cond_a

    .line 186
    :cond_8
    if-eqz v5, :cond_9

    const-string v0, "OP ENGAGED"

    goto :goto_3

    :cond_9
    const-string v0, "OP DISENGAGED"

    :goto_3
    invoke-static {v3, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 187
    sput-boolean v14, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sHaveActive:Z

    .line 188
    sput-boolean v5, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLastActive:Z

    .line 191
    :cond_a
    invoke-static {v15}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->normalizeGear(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    .line 192
    invoke-virtual {v0}, Ljava/lang/String;->length()I

    move-result v1

    if-lez v1, :cond_b

    sget-object v1, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLastGear:Ljava/lang/String;

    invoke-virtual {v0, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-nez v1, :cond_b

    .line 193
    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "GEAR "

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->gearLabel(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v2

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-static {v3, v1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 194
    sput-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLastGear:Ljava/lang/String;

    .line 197
    :cond_b
    sget-boolean v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sHaveBlinker:Z

    if-eqz v0, :cond_c

    sget-boolean v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLastLeftBlinker:Z

    if-ne v0, v10, :cond_c

    sget-boolean v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLastRightBlinker:Z

    if-eq v0, v11, :cond_d

    .line 198
    :cond_c
    invoke-static {v10, v11}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->blinkerLabel(ZZ)Ljava/lang/String;

    move-result-object v0

    invoke-static {v3, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 199
    sput-boolean v14, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sHaveBlinker:Z

    .line 200
    sput-boolean v10, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLastLeftBlinker:Z

    .line 201
    sput-boolean v11, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLastRightBlinker:Z

    .line 204
    :cond_d
    sget-boolean v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sHaveBlindspot:Z

    if-eqz v0, :cond_e

    sget-boolean v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLastLeftBlindspot:Z

    if-ne v0, v12, :cond_e

    sget-boolean v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLastRightBlindspot:Z

    if-eq v0, v13, :cond_11

    .line 205
    :cond_e
    if-nez v12, :cond_10

    if-eqz v13, :cond_f

    goto :goto_4

    .line 207
    :cond_f
    const-string v0, "BSM CLEAR"

    goto :goto_5

    .line 206
    :cond_10
    :goto_4
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "BSM "

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-static {v12, v13}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sideText(ZZ)Ljava/lang/String;

    move-result-object v1

    sget-object v2, Ljava/util/Locale;->US:Ljava/util/Locale;

    invoke-virtual {v1, v2}, Ljava/lang/String;->toUpperCase(Ljava/util/Locale;)Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    .line 205
    :goto_5
    invoke-static {v3, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 208
    sput-boolean v14, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sHaveBlindspot:Z

    .line 209
    sput-boolean v12, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLastLeftBlindspot:Z

    .line 210
    sput-boolean v13, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLastRightBlindspot:Z
    :try_end_1
    .catch Ljava/lang/Exception; {:try_start_1 .. :try_end_1} :catch_0

    .line 214
    :cond_11
    goto :goto_6

    .line 212
    :catch_0
    move-exception v0

    .line 213
    const-string v1, "bad openpilot display payload"

    invoke-static {v3, v1, v0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;Ljava/lang/Throwable;)I

    .line 215
    :goto_6
    return-void
.end method

.method private static normalizeGear(Ljava/lang/String;)Ljava/lang/String;
    .locals 1

    .line 458
    if-nez p0, :cond_0

    .line 459
    const-string p0, ""

    return-object p0

    .line 461
    :cond_0
    invoke-virtual {p0}, Ljava/lang/String;->trim()Ljava/lang/String;

    move-result-object p0

    sget-object v0, Ljava/util/Locale;->US:Ljava/util/Locale;

    invoke-virtual {p0, v0}, Ljava/lang/String;->toLowerCase(Ljava/util/Locale;)Ljava/lang/String;

    move-result-object p0

    .line 462
    const-string v0, ".reverse"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_1

    .line 463
    const-string p0, "reverse"

    return-object p0

    .line 465
    :cond_1
    const-string v0, ".drive"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_2

    .line 466
    const-string p0, "drive"

    return-object p0

    .line 468
    :cond_2
    const-string v0, ".neutral"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_3

    .line 469
    const-string p0, "neutral"

    return-object p0

    .line 471
    :cond_3
    const-string v0, ".park"

    invoke-virtual {p0, v0}, Ljava/lang/String;->endsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_4

    .line 472
    const-string p0, "park"

    return-object p0

    .line 474
    :cond_4
    return-object p0
.end method

.method private static scheduleTurnBlink()V
    .locals 4

    .line 260
    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sUiHandler:Landroid/os/Handler;

    sget-object v1, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sTurnBlinkRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0, v1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 261
    const/4 v0, 0x1

    sput-boolean v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sTurnBlinkScheduled:Z

    .line 262
    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sUiHandler:Landroid/os/Handler;

    sget-object v1, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sTurnBlinkRunnable:Ljava/lang/Runnable;

    const-wide/16 v2, 0x1c2

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 263
    return-void
.end method

.method private static setImageByName(Landroid/content/Context;Landroid/widget/ImageView;Ljava/lang/String;)V
    .locals 2

    .line 366
    invoke-virtual {p0}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;

    move-result-object v0

    const-string v1, "drawable"

    invoke-virtual {p0}, Landroid/content/Context;->getPackageName()Ljava/lang/String;

    move-result-object p0

    invoke-virtual {v0, p2, v1, p0}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I

    move-result p0

    .line 367
    if-eqz p0, :cond_0

    .line 368
    invoke-virtual {p1, p0}, Landroid/widget/ImageView;->setImageResource(I)V

    goto :goto_0

    .line 370
    :cond_0
    new-instance p0, Ljava/lang/StringBuilder;

    invoke-direct {p0}, Ljava/lang/StringBuilder;-><init>()V

    const-string p1, "missing drawable "

    invoke-virtual {p0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p0

    invoke-virtual {p0, p2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p0

    invoke-virtual {p0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p0

    const-string p1, "NavdyOpenpilot"

    invoke-static {p1, p0}, Landroid/util/Log;->w(Ljava/lang/String;Ljava/lang/String;)I

    .line 372
    :goto_0
    return-void
.end method

.method public static setMusicTitle(Ljava/lang/String;)V
    .locals 3

    if-nez p0, :cond_0

    const-string p0, ""

    :cond_0
    sput-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sMusicTitle:Ljava/lang/String;

    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sMusicTextView:Landroid/widget/TextView;

    if-eqz v0, :cond_2

    invoke-virtual {v0, p0}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    sget-boolean v1, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLastActive:Z

    if-eqz v1, :cond_1

    invoke-static {p0}, Landroid/text/TextUtils;->isEmpty(Ljava/lang/CharSequence;)Z

    move-result v2

    if-nez v2, :cond_1

    const/4 v1, 0x0

    goto :goto_0

    :cond_1
    const/16 v1, 0x8

    :goto_0
    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setVisibility(I)V

    :cond_2
    return-void
.end method

.method private static setOpenpilotIconState(ZZ)V
    .locals 2

    .line 375
    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sOpReadyView:Landroid/widget/ImageView;

    if-nez v0, :cond_0

    .line 376
    return-void

    .line 378
    :cond_0
    if-eqz p0, :cond_1

    const p0, -0xff19ba

    goto :goto_0

    :cond_1
    if-eqz p1, :cond_2

    const/4 p0, -0x1

    goto :goto_0

    :cond_2
    const p0, -0x888889

    :goto_0
    invoke-static {v0, p0}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->tintImage(Landroid/widget/ImageView;I)V

    .line 383
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sOpReadyView:Landroid/widget/ImageView;

    const/4 v1, 0x0

    invoke-virtual {p0, v1}, Landroid/widget/ImageView;->setVisibility(I)V

    .line 384
    return-void
.end method

.method private static setTurnBlinkers(ZZ)V
    .locals 3

    .line 239
    sget-boolean v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLeftBlinkerRequested:Z

    const/4 v1, 0x1

    const/4 v2, 0x0

    if-ne v0, p0, :cond_1

    sget-boolean v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sRightBlinkerRequested:Z

    if-eq v0, p1, :cond_0

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    goto :goto_1

    :cond_1
    :goto_0
    const/4 v0, 0x1

    .line 241
    :goto_1
    sput-boolean p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLeftBlinkerRequested:Z

    .line 242
    sput-boolean p1, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sRightBlinkerRequested:Z

    .line 244
    if-nez p0, :cond_2

    if-nez p1, :cond_2

    .line 245
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sUiHandler:Landroid/os/Handler;

    sget-object p1, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sTurnBlinkRunnable:Ljava/lang/Runnable;

    invoke-virtual {p0, p1}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 246
    sput-boolean v2, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sTurnBlinkScheduled:Z

    .line 247
    sput-boolean v2, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sTurnBlinkOn:Z

    .line 248
    invoke-static {}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->applyTurnBlinkVisibility()V

    .line 249
    return-void

    .line 252
    :cond_2
    if-nez v0, :cond_3

    sget-boolean p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sTurnBlinkScheduled:Z

    if-nez p0, :cond_4

    .line 253
    :cond_3
    sput-boolean v1, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sTurnBlinkOn:Z

    .line 254
    invoke-static {}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->applyTurnBlinkVisibility()V

    .line 255
    invoke-static {}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->scheduleTurnBlink()V

    .line 257
    :cond_4
    return-void
.end method

.method private static sideText(ZZ)Ljava/lang/String;
    .locals 0

    .line 429
    if-eqz p0, :cond_0

    if-eqz p1, :cond_0

    .line 430
    const-string p0, "both"

    return-object p0

    .line 432
    :cond_0
    if-eqz p0, :cond_1

    .line 433
    const-string p0, "left"

    return-object p0

    .line 435
    :cond_1
    if-eqz p1, :cond_2

    .line 436
    const-string p0, "right"

    return-object p0

    .line 438
    :cond_2
    const-string p0, "off"

    return-object p0
.end method

.method private static tintImage(Landroid/widget/ImageView;I)V
    .locals 1

    .line 387
    if-eqz p0, :cond_0

    .line 388
    sget-object v0, Landroid/graphics/PorterDuff$Mode;->SRC_IN:Landroid/graphics/PorterDuff$Mode;

    invoke-virtual {p0, p1, v0}, Landroid/widget/ImageView;->setColorFilter(ILandroid/graphics/PorterDuff$Mode;)V

    .line 390
    :cond_0
    return-void
.end method

.method private static applyStatusLayout(Z)V
    .locals 4

    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLeftTurnView:Landroid/widget/ImageView;

    invoke-virtual {v0}, Landroid/widget/ImageView;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v1

    check-cast v1, Landroid/widget/FrameLayout$LayoutParams;

    if-eqz p0, :cond_left_turn_disengaged

    const/16 v2, 0x80

    const/16 v3, 0xf2

    goto :goto_left_turn

    :cond_left_turn_disengaged
    const/16 v2, 0x86

    const/16 v3, 0xf0

    :goto_left_turn
    iput v2, v1, Landroid/widget/FrameLayout$LayoutParams;->leftMargin:I

    iput v3, v1, Landroid/widget/FrameLayout$LayoutParams;->topMargin:I

    invoke-virtual {v0, v1}, Landroid/widget/ImageView;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sRightTurnView:Landroid/widget/ImageView;

    invoke-virtual {v0}, Landroid/widget/ImageView;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v1

    check-cast v1, Landroid/widget/FrameLayout$LayoutParams;

    if-eqz p0, :cond_right_turn_disengaged

    const/16 v2, 0x1e8

    const/16 v3, 0xf2

    goto :goto_right_turn

    :cond_right_turn_disengaged
    const/16 v2, 0x1e2

    const/16 v3, 0xf0

    :goto_right_turn
    iput v2, v1, Landroid/widget/FrameLayout$LayoutParams;->leftMargin:I

    iput v3, v1, Landroid/widget/FrameLayout$LayoutParams;->topMargin:I

    invoke-virtual {v0, v1}, Landroid/widget/ImageView;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLeftBsmView:Landroid/widget/ImageView;

    invoke-virtual {v0}, Landroid/widget/ImageView;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v1

    check-cast v1, Landroid/widget/FrameLayout$LayoutParams;

    if-eqz p0, :cond_left_bsm_disengaged

    const/16 v2, 0xa7

    goto :goto_left_bsm

    :cond_left_bsm_disengaged
    const/16 v2, 0xad

    :goto_left_bsm
    iput v2, v1, Landroid/widget/FrameLayout$LayoutParams;->leftMargin:I

    invoke-virtual {v0, v1}, Landroid/widget/ImageView;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sRightBsmView:Landroid/widget/ImageView;

    invoke-virtual {v0}, Landroid/widget/ImageView;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v1

    check-cast v1, Landroid/widget/FrameLayout$LayoutParams;

    if-eqz p0, :cond_right_bsm_disengaged

    const/16 v2, 0x1b7

    goto :goto_right_bsm

    :cond_right_bsm_disengaged
    const/16 v2, 0x1b1

    :goto_right_bsm
    iput v2, v1, Landroid/widget/FrameLayout$LayoutParams;->leftMargin:I

    invoke-virtual {v0, v1}, Landroid/widget/ImageView;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sStandstillView:Landroid/widget/ImageView;

    invoke-virtual {v0}, Landroid/widget/ImageView;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v1

    check-cast v1, Landroid/widget/FrameLayout$LayoutParams;

    if-eqz p0, :cond_standstill_disengaged

    const/16 v2, 0xe2

    const/16 v3, 0x112

    goto :goto_standstill

    :cond_standstill_disengaged
    const/16 v2, 0xe4

    const/16 v3, 0xeb

    :goto_standstill
    iput v2, v1, Landroid/widget/FrameLayout$LayoutParams;->leftMargin:I

    iput v3, v1, Landroid/widget/FrameLayout$LayoutParams;->topMargin:I

    invoke-virtual {v0, v1}, Landroid/widget/ImageView;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sOpReadyView:Landroid/widget/ImageView;

    invoke-virtual {v0}, Landroid/widget/ImageView;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v1

    check-cast v1, Landroid/widget/FrameLayout$LayoutParams;

    if-eqz p0, :cond_op_ready_disengaged

    const/16 v3, 0x113

    goto :goto_op_ready

    :cond_op_ready_disengaged
    const/16 v3, 0xf0

    :goto_op_ready
    iput v3, v1, Landroid/widget/FrameLayout$LayoutParams;->topMargin:I

    invoke-virtual {v0, v1}, Landroid/widget/ImageView;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedRow:Landroid/widget/LinearLayout;

    invoke-virtual {v0}, Landroid/widget/LinearLayout;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v1

    check-cast v1, Landroid/widget/FrameLayout$LayoutParams;

    if-eqz p0, :cond_set_speed_disengaged

    const/16 v3, 0x128

    goto :goto_set_speed

    :cond_set_speed_disengaged
    const/16 v3, 0x12f

    :goto_set_speed
    iput v3, v1, Landroid/widget/FrameLayout$LayoutParams;->topMargin:I

    invoke-virtual {v0, v1}, Landroid/widget/LinearLayout;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    return-void
.end method

.method private static updateOpenpilotOverlay(Landroid/content/Context;ZZZDZZZZ)V
    .locals 1

    .line 220
    invoke-static {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->ensureOverlay(Landroid/content/Context;)Z

    move-result v0

    if-nez v0, :cond_0

    .line 221
    return-void

    .line 224
    :cond_0
    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->applyStatusLayout(Z)V

    invoke-static {}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->updateOutsideTemp()V

    invoke-static {p6, p7}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->setTurnBlinkers(ZZ)V

    sget-object p6, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sEngagedTopMask:Landroid/view/View;

    const/16 p7, 0x8

    if-eqz p1, :cond_1

    const/4 p7, 0x0

    :cond_1
    invoke-virtual {p6, p7}, Landroid/view/View;->setVisibility(I)V

    sget-object p6, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sEngagedBodyMask:Landroid/view/View;

    invoke-virtual {p6, p7}, Landroid/view/View;->setVisibility(I)V

    sget-object p6, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sMusicTextView:Landroid/widget/TextView;

    sget-object p7, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sMusicTitle:Ljava/lang/String;

    invoke-static {p7}, Landroid/text/TextUtils;->isEmpty(Ljava/lang/CharSequence;)Z

    move-result p7

    if-eqz p1, :cond_2

    if-nez p7, :cond_2

    const/4 p7, 0x0

    goto :goto_0

    :cond_2
    const/16 p7, 0x8

    :goto_0
    invoke-virtual {p6, p7}, Landroid/widget/TextView;->setVisibility(I)V

    .line 225
    sget-object p6, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sLeftBsmView:Landroid/widget/ImageView;

    const/16 p7, 0x8

    const/4 v0, 0x0

    if-eqz p8, :cond_3

    const/4 p8, 0x0

    goto :goto_1

    :cond_3
    const/16 p8, 0x8

    :goto_1
    invoke-virtual {p6, p8}, Landroid/widget/ImageView;->setVisibility(I)V

    .line 226
    sget-object p6, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sRightBsmView:Landroid/widget/ImageView;

    if-eqz p9, :cond_4

    const/4 p8, 0x0

    goto :goto_2

    :cond_4
    const/16 p8, 0x8

    :goto_2
    invoke-virtual {p6, p8}, Landroid/widget/ImageView;->setVisibility(I)V

    .line 227
    sget-object p6, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sStandstillView:Landroid/widget/ImageView;

    if-eqz p3, :cond_5

    const/4 p7, 0x0

    :cond_5
    invoke-virtual {p6, p7}, Landroid/widget/ImageView;->setVisibility(I)V

    .line 228
    invoke-static {p1, p2}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->setOpenpilotIconState(ZZ)V

    .line 230
    if-eqz p1, :cond_6

    const-string p2, "navdy_op_set_green"

    goto :goto_3

    :cond_6
    const-string p2, "navdy_op_set_white"

    .line 231
    :goto_3
    sget-object p3, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedIconView:Landroid/widget/ImageView;

    invoke-static {p0, p3, p2}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->setImageByName(Landroid/content/Context;Landroid/widget/ImageView;Ljava/lang/String;)V

    .line 232
    if-eqz p1, :cond_7

    const p0, -0xff19ba

    goto :goto_4

    :cond_7
    const/4 p0, -0x1

    .line 233
    :goto_4
    sget-object p1, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedTextView:Landroid/widget/TextView;

    invoke-virtual {p1, p0}, Landroid/widget/TextView;->setTextColor(I)V

    .line 234
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedTextView:Landroid/widget/TextView;

    invoke-static {p4, p5}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->formatSetSpeed(D)Ljava/lang/String;

    move-result-object p1

    invoke-virtual {p0, p1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 235
    sget-object p0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sSetSpeedRow:Landroid/widget/LinearLayout;

    invoke-virtual {p0, v0}, Landroid/widget/LinearLayout;->setVisibility(I)V

    .line 236
    return-void
.end method

.method private static updateOutsideTemp()V
    .locals 7

    sget-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->sOutsideTempTextView:Landroid/widget/TextView;

    if-nez v0, :cond_0

    return-void

    :cond_0
    const-string v1, "--\u00b0C"

    :try_start_0
    invoke-static {}, Lcom/navdy/hud/app/obd/ObdManager;->getInstance()Lcom/navdy/hud/app/obd/ObdManager;

    move-result-object v2

    invoke-virtual {v2}, Lcom/navdy/hud/app/obd/ObdManager;->getSupportedPids()Lcom/navdy/obd/PidSet;

    move-result-object v4

    if-eqz v4, :cond_1

    const/16 v5, 0x46

    invoke-virtual {v4, v5}, Lcom/navdy/obd/PidSet;->contains(I)Z

    move-result v4

    if-eqz v4, :cond_1

    const/16 v3, 0x46

    invoke-virtual {v2, v3}, Lcom/navdy/hud/app/obd/ObdManager;->getPidValue(I)D

    move-result-wide v2

    invoke-static {v2, v3}, Ljava/lang/Double;->isNaN(D)Z

    move-result v4

    if-nez v4, :cond_1

    invoke-static {v2, v3}, Ljava/lang/Double;->isInfinite(D)Z

    move-result v4

    if-nez v4, :cond_1

    const-wide/high16 v4, -0x4010000000000000L    # -1.0

    cmpl-double v6, v2, v4

    if-eqz v6, :cond_1

    invoke-static {v2, v3}, Ljava/lang/Math;->round(D)J

    move-result-wide v2

    new-instance v4, Ljava/lang/StringBuilder;

    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v4, v2, v3}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    move-result-object v2

    const-string/jumbo v3, "\u00b0C"

    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    :cond_1
    :goto_0
    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    return-void

    :catch_0
    move-exception v2

    goto :goto_0
.end method


# virtual methods
.method public onReceive(Landroid/content/Context;Landroid/content/Intent;)V
    .locals 3

    .line 112
    if-eqz p1, :cond_6

    if-nez p2, :cond_0

    goto/16 :goto_0

    .line 116
    :cond_0
    invoke-virtual {p2}, Landroid/content/Intent;->getAction()Ljava/lang/String;

    move-result-object v0

    .line 117
    const-string v1, "com.navdy.OPENPILOT_STATE"

    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    const-string v2, "NavdyOpenpilot"

    if-eqz v1, :cond_1

    .line 118
    const-string v0, "payload"

    invoke-virtual {p2, v0}, Landroid/content/Intent;->getStringExtra(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    .line 119
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "openpilot payload="

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    invoke-static {v2, v0}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 120
    invoke-static {p1, p2}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->handleOpenpilotPayload(Landroid/content/Context;Ljava/lang/String;)V

    .line 121
    return-void

    .line 124
    :cond_1
    const-string p2, "com.navdy.AMBIENT_TEST_REVERSE"

    invoke-virtual {p2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p2

    if-eqz p2, :cond_2

    .line 125
    const-string p2, "ambient test reverse"

    invoke-static {v2, p2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 126
    const-string p2, "reverse"

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onGearText(Landroid/content/Context;Ljava/lang/String;)V

    .line 127
    return-void

    .line 130
    :cond_2
    const-string p2, "com.navdy.AMBIENT_TEST_DRIVE"

    invoke-virtual {p2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p2

    if-eqz p2, :cond_3

    .line 131
    const-string p2, "ambient test drive"

    invoke-static {v2, p2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 132
    const-string p2, "drive"

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onGearText(Landroid/content/Context;Ljava/lang/String;)V

    .line 133
    return-void

    .line 136
    :cond_3
    const-string p2, "com.navdy.AMBIENT_TEST_OVERSPEED_ON"

    invoke-virtual {p2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p2

    if-eqz p2, :cond_4

    .line 137
    const-string p2, "ambient test overspeed on"

    invoke-static {v2, p2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 138
    const/4 p2, 0x1

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onOverspeedChanged(Landroid/content/Context;Z)V

    .line 139
    return-void

    .line 142
    :cond_4
    const-string p2, "com.navdy.AMBIENT_TEST_OVERSPEED_OFF"

    invoke-virtual {p2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p2

    if-eqz p2, :cond_5

    .line 143
    const-string p2, "ambient test overspeed off"

    invoke-static {v2, p2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 144
    const/4 p2, 0x0

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onOverspeedChanged(Landroid/content/Context;Z)V

    .line 146
    :cond_5
    return-void

    .line 113
    :cond_6
    :goto_0
    return-void
.end method
