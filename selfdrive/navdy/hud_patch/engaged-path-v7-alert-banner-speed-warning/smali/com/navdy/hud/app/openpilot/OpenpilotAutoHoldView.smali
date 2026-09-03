.class public final Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;
.super Landroid/view/View;
.source "OpenpilotAutoHoldView.java"


# static fields
.field private static final COLOR_PROGRESS:I = -0xc60090

.field private static final RING_CENTER_X:F = 26.0f

.field private static final RING_RADIUS:F = 21.0f

.field private static final RING_WIDTH:F = 3.0f


# instance fields
.field private elapsedSeconds:F

.field private progress:F

.field private final ringBounds:Landroid/graphics/RectF;

.field private final ringPaint:Landroid/graphics/Paint;

.field private final textPaint:Landroid/graphics/Paint;


# direct methods
.method public constructor <init>(Landroid/content/Context;)V
    .registers 3

    .line 26
    invoke-direct {p0, p1}, Landroid/view/View;-><init>(Landroid/content/Context;)V

    .line 19
    new-instance p1, Landroid/graphics/Paint;

    const/4 v0, 0x1

    invoke-direct {p1, v0}, Landroid/graphics/Paint;-><init>(I)V

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringPaint:Landroid/graphics/Paint;

    .line 20
    new-instance p1, Landroid/graphics/Paint;

    invoke-direct {p1, v0}, Landroid/graphics/Paint;-><init>(I)V

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->textPaint:Landroid/graphics/Paint;

    .line 21
    new-instance p1, Landroid/graphics/RectF;

    invoke-direct {p1}, Landroid/graphics/RectF;-><init>()V

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringBounds:Landroid/graphics/RectF;

    .line 27
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringPaint:Landroid/graphics/Paint;

    sget-object v0, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 28
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringPaint:Landroid/graphics/Paint;

    sget-object v0, Landroid/graphics/Paint$Cap;->ROUND:Landroid/graphics/Paint$Cap;

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setStrokeCap(Landroid/graphics/Paint$Cap;)V

    .line 29
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringPaint:Landroid/graphics/Paint;

    const/high16 v0, 0x40400000    # 3.0f

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 30
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->textPaint:Landroid/graphics/Paint;

    const/4 v0, -0x1

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setColor(I)V

    .line 31
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->textPaint:Landroid/graphics/Paint;

    const/high16 v0, 0x41a00000    # 20.0f

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setTextSize(F)V

    .line 32
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->textPaint:Landroid/graphics/Paint;

    sget-object v0, Landroid/graphics/Typeface;->DEFAULT_BOLD:Landroid/graphics/Typeface;

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setTypeface(Landroid/graphics/Typeface;)Landroid/graphics/Typeface;

    .line 33
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->textPaint:Landroid/graphics/Paint;

    sget-object v0, Landroid/graphics/Paint$Align;->LEFT:Landroid/graphics/Paint$Align;

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setTextAlign(Landroid/graphics/Paint$Align;)V

    .line 34
    const/4 p1, 0x0

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->setWillNotDraw(Z)V

    .line 35
    const/16 p1, 0x8

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->setVisibility(I)V

    .line 36
    return-void
.end method

.method private static clamp01(F)F
    .registers 2

    .line 72
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
    .registers 12

    .line 52
    invoke-super {p0, p1}, Landroid/view/View;->onDraw(Landroid/graphics/Canvas;)V

    .line 53
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->getHeight()I

    move-result v0

    int-to-float v0, v0

    const/high16 v1, 0x3f000000    # 0.5f

    mul-float v0, v0, v1

    .line 54
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringBounds:Landroid/graphics/RectF;

    const/high16 v3, 0x41a80000    # 21.0f

    sub-float v4, v0, v3

    const/high16 v5, 0x423c0000    # 47.0f

    add-float/2addr v3, v0

    const/high16 v6, 0x40a00000    # 5.0f

    invoke-virtual {v2, v6, v4, v5, v3}, Landroid/graphics/RectF;->set(FFFF)V

    .line 57
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringPaint:Landroid/graphics/Paint;

    const/16 v3, 0x46

    const/16 v4, 0xff

    invoke-static {v3, v4, v4, v4}, Landroid/graphics/Color;->argb(IIII)I

    move-result v3

    invoke-virtual {v2, v3}, Landroid/graphics/Paint;->setColor(I)V

    .line 58
    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringBounds:Landroid/graphics/RectF;

    const/4 v8, 0x0

    iget-object v9, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringPaint:Landroid/graphics/Paint;

    const/high16 v6, -0x3d4c0000    # -90.0f

    const/high16 v7, 0x43b40000    # 360.0f

    move-object v4, p1

    invoke-virtual/range {v4 .. v9}, Landroid/graphics/Canvas;->drawArc(Landroid/graphics/RectF;FFZLandroid/graphics/Paint;)V

    .line 59
    iget v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->progress:F

    const/4 v3, 0x0

    cmpl-float v2, v2, v3

    if-lez v2, :cond_54

    .line 60
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringPaint:Landroid/graphics/Paint;

    const v3, -0xc60090

    invoke-virtual {v2, v3}, Landroid/graphics/Paint;->setColor(I)V

    .line 61
    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringBounds:Landroid/graphics/RectF;

    const/high16 v2, 0x43b40000    # 360.0f

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->progress:F

    mul-float v7, v3, v2

    const/4 v8, 0x0

    iget-object v9, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->ringPaint:Landroid/graphics/Paint;

    const/high16 v6, -0x3d4c0000    # -90.0f

    move-object v4, p1

    invoke-virtual/range {v4 .. v9}, Landroid/graphics/Canvas;->drawArc(Landroid/graphics/RectF;FFZLandroid/graphics/Paint;)V

    .line 64
    :cond_54
    return-void
.end method

.method public updatePayload(Lorg/json/JSONObject;)V
    .registers 9

    .line 39
    const/4 v0, 0x0

    if-eqz p1, :cond_d

    const-string v1, "autoHoldActive"

    invoke-virtual {p1, v1, v0}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v1

    if-eqz v1, :cond_d

    const/4 v1, 0x1

    goto :goto_e

    :cond_d
    const/4 v1, 0x0

    .line 40
    :goto_e
    const-wide/16 v2, 0x0

    const/4 v4, 0x0

    if-nez p1, :cond_15

    const/4 v5, 0x0

    goto :goto_20

    .line 41
    :cond_15
    const-string v5, "autoHoldElapsedSec"

    invoke-virtual {p1, v5, v2, v3}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v5

    double-to-float v5, v5

    .line 40
    invoke-static {v4, v5}, Ljava/lang/Math;->max(FF)F

    move-result v5

    :goto_20
    iput v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->elapsedSeconds:F

    .line 42
    if-nez p1, :cond_25

    goto :goto_30

    .line 43
    :cond_25
    const-string v4, "autoHoldEpbProgress"

    invoke-virtual {p1, v4, v2, v3}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v2

    double-to-float p1, v2

    .line 42
    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->clamp01(F)F

    move-result v4

    :goto_30
    iput v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->progress:F

    .line 44
    if-eqz v1, :cond_35

    goto :goto_37

    :cond_35
    const/16 v0, 0x8

    :goto_37
    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->setVisibility(I)V

    .line 45
    if-eqz v1, :cond_3f

    .line 46
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotAutoHoldView;->invalidate()V

    .line 48
    :cond_3f
    return-void
.end method
