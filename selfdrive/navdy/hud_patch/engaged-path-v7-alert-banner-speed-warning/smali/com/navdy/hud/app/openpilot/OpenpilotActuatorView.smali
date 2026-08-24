.class public final Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;
.super Landroid/view/View;
.source "OpenpilotActuatorView.java"


# static fields
.field private static final ACTUATOR_ACCELERATOR:I = 0x1

.field private static final ACTUATOR_BRAKE:I = 0x2

.field private static final ACTUATOR_NONE:I = 0x0

.field private static final COLOR_ACCELERATOR:I = -0xd07301

.field private static final COLOR_BRAKE:I = -0xc4d0

.field private static final INDICATOR_RADIUS_PX:F = 16.0f

.field private static final MAX_ICON_SIZE_PX:F = 18.0f


# instance fields
.field private final acceleratorBitmap:Landroid/graphics/Bitmap;

.field private actuator:I

.field private final bitmapPaint:Landroid/graphics/Paint;

.field private final brakeBitmap:Landroid/graphics/Bitmap;

.field private final destination:Landroid/graphics/RectF;

.field private final fillPaint:Landroid/graphics/Paint;

.field private final iconFilter:Landroid/graphics/PorterDuffColorFilter;

.field private level:F


# direct methods
.method public constructor <init>(Landroid/content/Context;)V
    .registers 5

    .line 35
    invoke-direct {p0, p1}, Landroid/view/View;-><init>(Landroid/content/Context;)V

    .line 26
    new-instance v0, Landroid/graphics/Paint;

    const/4 v1, 0x3

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->bitmapPaint:Landroid/graphics/Paint;

    .line 27
    new-instance v0, Landroid/graphics/Paint;

    const/4 v1, 0x1

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->fillPaint:Landroid/graphics/Paint;

    .line 28
    new-instance v0, Landroid/graphics/RectF;

    invoke-direct {v0}, Landroid/graphics/RectF;-><init>()V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->destination:Landroid/graphics/RectF;

    .line 29
    new-instance v0, Landroid/graphics/PorterDuffColorFilter;

    const/4 v1, -0x1

    sget-object v2, Landroid/graphics/PorterDuff$Mode;->SRC_IN:Landroid/graphics/PorterDuff$Mode;

    invoke-direct {v0, v1, v2}, Landroid/graphics/PorterDuffColorFilter;-><init>(ILandroid/graphics/PorterDuff$Mode;)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->iconFilter:Landroid/graphics/PorterDuffColorFilter;

    .line 36
    const-string v0, "navdy_accelerator_pedal"

    invoke-direct {p0, p1, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->loadBitmap(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v0

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->acceleratorBitmap:Landroid/graphics/Bitmap;

    .line 37
    const-string v0, "navdy_brake_pedal"

    invoke-direct {p0, p1, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->loadBitmap(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object p1

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->brakeBitmap:Landroid/graphics/Bitmap;

    .line 38
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->fillPaint:Landroid/graphics/Paint;

    sget-object v0, Landroid/graphics/Paint$Style;->FILL:Landroid/graphics/Paint$Style;

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 39
    const/4 p1, 0x0

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->setWillNotDraw(Z)V

    .line 40
    const/16 p1, 0x8

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->setVisibility(I)V

    .line 41
    return-void
.end method

.method private static clamp01(F)F
    .registers 2

    .line 114
    const/high16 v0, 0x3f800000    # 1.0f

    invoke-static {v0, p0}, Ljava/lang/Math;->min(FF)F

    move-result p0

    const/4 v0, 0x0

    invoke-static {v0, p0}, Ljava/lang/Math;->max(FF)F

    move-result p0

    return p0
.end method

.method private drawIcon(Landroid/graphics/Canvas;Landroid/graphics/Bitmap;FFZ)V
    .registers 10

    .line 96
    if-eqz p2, :cond_5b

    invoke-virtual {p2}, Landroid/graphics/Bitmap;->getWidth()I

    move-result v0

    if-lez v0, :cond_5b

    invoke-virtual {p2}, Landroid/graphics/Bitmap;->getHeight()I

    move-result v0

    if-gtz v0, :cond_f

    goto :goto_5b

    .line 100
    :cond_f
    invoke-virtual {p2}, Landroid/graphics/Bitmap;->getWidth()I

    move-result v0

    int-to-float v0, v0

    const/high16 v1, 0x41900000    # 18.0f

    div-float v0, v1, v0

    .line 101
    invoke-virtual {p2}, Landroid/graphics/Bitmap;->getHeight()I

    move-result v2

    int-to-float v2, v2

    div-float/2addr v1, v2

    .line 100
    invoke-static {v0, v1}, Ljava/lang/Math;->min(FF)F

    move-result v0

    .line 102
    invoke-virtual {p2}, Landroid/graphics/Bitmap;->getWidth()I

    move-result v1

    int-to-float v1, v1

    mul-float v1, v1, v0

    .line 103
    invoke-virtual {p2}, Landroid/graphics/Bitmap;->getHeight()I

    move-result v2

    int-to-float v2, v2

    mul-float v2, v2, v0

    .line 104
    const/high16 v0, 0x3f000000    # 0.5f

    mul-float v3, v1, v0

    sub-float/2addr p3, v3

    .line 105
    mul-float v0, v0, v2

    sub-float/2addr p4, v0

    .line 106
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->destination:Landroid/graphics/RectF;

    add-float/2addr v1, p3

    add-float/2addr v2, p4

    invoke-virtual {v0, p3, p4, v1, v2}, Landroid/graphics/RectF;->set(FFFF)V

    .line 108
    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->bitmapPaint:Landroid/graphics/Paint;

    iget-object p4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->iconFilter:Landroid/graphics/PorterDuffColorFilter;

    invoke-virtual {p3, p4}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 109
    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->bitmapPaint:Landroid/graphics/Paint;

    if-eqz p5, :cond_4d

    const/16 p4, 0xff

    goto :goto_4f

    :cond_4d
    const/16 p4, 0xb4

    :goto_4f
    invoke-virtual {p3, p4}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 110
    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->destination:Landroid/graphics/RectF;

    iget-object p4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->bitmapPaint:Landroid/graphics/Paint;

    const/4 p5, 0x0

    invoke-virtual {p1, p2, p5, p3, p4}, Landroid/graphics/Canvas;->drawBitmap(Landroid/graphics/Bitmap;Landroid/graphics/Rect;Landroid/graphics/RectF;Landroid/graphics/Paint;)V

    .line 111
    return-void

    .line 97
    :cond_5b
    :goto_5b
    return-void
.end method

.method private drawIndicator(Landroid/graphics/Canvas;FFZI)V
    .registers 7

    .line 85
    if-nez p4, :cond_3

    .line 86
    return-void

    .line 89
    :cond_3
    iget-object p4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->fillPaint:Landroid/graphics/Paint;

    invoke-virtual {p4, p5}, Landroid/graphics/Paint;->setColor(I)V

    .line 90
    iget-object p4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->fillPaint:Landroid/graphics/Paint;

    iget p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->level:F

    const/high16 v0, 0x425c0000    # 55.0f

    mul-float p5, p5, v0

    invoke-static {p5}, Ljava/lang/Math;->round(F)I

    move-result p5

    add-int/lit16 p5, p5, 0xaf

    invoke-virtual {p4, p5}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 91
    const/high16 p4, 0x41800000    # 16.0f

    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->fillPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p2, p3, p4, p5}, Landroid/graphics/Canvas;->drawCircle(FFFLandroid/graphics/Paint;)V

    .line 92
    return-void
.end method

.method private loadBitmap(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;
    .registers 5

    .line 44
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->getResources()Landroid/content/res/Resources;

    move-result-object v0

    const-string v1, "drawable"

    invoke-virtual {p1}, Landroid/content/Context;->getPackageName()Ljava/lang/String;

    move-result-object p1

    invoke-virtual {v0, p2, v1, p1}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I

    move-result p1

    .line 45
    if-nez p1, :cond_12

    const/4 p1, 0x0

    goto :goto_1a

    :cond_12
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->getResources()Landroid/content/res/Resources;

    move-result-object p2

    invoke-static {p2, p1}, Landroid/graphics/BitmapFactory;->decodeResource(Landroid/content/res/Resources;I)Landroid/graphics/Bitmap;

    move-result-object p1

    :goto_1a
    return-object p1
.end method


# virtual methods
.method protected onDraw(Landroid/graphics/Canvas;)V
    .registers 13

    .line 69
    invoke-super {p0, p1}, Landroid/view/View;->onDraw(Landroid/graphics/Canvas;)V

    .line 70
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->getHeight()I

    move-result v0

    int-to-float v0, v0

    const/high16 v1, 0x3f000000    # 0.5f

    mul-float v5, v0, v1

    .line 71
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->getWidth()I

    move-result v0

    int-to-float v0, v0

    const/high16 v1, 0x3e800000    # 0.25f

    mul-float v4, v0, v1

    .line 72
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->getWidth()I

    move-result v0

    int-to-float v0, v0

    const/high16 v1, 0x3f400000    # 0.75f

    mul-float v0, v0, v1

    .line 73
    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->actuator:I

    const/4 v8, 0x0

    const/4 v9, 0x1

    if-ne v1, v9, :cond_26

    const/4 v6, 0x1

    goto :goto_27

    :cond_26
    const/4 v6, 0x0

    :goto_27
    const v7, -0xd07301

    move-object v2, p0

    move-object v3, p1

    invoke-direct/range {v2 .. v7}, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->drawIndicator(Landroid/graphics/Canvas;FFZI)V

    .line 75
    move p1, v4

    iget v1, v2, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->actuator:I

    const/4 v10, 0x2

    if-ne v1, v10, :cond_37

    const/4 v6, 0x1

    goto :goto_38

    :cond_37
    const/4 v6, 0x0

    :goto_38
    const v7, -0xc4d0

    move v4, v0

    invoke-direct/range {v2 .. v7}, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->drawIndicator(Landroid/graphics/Canvas;FFZI)V

    .line 77
    iget-object v4, v2, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->acceleratorBitmap:Landroid/graphics/Bitmap;

    iget v1, v2, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->actuator:I

    if-ne v1, v9, :cond_47

    const/4 v7, 0x1

    goto :goto_48

    :cond_47
    const/4 v7, 0x0

    :goto_48
    move v6, v5

    move v5, p1

    invoke-direct/range {v2 .. v7}, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->drawIcon(Landroid/graphics/Canvas;Landroid/graphics/Bitmap;FFZ)V

    .line 79
    move v5, v6

    iget-object v4, v2, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->brakeBitmap:Landroid/graphics/Bitmap;

    iget p1, v2, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->actuator:I

    if-ne p1, v10, :cond_56

    const/4 v7, 0x1

    goto :goto_57

    :cond_56
    const/4 v7, 0x0

    :goto_57
    move v6, v5

    move v5, v0

    invoke-direct/range {v2 .. v7}, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->drawIcon(Landroid/graphics/Canvas;Landroid/graphics/Bitmap;FFZ)V

    .line 81
    return-void
.end method

.method public updatePayload(Lorg/json/JSONObject;Z)V
    .registers 7

    .line 49
    const/4 v0, 0x0

    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->actuator:I

    .line 50
    const/4 v1, 0x0

    iput v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->level:F

    .line 51
    if-eqz p2, :cond_38

    if-eqz p1, :cond_38

    .line 52
    const-string v1, "longitudinalActuator"

    const-string v2, "none"

    invoke-virtual {p1, v1, v2}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v1

    .line 53
    const-string v2, "accelerator"

    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v2

    if-eqz v2, :cond_1e

    .line 54
    const/4 v1, 0x1

    iput v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->actuator:I

    goto :goto_29

    .line 55
    :cond_1e
    const-string v2, "brake"

    invoke-virtual {v2, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_29

    .line 56
    const/4 v1, 0x2

    iput v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->actuator:I

    .line 58
    :cond_29
    :goto_29
    const-string v1, "longitudinalActuatorLevel"

    const-wide/16 v2, 0x0

    invoke-virtual {p1, v1, v2, v3}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v1

    double-to-float p1, v1

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->level:F

    .line 61
    :cond_38
    if-eqz p2, :cond_3b

    goto :goto_3d

    :cond_3b
    const/16 v0, 0x8

    :goto_3d
    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->setVisibility(I)V

    .line 62
    if-eqz p2, :cond_45

    .line 63
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotActuatorView;->invalidate()V

    .line 65
    :cond_45
    return-void
.end method
