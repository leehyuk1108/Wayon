.class public final Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;
.super Landroid/view/View;
.source "OpenpilotAutoHoldView.java"


# static fields
.field private static final COLOR_PROGRESS:I

.field private static final RING_RADIUS:F = 21.0f

.field private static final RING_WIDTH:F = 3.0f

.field private static final TIMER_X:F = 60.0f


# instance fields
.field private active:Z

.field private elapsedSeconds:F

.field private progress:F

.field private final ringBounds:Landroid/graphics/RectF;

.field private final ringPaint:Landroid/graphics/Paint;

.field private startedAtMs:J

.field private final textPaint:Landroid/graphics/Paint;


# direct methods
.method static constructor <clinit>()V
    .locals 3

    .line 17
    const/16 v0, 0xff

    const/16 v1, 0x70

    const/16 v2, 0x3a

    invoke-static {v2, v0, v1}, Landroid/graphics/Color;->rgb(III)I

    move-result v0

    sput v0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->COLOR_PROGRESS:I

    return-void
.end method

.method public constructor <init>(Landroid/content/Context;)V
    .locals 1

    .line 31
    invoke-direct {p0, p1}, Landroid/view/View;-><init>(Landroid/content/Context;)V

    .line 22
    new-instance p1, Landroid/graphics/Paint;

    const/4 v0, 0x1

    invoke-direct {p1, v0}, Landroid/graphics/Paint;-><init>(I)V

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringPaint:Landroid/graphics/Paint;

    .line 23
    new-instance p1, Landroid/graphics/Paint;

    invoke-direct {p1, v0}, Landroid/graphics/Paint;-><init>(I)V

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->textPaint:Landroid/graphics/Paint;

    .line 24
    new-instance p1, Landroid/graphics/RectF;

    invoke-direct {p1}, Landroid/graphics/RectF;-><init>()V

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringBounds:Landroid/graphics/RectF;

    .line 32
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringPaint:Landroid/graphics/Paint;

    sget-object v0, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 33
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringPaint:Landroid/graphics/Paint;

    sget-object v0, Landroid/graphics/Paint$Cap;->ROUND:Landroid/graphics/Paint$Cap;

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setStrokeCap(Landroid/graphics/Paint$Cap;)V

    .line 34
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringPaint:Landroid/graphics/Paint;

    const/high16 v0, 0x40400000    # 3.0f

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 35
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->textPaint:Landroid/graphics/Paint;

    const/4 v0, -0x1

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setColor(I)V

    .line 36
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->textPaint:Landroid/graphics/Paint;

    const/high16 v0, 0x41f00000    # 30.0f

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setTextSize(F)V

    .line 37
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->textPaint:Landroid/graphics/Paint;

    sget-object v0, Landroid/graphics/Typeface;->DEFAULT_BOLD:Landroid/graphics/Typeface;

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setTypeface(Landroid/graphics/Typeface;)Landroid/graphics/Typeface;

    .line 38
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->textPaint:Landroid/graphics/Paint;

    sget-object v0, Landroid/graphics/Paint$Align;->LEFT:Landroid/graphics/Paint$Align;

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setTextAlign(Landroid/graphics/Paint$Align;)V

    .line 39
    const/4 p1, 0x0

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->setWillNotDraw(Z)V

    .line 40
    const/16 p1, 0x8

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->setVisibility(I)V

    .line 41
    return-void
.end method

.method private static clamp01(F)F
    .locals 1

    .line 91
    const/high16 v0, 0x3f800000    # 1.0f

    invoke-static {v0, p0}, Ljava/lang/Math;->min(FF)F

    move-result p0

    const/4 v0, 0x0

    invoke-static {v0, p0}, Ljava/lang/Math;->max(FF)F

    move-result p0

    return p0
.end method


# virtual methods
.method protected onDraw(Landroid/graphics/Canvas;)V
    .locals 17

    .line 72
    move-object/from16 v0, p0

    invoke-super/range {p0 .. p1}, Landroid/view/View;->onDraw(Landroid/graphics/Canvas;)V

    .line 73
    invoke-virtual {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->getHeight()I

    move-result v1

    int-to-float v1, v1

    const/high16 v2, 0x3f000000    # 0.5f

    mul-float v1, v1, v2

    .line 74
    iget-object v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringBounds:Landroid/graphics/RectF;

    const/high16 v4, 0x41a80000    # 21.0f

    sub-float v5, v1, v4

    const/high16 v6, 0x423c0000    # 47.0f

    add-float/2addr v4, v1

    const/high16 v7, 0x40a00000    # 5.0f

    invoke-virtual {v3, v7, v5, v6, v4}, Landroid/graphics/RectF;->set(FFFF)V

    .line 76
    iget-object v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringPaint:Landroid/graphics/Paint;

    const/16 v4, 0x46

    const/16 v5, 0xff

    invoke-static {v4, v5, v5, v5}, Landroid/graphics/Color;->argb(IIII)I

    move-result v4

    invoke-virtual {v3, v4}, Landroid/graphics/Paint;->setColor(I)V

    .line 77
    iget-object v6, v0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringBounds:Landroid/graphics/RectF;

    const/4 v9, 0x0

    iget-object v10, v0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringPaint:Landroid/graphics/Paint;

    const/high16 v7, -0x3d4c0000    # -90.0f

    const/high16 v8, 0x43b40000    # 360.0f

    move-object/from16 v5, p1

    invoke-virtual/range {v5 .. v10}, Landroid/graphics/Canvas;->drawArc(Landroid/graphics/RectF;FFZLandroid/graphics/Paint;)V

    .line 78
    iget v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->progress:F

    const/4 v4, 0x0

    cmpl-float v3, v3, v4

    if-lez v3, :cond_0

    .line 79
    iget-object v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringPaint:Landroid/graphics/Paint;

    sget v4, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->COLOR_PROGRESS:I

    invoke-virtual {v3, v4}, Landroid/graphics/Paint;->setColor(I)V

    .line 80
    iget-object v12, v0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringBounds:Landroid/graphics/RectF;

    const/high16 v3, 0x43b40000    # 360.0f

    iget v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->progress:F

    mul-float v14, v4, v3

    const/4 v15, 0x0

    iget-object v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringPaint:Landroid/graphics/Paint;

    const/high16 v13, -0x3d4c0000    # -90.0f

    move-object/from16 v11, p1

    move-object/from16 v16, v3

    invoke-virtual/range {v11 .. v16}, Landroid/graphics/Canvas;->drawArc(Landroid/graphics/RectF;FFZLandroid/graphics/Paint;)V

    .line 83
    :cond_0
    iget v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->elapsedSeconds:F

    float-to-int v3, v3

    const/4 v4, 0x0

    invoke-static {v4, v3}, Ljava/lang/Math;->max(II)I

    move-result v3

    .line 84
    sget-object v5, Ljava/util/Locale;->US:Ljava/util/Locale;

    div-int/lit8 v6, v3, 0x3c

    invoke-static {v6}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;

    move-result-object v6

    rem-int/lit8 v3, v3, 0x3c

    invoke-static {v3}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;

    move-result-object v3

    const/4 v7, 0x2

    new-array v7, v7, [Ljava/lang/Object;

    aput-object v6, v7, v4

    const/4 v4, 0x1

    aput-object v3, v7, v4

    const-string v3, "%02d:%02d"

    invoke-static {v5, v3, v7}, Ljava/lang/String;->format(Ljava/util/Locale;Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v3

    .line 85
    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->textPaint:Landroid/graphics/Paint;

    invoke-virtual {v4}, Landroid/graphics/Paint;->getFontMetrics()Landroid/graphics/Paint$FontMetrics;

    move-result-object v4

    .line 86
    iget v5, v4, Landroid/graphics/Paint$FontMetrics;->ascent:F

    iget v4, v4, Landroid/graphics/Paint$FontMetrics;->descent:F

    add-float/2addr v5, v4

    mul-float v5, v5, v2

    sub-float/2addr v1, v5

    .line 87
    const/high16 v2, 0x42700000    # 60.0f

    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->textPaint:Landroid/graphics/Paint;

    move-object/from16 v5, p1

    invoke-virtual {v5, v3, v2, v1, v4}, Landroid/graphics/Canvas;->drawText(Ljava/lang/String;FFLandroid/graphics/Paint;)V

    .line 88
    return-void
.end method

.method public updatePayload(Lorg/json/JSONObject;)V
    .locals 12

    .line 44
    const/4 v0, 0x0

    if-eqz p1, :cond_0

    .line 45
    const-string v1, "standstill"

    invoke-virtual {p1, v1, v0}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v1

    const-string v2, "autoHoldActive"

    invoke-virtual {p1, v2, v1}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v1

    if-eqz v1, :cond_0

    const/4 v1, 0x1

    goto :goto_0

    :cond_0
    const/4 v1, 0x0

    .line 46
    :goto_0
    invoke-static {}, Landroid/os/SystemClock;->elapsedRealtime()J

    move-result-wide v2

    .line 48
    const-wide/16 v4, 0x0

    const-wide/16 v6, 0x0

    const/4 v8, 0x0

    if-eqz v1, :cond_4

    .line 49
    iget-boolean v9, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->active:Z

    if-eqz v9, :cond_1

    iget-wide v9, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->startedAtMs:J

    cmp-long v11, v9, v6

    if-gtz v11, :cond_2

    .line 50
    :cond_1
    iput-wide v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->startedAtMs:J

    .line 52
    :cond_2
    const-string v6, "autoHoldElapsedSec"

    const-wide/high16 v9, -0x4010000000000000L    # -1.0

    invoke-virtual {p1, v6, v9, v10}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v6

    .line 53
    cmpl-double v9, v6, v4

    if-ltz v9, :cond_3

    .line 54
    double-to-float v2, v6

    invoke-static {v8, v2}, Ljava/lang/Math;->max(FF)F

    move-result v2

    goto :goto_1

    .line 55
    :cond_3
    iget-wide v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->startedAtMs:J

    sub-long/2addr v2, v6

    long-to-float v2, v2

    const/high16 v3, 0x447a0000    # 1000.0f

    div-float/2addr v2, v3

    invoke-static {v8, v2}, Ljava/lang/Math;->max(FF)F

    move-result v2

    :goto_1
    iput v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->elapsedSeconds:F

    .line 56
    goto :goto_2

    .line 57
    :cond_4
    iput-wide v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->startedAtMs:J

    .line 58
    iput v8, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->elapsedSeconds:F

    .line 61
    :goto_2
    iput-boolean v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->active:Z

    .line 62
    if-nez p1, :cond_5

    goto :goto_3

    .line 63
    :cond_5
    const-string v1, "autoHoldEpbProgress"

    invoke-virtual {p1, v1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v1

    double-to-float p1, v1

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->clamp01(F)F

    move-result v8

    :goto_3
    iput v8, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->progress:F

    .line 64
    iget-boolean p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->active:Z

    if-eqz p1, :cond_6

    goto :goto_4

    :cond_6
    const/16 v0, 0x8

    :goto_4
    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->setVisibility(I)V

    .line 65
    iget-boolean p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->active:Z

    if-eqz p1, :cond_7

    .line 66
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->invalidate()V

    .line 68
    :cond_7
    return-void
.end method
