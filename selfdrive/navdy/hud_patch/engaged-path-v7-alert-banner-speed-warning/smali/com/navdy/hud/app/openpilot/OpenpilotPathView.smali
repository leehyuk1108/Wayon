.class public final Lcom/navdy/hud/app/openpilot/OpenpilotPathView;
.super Landroid/view/View;
.source "OpenpilotPathView.java"


# static fields
.field private static final COLOR_GREEN:I = -0xff19ba


# instance fields
.field private laneLeft:[F

.field private laneLeftProb:F

.field private final lanePaint:Landroid/graphics/Paint;

.field private laneRight:[F

.field private laneRightProb:F

.field private final pathEdgePaint:Landroid/graphics/Paint;

.field private final pathFillPaint:Landroid/graphics/Paint;

.field private pathLeft:[F

.field private pathRight:[F

.field private roadEdgeLeft:[F

.field private roadEdgeRight:[F


# direct methods
.method public constructor <init>(Landroid/content/Context;)V
    .locals 2

    .line 27
    invoke-direct {p0, p1}, Landroid/view/View;-><init>(Landroid/content/Context;)V

    .line 16
    new-instance p1, Landroid/graphics/Paint;

    const/4 v0, 0x1

    invoke-direct {p1, v0}, Landroid/graphics/Paint;-><init>(I)V

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    .line 17
    new-instance p1, Landroid/graphics/Paint;

    invoke-direct {p1, v0}, Landroid/graphics/Paint;-><init>(I)V

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    .line 18
    new-instance p1, Landroid/graphics/Paint;

    invoke-direct {p1, v0}, Landroid/graphics/Paint;-><init>(I)V

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    .line 19
    const/4 p1, 0x0

    new-array v0, p1, [F

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    .line 20
    new-array v0, p1, [F

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    new-array v0, p1, [F

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    new-array v0, p1, [F

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    .line 23
    new-array v0, p1, [F

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 24
    new-array v0, p1, [F

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    .line 28
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    sget-object v1, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 29
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    sget-object v1, Landroid/graphics/Paint$Cap;->ROUND:Landroid/graphics/Paint$Cap;

    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setStrokeCap(Landroid/graphics/Paint$Cap;)V

    .line 30
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    sget-object v1, Landroid/graphics/Paint$Join;->ROUND:Landroid/graphics/Paint$Join;

    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setStrokeJoin(Landroid/graphics/Paint$Join;)V

    .line 31
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    const/high16 v1, 0x40200000    # 2.5f

    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 32
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    const v1, -0xff19ba

    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setColor(I)V

    .line 33
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    sget-object v1, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 34
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    sget-object v1, Landroid/graphics/Paint$Join;->ROUND:Landroid/graphics/Paint$Join;

    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setStrokeJoin(Landroid/graphics/Paint$Join;)V

    .line 35
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    const v1, 0x3fe66666    # 1.8f

    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 36
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    sget-object v1, Landroid/graphics/Paint$Style;->FILL:Landroid/graphics/Paint$Style;

    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 37
    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setWillNotDraw(Z)V

    .line 38
    const/16 p1, 0x8

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setVisibility(I)V

    .line 39
    return-void
.end method

.method private static clamp01(F)F
    .locals 1

    .line 113
    const/high16 v0, 0x3f800000    # 1.0f

    invoke-static {v0, p0}, Ljava/lang/Math;->min(FF)F

    move-result p0

    const/4 v0, 0x0

    invoke-static {v0, p0}, Ljava/lang/Math;->max(FF)F

    move-result p0

    return p0
.end method

.method private clearGeometry()V
    .locals 2

    .line 104
    const/4 v0, 0x0

    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 105
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    .line 106
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    .line 107
    new-array v0, v0, [F

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    .line 108
    const/16 v0, 0x8

    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setVisibility(I)V

    .line 109
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->invalidate()V

    .line 110
    return-void
.end method

.method private static linePath([F)Landroid/graphics/Path;
    .locals 4

    .line 117
    new-instance v0, Landroid/graphics/Path;

    invoke-direct {v0}, Landroid/graphics/Path;-><init>()V

    .line 118
    const/4 v1, 0x0

    aget v1, p0, v1

    const/4 v2, 0x1

    aget v2, p0, v2

    invoke-virtual {v0, v1, v2}, Landroid/graphics/Path;->moveTo(FF)V

    .line 119
    const/4 v1, 0x2

    :goto_0
    array-length v2, p0

    if-ge v1, v2, :cond_0

    .line 120
    aget v2, p0, v1

    add-int/lit8 v3, v1, 0x1

    aget v3, p0, v3

    invoke-virtual {v0, v2, v3}, Landroid/graphics/Path;->lineTo(FF)V

    .line 119
    add-int/lit8 v1, v1, 0x2

    goto :goto_0

    .line 122
    :cond_0
    return-object v0
.end method

.method private static readPoints(Lorg/json/JSONArray;)[F
    .locals 4

    .line 126
    const/4 v0, 0x0

    if-eqz p0, :cond_2

    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    const/4 v2, 0x4

    if-lt v1, v2, :cond_2

    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    and-int/lit8 v1, v1, 0x1

    if-eqz v1, :cond_0

    goto :goto_1

    .line 129
    :cond_0
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    new-array v1, v1, [F

    .line 130
    nop

    :goto_0
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v2

    if-ge v0, v2, :cond_1

    .line 131
    const-wide/16 v2, 0x0

    invoke-virtual {p0, v0, v2, v3}, Lorg/json/JSONArray;->optDouble(ID)D

    move-result-wide v2

    double-to-float v2, v2

    aput v2, v1, v0

    .line 130
    add-int/lit8 v0, v0, 0x1

    goto :goto_0

    .line 133
    :cond_1
    return-object v1

    .line 127
    :cond_2
    :goto_1
    new-array p0, v0, [F

    return-object p0
.end method

.method private static validLine([F)Z
    .locals 2

    .line 137
    if-eqz p0, :cond_0

    array-length v0, p0

    const/4 v1, 0x4

    if-lt v0, v1, :cond_0

    array-length p0, p0

    const/4 v0, 0x1

    and-int/2addr p0, v0

    if-nez p0, :cond_0

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    :goto_0
    return v0
.end method


# virtual methods
.method protected onDraw(Landroid/graphics/Canvas;)V
    .locals 5

    .line 83
    invoke-super {p0, p1}, Landroid/view/View;->onDraw(Landroid/graphics/Canvas;)V

    .line 84
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_2

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-nez v0, :cond_0

    goto :goto_1

    .line 88
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    .line 89
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    array-length v1, v1

    add-int/lit8 v1, v1, -0x2

    :goto_0
    if-ltz v1, :cond_1

    .line 90
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    aget v2, v2, v1

    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    add-int/lit8 v4, v1, 0x1

    aget v3, v3, v4

    invoke-virtual {v0, v2, v3}, Landroid/graphics/Path;->lineTo(FF)V

    .line 89
    add-int/lit8 v1, v1, -0x2

    goto :goto_0

    .line 92
    :cond_1
    invoke-virtual {v0}, Landroid/graphics/Path;->close()V

    .line 93
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 94
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 95
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    const/16 v1, 0x46

    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setAlpha(I)V

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_navdy_road_edge_right

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    :cond_navdy_road_edge_right
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_navdy_road_edges_done

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    :cond_navdy_road_edges_done

    .line 97
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftProb:F

    const/high16 v2, 0x43480000    # 200.0f

    mul-float v1, v1, v2

    const/high16 v3, 0x425c0000    # 55.0f

    add-float/2addr v1, v3

    float-to-int v1, v1

    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 98
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 99
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightProb:F

    mul-float v1, v1, v2

    add-float/2addr v1, v3

    float-to-int v1, v1

    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 100
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 101
    return-void

    .line 85
    :cond_2
    :goto_1
    return-void
.end method

.method protected onSizeChanged(IIII)V
    .locals 9

    .line 74
    invoke-super {p0, p1, p2, p3, p4}, Landroid/view/View;->onSizeChanged(IIII)V

    .line 75
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    new-instance v0, Landroid/graphics/LinearGradient;

    int-to-float v4, p2

    const v6, -0x11000001

    sget-object v7, Landroid/graphics/Shader$TileMode;->CLAMP:Landroid/graphics/Shader$TileMode;

    const/4 v1, 0x0

    const/4 v2, 0x0

    const/4 v3, 0x0

    const v5, 0x22ffffff

    invoke-direct/range {v0 .. v7}, Landroid/graphics/LinearGradient;-><init>(FFFFIILandroid/graphics/Shader$TileMode;)V

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setShader(Landroid/graphics/Shader;)Landroid/graphics/Shader;

    .line 77
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    new-instance v1, Landroid/graphics/LinearGradient;

    const v7, -0x66ff19ba

    sget-object v8, Landroid/graphics/Shader$TileMode;->CLAMP:Landroid/graphics/Shader$TileMode;

    move v5, v4

    const/4 v4, 0x0

    const v6, 0x1100e646

    invoke-direct/range {v1 .. v8}, Landroid/graphics/LinearGradient;-><init>(FFFFIILandroid/graphics/Shader$TileMode;)V

    invoke-virtual {p1, v1}, Landroid/graphics/Paint;->setShader(Landroid/graphics/Shader;)Landroid/graphics/Shader;

    .line 79
    return-void
.end method

.method public updatePayload(Ljava/lang/String;Z)V
    .locals 6

    .line 42
    if-eqz p2, :cond_3

    if-nez p1, :cond_0

    goto/16 :goto_2

    .line 48
    :cond_0
    :try_start_0
    new-instance p2, Lorg/json/JSONObject;

    invoke-direct {p2, p1}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    const-string p1, "navPathLeft"

    invoke-virtual {p2, p1}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result p1

    if-nez p1, :cond_navdy_path_payload_present

    return-void

    :cond_navdy_path_payload_present

    .line 49
    const-string p1, "navPathLeft"

    invoke-virtual {p2, p1}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object p1

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object p1

    .line 50
    const-string v0, "navPathRight"

    invoke-virtual {p2, v0}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v0

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v0

    .line 51
    const-string v1, "navLaneLeft"

    invoke-virtual {p2, v1}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v1

    invoke-static {v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v1

    .line 52
    const-string v2, "navLaneRight"

    invoke-virtual {p2, v2}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v2

    invoke-static {v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v2

    const-string v3, "navRoadEdgeLeft"

    invoke-virtual {p2, v3}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v3

    invoke-static {v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v4

    const-string v3, "navRoadEdgeRight"

    invoke-virtual {p2, v3}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v3

    invoke-static {v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v5

    .line 53
    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v3

    if-eqz v3, :cond_2

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v3

    if-eqz v3, :cond_2

    .line 54
    invoke-static {v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v3

    if-eqz v3, :cond_2

    invoke-static {v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v3

    if-nez v3, :cond_1

    goto :goto_0

    .line 59
    :cond_1
    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 60
    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    .line 61
    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    .line 62
    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    iput-object v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    iput-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    .line 63
    const-string p1, "navLaneLeftProb"

    const-wide/16 v0, 0x0

    invoke-virtual {p2, p1, v0, v1}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v2

    double-to-float p1, v2

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftProb:F

    .line 64
    const-string p1, "navLaneRightProb"

    invoke-virtual {p2, p1, v0, v1}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide p1

    double-to-float p1, p1

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightProb:F

    .line 65
    const/4 p1, 0x0

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setVisibility(I)V

    .line 66
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->invalidate()V

    .line 69
    goto :goto_1

    .line 55
    :cond_2
    :goto_0
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 56
    return-void

    .line 67
    :catch_0
    move-exception p1

    .line 68
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V

    .line 70
    :goto_1
    return-void

    .line 43
    :cond_3
    :goto_2
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V

    .line 44
    return-void
.end method
