.class public final Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;
.super Landroid/view/View;
.source "OpenpilotSectionCameraView.java"


# static fields
.field private static final BLACK:I

.field private static final GREEN:I

.field private static final RED:I

.field private static final TRACK:I

.field private static final WHITE:I = -0x1

.field private static final YELLOW:I


# instance fields
.field private adjusting:Z

.field private averageKph:D

.field private limitKph:I

.field private final paint:Landroid/graphics/Paint;

.field private progress:D

.field private remainingM:D


# direct methods
.method static constructor <clinit>()V
    .registers 4

    .line 14
    const/16 v0, 0x11

    invoke-static {v0, v0, v0}, Landroid/graphics/Color;->rgb(III)I

    move-result v0

    sput v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->BLACK:I

    .line 15
    const/16 v0, 0x3d

    const/16 v1, 0x36

    const/16 v2, 0xe5

    invoke-static {v2, v0, v1}, Landroid/graphics/Color;->rgb(III)I

    move-result v0

    sput v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->RED:I

    .line 16
    const/16 v0, 0xbf

    const/16 v1, 0x2f

    const/16 v2, 0xff

    invoke-static {v2, v0, v1}, Landroid/graphics/Color;->rgb(III)I

    move-result v0

    sput v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->YELLOW:I

    .line 17
    const/16 v0, 0xd0

    const/16 v1, 0x6f

    const/16 v3, 0x35

    invoke-static {v3, v0, v1}, Landroid/graphics/Color;->rgb(III)I

    move-result v0

    sput v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->GREEN:I

    .line 18
    const/16 v0, 0x48

    invoke-static {v0, v2, v2, v2}, Landroid/graphics/Color;->argb(IIII)I

    move-result v0

    sput v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->TRACK:I

    return-void
.end method

.method public constructor <init>(Landroid/content/Context;)V
    .registers 4

    .line 28
    invoke-direct {p0, p1}, Landroid/view/View;-><init>(Landroid/content/Context;)V

    .line 20
    new-instance p1, Landroid/graphics/Paint;

    const/4 v0, 0x1

    invoke-direct {p1, v0}, Landroid/graphics/Paint;-><init>(I)V

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    .line 29
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    const-string v1, "sans"

    invoke-static {v1, v0}, Landroid/graphics/Typeface;->create(Ljava/lang/String;I)Landroid/graphics/Typeface;

    move-result-object v0

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setTypeface(Landroid/graphics/Typeface;)Landroid/graphics/Typeface;

    .line 30
    const/16 p1, 0x8

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->setVisibility(I)V

    .line 31
    return-void
.end method

.method private static clamp(D)D
    .registers 4

    .line 75
    const-wide/high16 v0, 0x3ff0000000000000L    # 1.0

    invoke-static {v0, v1, p0, p1}, Ljava/lang/Math;->min(DD)D

    move-result-wide p0

    const-wide/16 v0, 0x0

    invoke-static {v0, v1, p0, p1}, Ljava/lang/Math;->max(DD)D

    move-result-wide p0

    return-wide p0
.end method

.method private drawCentered(Landroid/graphics/Canvas;Ljava/lang/String;FF)V
    .registers 7

    .line 86
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    sget-object v1, Landroid/graphics/Paint$Align;->CENTER:Landroid/graphics/Paint$Align;

    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setTextAlign(Landroid/graphics/Paint$Align;)V

    .line 87
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    invoke-virtual {p1, p2, p3, p4, v0}, Landroid/graphics/Canvas;->drawText(Ljava/lang/String;FFLandroid/graphics/Paint;)V

    .line 88
    return-void
.end method

.method private static formatDistance(D)Ljava/lang/String;
    .registers 7

    .line 79
    const/4 v0, 0x0

    const/4 v1, 0x1

    const-wide v2, 0x408f400000000000L    # 1000.0

    cmpl-double v4, p0, v2

    if-ltz v4, :cond_1d

    .line 80
    sget-object v4, Ljava/util/Locale;->US:Ljava/util/Locale;

    div-double/2addr p0, v2

    invoke-static {p0, p1}, Ljava/lang/Double;->valueOf(D)Ljava/lang/Double;

    move-result-object p0

    new-array p1, v1, [Ljava/lang/Object;

    aput-object p0, p1, v0

    const-string p0, "%.1fkm"

    invoke-static {v4, p0, p1}, Ljava/lang/String;->format(Ljava/util/Locale;Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;

    move-result-object p0

    return-object p0

    .line 82
    :cond_1d
    const-wide/16 v2, 0x0

    cmpl-double v4, p0, v2

    if-lez v4, :cond_34

    sget-object v2, Ljava/util/Locale;->US:Ljava/util/Locale;

    invoke-static {p0, p1}, Ljava/lang/Double;->valueOf(D)Ljava/lang/Double;

    move-result-object p0

    new-array p1, v1, [Ljava/lang/Object;

    aput-object p0, p1, v0

    const-string p0, "%.0fm"

    invoke-static {v2, p0, p1}, Ljava/lang/String;->format(Ljava/util/Locale;Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;

    move-result-object p0

    goto :goto_36

    :cond_34
    const-string p0, "--"

    :goto_36
    return-object p0
.end method


# virtual methods
.method protected onDraw(Landroid/graphics/Canvas;)V
    .registers 18

    .line 92
    move-object/from16 v0, p0

    move-object/from16 v1, p1

    invoke-super/range {p0 .. p1}, Landroid/view/View;->onDraw(Landroid/graphics/Canvas;)V

    .line 93
    invoke-virtual/range {p0 .. p0}, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->getWidth()I

    move-result v2

    int-to-float v2, v2

    const/high16 v3, 0x3f000000    # 0.5f

    mul-float v2, v2, v3

    .line 95
    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    sget-object v5, Landroid/graphics/Paint$Style;->FILL:Landroid/graphics/Paint$Style;

    invoke-virtual {v4, v5}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 96
    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    sget v5, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->YELLOW:I

    invoke-virtual {v4, v5}, Landroid/graphics/Paint;->setColor(I)V

    .line 97
    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    const/high16 v5, 0x41300000    # 11.0f

    invoke-virtual {v4, v5}, Landroid/graphics/Paint;->setTextSize(F)V

    .line 98
    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    const/4 v5, 0x1

    invoke-virtual {v4, v5}, Landroid/graphics/Paint;->setFakeBoldText(Z)V

    .line 99
    const-string v4, "\uad6c\uac04\ub2e8\uc18d"

    const/high16 v6, 0x41400000    # 12.0f

    invoke-direct {v0, v1, v4, v2, v6}, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->drawCentered(Landroid/graphics/Canvas;Ljava/lang/String;FF)V

    .line 101
    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    const/4 v7, -0x1

    invoke-virtual {v4, v7}, Landroid/graphics/Paint;->setColor(I)V

    .line 102
    const/high16 v4, 0x41e80000    # 29.0f

    iget-object v8, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    const/high16 v9, 0x423c0000    # 47.0f

    invoke-virtual {v1, v2, v9, v4, v8}, Landroid/graphics/Canvas;->drawCircle(FFFLandroid/graphics/Paint;)V

    .line 103
    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    sget-object v8, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v4, v8}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 104
    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    const/high16 v8, 0x40a00000    # 5.0f

    invoke-virtual {v4, v8}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 105
    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    sget v8, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->RED:I

    invoke-virtual {v4, v8}, Landroid/graphics/Paint;->setColor(I)V

    .line 106
    const/high16 v4, 0x41d80000    # 27.0f

    iget-object v8, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    invoke-virtual {v1, v2, v9, v4, v8}, Landroid/graphics/Canvas;->drawCircle(FFFLandroid/graphics/Paint;)V

    .line 108
    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    sget-object v8, Landroid/graphics/Paint$Style;->FILL:Landroid/graphics/Paint$Style;

    invoke-virtual {v4, v8}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 109
    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    sget v8, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->BLACK:I

    invoke-virtual {v4, v8}, Landroid/graphics/Paint;->setColor(I)V

    .line 110
    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    iget v8, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->limitKph:I

    const/16 v10, 0x64

    if-lt v8, v10, :cond_76

    const/high16 v8, 0x41d00000    # 26.0f

    goto :goto_78

    :cond_76
    const/high16 v8, 0x41f00000    # 30.0f

    :goto_78
    invoke-virtual {v4, v8}, Landroid/graphics/Paint;->setTextSize(F)V

    .line 111
    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    invoke-virtual {v4, v5}, Landroid/graphics/Paint;->setFakeBoldText(Z)V

    .line 112
    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    invoke-virtual {v4}, Landroid/graphics/Paint;->getFontMetrics()Landroid/graphics/Paint$FontMetrics;

    move-result-object v4

    .line 113
    iget v8, v4, Landroid/graphics/Paint$FontMetrics;->ascent:F

    iget v4, v4, Landroid/graphics/Paint$FontMetrics;->descent:F

    add-float/2addr v8, v4

    mul-float v8, v8, v3

    sub-float/2addr v9, v8

    .line 114
    iget v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->limitKph:I

    invoke-static {v3}, Ljava/lang/Integer;->toString(I)Ljava/lang/String;

    move-result-object v3

    invoke-direct {v0, v1, v3, v2, v9}, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->drawCentered(Landroid/graphics/Canvas;Ljava/lang/String;FF)V

    .line 116
    iget-object v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    const/high16 v4, 0x41200000    # 10.0f

    invoke-virtual {v3, v4}, Landroid/graphics/Paint;->setTextSize(F)V

    .line 117
    iget-object v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    invoke-virtual {v3, v5}, Landroid/graphics/Paint;->setFakeBoldText(Z)V

    .line 118
    iget-object v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    iget-wide v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->averageKph:D

    iget v8, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->limitKph:I

    int-to-double v8, v8

    const/16 v10, 0x4d

    const/16 v11, 0x52

    const-wide/high16 v12, 0x4008000000000000L    # 3.0

    const/16 v14, 0xff

    cmpl-double v15, v4, v8

    if-lez v15, :cond_bb

    invoke-static {v14, v11, v10}, Landroid/graphics/Color;->rgb(III)I

    move-result v7

    goto :goto_c7

    .line 119
    :cond_bb
    iget-wide v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->averageKph:D

    iget v8, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->limitKph:I

    int-to-double v8, v8

    sub-double/2addr v8, v12

    cmpl-double v15, v4, v8

    if-ltz v15, :cond_c7

    sget v7, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->YELLOW:I

    .line 118
    :cond_c7
    :goto_c7
    invoke-virtual {v3, v7}, Landroid/graphics/Paint;->setColor(I)V

    .line 120
    iget-wide v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->averageKph:D

    const-wide/16 v7, 0x0

    cmpl-double v5, v3, v7

    if-lez v5, :cond_ec

    new-instance v3, Ljava/lang/StringBuilder;

    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V

    const-string v4, "\ud3c9\uade0 "

    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    iget-wide v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->averageKph:D

    invoke-static {v4, v5}, Ljava/lang/Math;->round(D)J

    move-result-wide v4

    invoke-virtual {v3, v4, v5}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    move-result-object v3

    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v3

    goto :goto_ee

    :cond_ec
    const-string v3, "\ud3c9\uade0 --"

    .line 121
    :goto_ee
    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    sget-object v5, Landroid/graphics/Paint$Align;->RIGHT:Landroid/graphics/Paint$Align;

    invoke-virtual {v4, v5}, Landroid/graphics/Paint;->setTextAlign(Landroid/graphics/Paint$Align;)V

    .line 122
    const/high16 v4, 0x40400000    # 3.0f

    sub-float v5, v2, v4

    iget-object v7, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    const/high16 v8, 0x42ac0000    # 86.0f

    invoke-virtual {v1, v3, v5, v8, v7}, Landroid/graphics/Canvas;->drawText(Ljava/lang/String;FFLandroid/graphics/Paint;)V

    .line 124
    iget-object v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    const/16 v5, 0xdc

    invoke-static {v5, v14, v14, v14}, Landroid/graphics/Color;->argb(IIII)I

    move-result v5

    invoke-virtual {v3, v5}, Landroid/graphics/Paint;->setColor(I)V

    .line 125
    iget-object v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    sget-object v5, Landroid/graphics/Paint$Align;->LEFT:Landroid/graphics/Paint$Align;

    invoke-virtual {v3, v5}, Landroid/graphics/Paint;->setTextAlign(Landroid/graphics/Paint$Align;)V

    .line 126
    iget-wide v12, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->remainingM:D

    invoke-static {v12, v13}, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->formatDistance(D)Ljava/lang/String;

    move-result-object v3

    add-float/2addr v2, v4

    iget-object v4, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    invoke-virtual {v1, v3, v2, v8, v4}, Landroid/graphics/Canvas;->drawText(Ljava/lang/String;FFLandroid/graphics/Paint;)V

    .line 128
    new-instance v2, Landroid/graphics/RectF;

    invoke-virtual/range {p0 .. p0}, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->getWidth()I

    move-result v3

    int-to-float v3, v3

    sub-float/2addr v3, v6

    const/high16 v4, 0x42c00000    # 96.0f

    const/high16 v5, 0x42c80000    # 100.0f

    invoke-direct {v2, v6, v4, v3, v5}, Landroid/graphics/RectF;-><init>(FFFF)V

    .line 129
    iget-object v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    sget v7, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->TRACK:I

    invoke-virtual {v3, v7}, Landroid/graphics/Paint;->setColor(I)V

    .line 130
    iget-object v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    const/high16 v7, 0x40000000    # 2.0f

    invoke-virtual {v1, v2, v7, v7, v3}, Landroid/graphics/Canvas;->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V

    .line 131
    iget-wide v2, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->averageKph:D

    iget v8, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->limitKph:I

    int-to-double v8, v8

    cmpl-double v12, v2, v8

    if-lez v12, :cond_149

    invoke-static {v14, v11, v10}, Landroid/graphics/Color;->rgb(III)I

    move-result v2

    goto :goto_15a

    .line 132
    :cond_149
    iget-wide v2, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->averageKph:D

    iget v8, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->limitKph:I

    int-to-double v8, v8

    const-wide/high16 v10, 0x4008000000000000L    # 3.0

    sub-double/2addr v8, v10

    cmpl-double v10, v2, v8

    if-ltz v10, :cond_158

    sget v2, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->YELLOW:I

    goto :goto_15a

    :cond_158
    sget v2, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->GREEN:I

    .line 133
    :goto_15a
    nop

    .line 134
    iget-boolean v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->adjusting:Z

    if-eqz v3, :cond_185

    .line 135
    invoke-static {}, Landroid/os/SystemClock;->uptimeMillis()J

    move-result-wide v8

    long-to-double v8, v8

    const-wide v10, 0x4066800000000000L    # 180.0

    div-double/2addr v8, v10

    invoke-static {v8, v9}, Ljava/lang/Math;->sin(D)D

    move-result-wide v8

    const-wide/high16 v10, 0x3ff0000000000000L    # 1.0

    add-double/2addr v8, v10

    const-wide/high16 v10, 0x3fe0000000000000L    # 0.5

    mul-double v8, v8, v10

    .line 136
    const-wide v10, 0x4062c00000000000L    # 150.0

    mul-double v8, v8, v10

    double-to-int v3, v8

    add-int/lit8 v3, v3, 0x69

    .line 137
    const-wide/16 v8, 0x50

    invoke-virtual {v0, v8, v9}, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->postInvalidateDelayed(J)V

    goto :goto_187

    .line 134
    :cond_185
    const/16 v3, 0xff

    .line 139
    :goto_187
    iget-object v8, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    invoke-virtual {v8, v2}, Landroid/graphics/Paint;->setColor(I)V

    .line 140
    iget-object v2, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    invoke-virtual {v2, v3}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 141
    new-instance v2, Landroid/graphics/RectF;

    .line 142
    invoke-virtual/range {p0 .. p0}, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->getWidth()I

    move-result v3

    int-to-float v3, v3

    const/high16 v8, 0x41c00000    # 24.0f

    sub-float/2addr v3, v8

    iget-wide v8, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->progress:D

    double-to-float v8, v8

    mul-float v3, v3, v8

    add-float/2addr v3, v6

    invoke-direct {v2, v6, v4, v3, v5}, Landroid/graphics/RectF;-><init>(FFFF)V

    .line 143
    iget-object v3, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    invoke-virtual {v1, v2, v7, v7, v3}, Landroid/graphics/Canvas;->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V

    .line 144
    iget-object v1, v0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->paint:Landroid/graphics/Paint;

    invoke-virtual {v1, v14}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 145
    return-void
.end method

.method public updatePayload(Ljava/lang/String;IZ)V
    .registers 5

    .line 35
    :try_start_0
    new-instance v0, Lorg/json/JSONObject;

    invoke-direct {v0, p1}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    invoke-virtual {p0, v0, p2, p3}, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->updatePayload(Lorg/json/JSONObject;IZ)V
    :try_end_8
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_8} :catch_9

    .line 38
    goto :goto_11

    .line 36
    :catch_9
    move-exception p1

    .line 37
    const/4 p1, 0x0

    move-object v0, p1

    check-cast v0, Lorg/json/JSONObject;

    invoke-virtual {p0, p1, p2, p3}, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->updatePayload(Lorg/json/JSONObject;IZ)V

    .line 39
    :goto_11
    return-void
.end method

.method public updatePayload(Lorg/json/JSONObject;IZ)V
    .registers 11

    .line 42
    const/4 v0, 0x1

    const/4 v1, 0x0

    if-eqz p3, :cond_8

    if-lez p2, :cond_8

    const/4 p3, 0x1

    goto :goto_9

    :cond_8
    const/4 p3, 0x0

    .line 43
    :goto_9
    if-nez p3, :cond_13

    .line 44
    const/16 p1, 0x8

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->setVisibility(I)V

    .line 45
    iput-boolean v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->adjusting:Z

    .line 46
    return-void

    .line 49
    :cond_13
    iput p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->limitKph:I

    .line 51
    const-wide/16 v2, 0x0

    if-eqz p1, :cond_71

    .line 54
    :try_start_19
    const-string p3, "sectionLimitKph"

    int-to-double v4, p2

    invoke-virtual {p1, p3, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide p2

    .line 55
    const-wide/high16 v4, 0x4034000000000000L    # 20.0

    cmpl-double v6, p2, v4

    if-ltz v6, :cond_36

    const-wide v4, 0x4061800000000000L    # 140.0

    cmpg-double v6, p2, v4

    if-gtz v6, :cond_36

    .line 56
    invoke-static {p2, p3}, Ljava/lang/Math;->round(D)J

    move-result-wide p2

    long-to-int p3, p2

    iput p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->limitKph:I

    .line 58
    :cond_36
    const-string p2, "sectionAverageKph"

    invoke-virtual {p1, p2, v2, v3}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide p2

    invoke-static {v2, v3, p2, p3}, Ljava/lang/Math;->max(DD)D

    move-result-wide p2

    iput-wide p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->averageKph:D

    .line 59
    const-string p2, "sectionProgress"

    invoke-virtual {p1, p2, v2, v3}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide p2

    invoke-static {p2, p3}, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->clamp(D)D

    move-result-wide p2

    iput-wide p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->progress:D

    .line 60
    const-string p2, "sectionRemainingM"

    invoke-virtual {p1, p2, v2, v3}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide p2

    invoke-static {v2, v3, p2, p3}, Ljava/lang/Math;->max(DD)D

    move-result-wide p2

    iput-wide p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->remainingM:D

    .line 61
    const-string p2, "automaticAccActive"

    invoke-virtual {p1, p2, v1}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result p2

    if-eqz p2, :cond_6b

    const-string p2, "automaticAccAtTarget"

    .line 62
    invoke-virtual {p1, p2, v1}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result p1

    if-nez p1, :cond_6b

    goto :goto_6c

    :cond_6b
    const/4 v0, 0x0

    :goto_6c
    iput-boolean v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->adjusting:Z

    .line 68
    goto :goto_81

    .line 63
    :catch_6f
    move-exception p1

    goto :goto_79

    .line 52
    :cond_71
    new-instance p1, Ljava/lang/IllegalArgumentException;

    const-string p2, "missing section payload"

    invoke-direct {p1, p2}, Ljava/lang/IllegalArgumentException;-><init>(Ljava/lang/String;)V

    throw p1
    :try_end_79
    .catch Ljava/lang/Exception; {:try_start_19 .. :try_end_79} :catch_6f

    .line 64
    :goto_79
    iput-wide v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->averageKph:D

    .line 65
    iput-wide v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->progress:D

    .line 66
    iput-wide v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->remainingM:D

    .line 67
    iput-boolean v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->adjusting:Z

    .line 70
    :goto_81
    invoke-virtual {p0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->setVisibility(I)V

    .line 71
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotSectionCameraView;->invalidate()V

    .line 72
    return-void
.end method
