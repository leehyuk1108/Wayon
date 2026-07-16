.class public final Lcom/navdy/hud/app/openpilot/OpenpilotPathView;
.super Landroid/view/View;
.source "OpenpilotPathView.java"


# static fields
.field private static final COLOR_GREEN:I = -0xff19ba

.field private static final COLOR_VEHICLE_FUSED:I = -0xff1a01

.field private static final COLOR_VEHICLE_RADAR:I = -0x22000001

.field private static final COLOR_VEHICLE_VISION:I = -0xff19ba

.field private static final DASH_FRAME_MS:J = 0x42L

.field private static final LANE_DASH_CYCLE:F = 80.0f

.field private static final LANE_DASH_PATTERN:[F

.field private static final ROAD_EDGE_MIN_CONFIDENCE:F = 0.5f


# instance fields
.field private dashPhase:F

.field private laneFarLeft:[F

.field private laneFarLeftProb:F

.field private laneFarRight:[F

.field private laneFarRightProb:F

.field private laneLeft:[F

.field private laneLeftProb:F

.field private final lanePaint:Landroid/graphics/Paint;

.field private laneRight:[F

.field private laneRightProb:F

.field private lastDashFrameMs:J

.field private final pathEdgePaint:Landroid/graphics/Paint;

.field private final pathFillPaint:Landroid/graphics/Paint;

.field private pathLeft:[F

.field private pathRight:[F

.field private roadEdgeLeft:[F

.field private roadEdgeLeftProb:F

.field private final roadEdgePaint:Landroid/graphics/Paint;

.field private roadEdgeRight:[F

.field private roadEdgeRightProb:F

.field private final vehicleBitmapPaint:Landroid/graphics/Paint;

.field private final vehicleFillPaint:Landroid/graphics/Paint;

.field private final vehicleFusedFilter:Landroid/graphics/LightingColorFilter;

.field private final vehicleLeftMarkerBitmaps:[Landroid/graphics/Bitmap;

.field private final vehicleMarkerBitmap:Landroid/graphics/Bitmap;

.field private final vehicleRadarFilter:Landroid/graphics/LightingColorFilter;

.field private final vehicleRightMarkerBitmaps:[Landroid/graphics/Bitmap;

.field private vehicleSpeedKph:F

.field private final vehicleVisionFilter:Landroid/graphics/LightingColorFilter;

.field private vehicles:[F


# direct methods
.method static constructor <clinit>()V
    .registers 1

    .line 25
    const/4 v0, 0x2

    new-array v0, v0, [F

    fill-array-data v0, :array_a

    sput-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->LANE_DASH_PATTERN:[F

    return-void

    nop

    :array_a
    .array-data 4
        0x42600000    # 56.0f
        0x41c00000    # 24.0f
    .end array-data
.end method

.method public constructor <init>(Landroid/content/Context;)V
    .registers 13

    .line 65
    invoke-direct {p0, p1}, Landroid/view/View;-><init>(Landroid/content/Context;)V

    .line 30
    new-instance v0, Landroid/graphics/Paint;

    const/4 v1, 0x1

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    .line 31
    new-instance v2, Landroid/graphics/Paint;

    invoke-direct {v2, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    .line 32
    new-instance v3, Landroid/graphics/Paint;

    invoke-direct {v3, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    .line 33
    new-instance v4, Landroid/graphics/Paint;

    invoke-direct {v4, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    .line 34
    new-instance v5, Landroid/graphics/Paint;

    invoke-direct {v5, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    .line 35
    new-instance v6, Landroid/graphics/Paint;

    const/4 v7, 0x3

    invoke-direct {v6, v7}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    .line 37
    new-instance v6, Landroid/graphics/LightingColorFilter;

    const/4 v8, -0x1

    const/4 v9, 0x0

    invoke-direct {v6, v8, v9}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRadarFilter:Landroid/graphics/LightingColorFilter;

    .line 38
    new-instance v6, Landroid/graphics/LightingColorFilter;

    const v8, -0xff19ba

    invoke-direct {v6, v8, v9}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleVisionFilter:Landroid/graphics/LightingColorFilter;

    .line 40
    new-instance v6, Landroid/graphics/LightingColorFilter;

    const v10, -0xff1a01

    invoke-direct {v6, v10, v9}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFusedFilter:Landroid/graphics/LightingColorFilter;

    .line 45
    new-array v6, v9, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeft:[F

    .line 47
    new-array v6, v9, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    .line 49
    new-array v6, v9, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    .line 51
    new-array v6, v9, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRight:[F

    .line 53
    new-array v6, v9, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 54
    new-array v6, v9, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    .line 55
    new-array v6, v9, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    .line 57
    new-array v6, v9, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    .line 59
    new-array v6, v9, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    .line 67
    sget-object v6, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v0, v6}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 68
    sget-object v6, Landroid/graphics/Paint$Cap;->ROUND:Landroid/graphics/Paint$Cap;

    invoke-virtual {v0, v6}, Landroid/graphics/Paint;->setStrokeCap(Landroid/graphics/Paint$Cap;)V

    .line 69
    sget-object v6, Landroid/graphics/Paint$Join;->ROUND:Landroid/graphics/Paint$Join;

    invoke-virtual {v0, v6}, Landroid/graphics/Paint;->setStrokeJoin(Landroid/graphics/Paint$Join;)V

    .line 70
    const/high16 v6, 0x40200000    # 2.5f

    invoke-virtual {v0, v6}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 72
    sget-object v0, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v2, v0}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 73
    sget-object v0, Landroid/graphics/Paint$Cap;->ROUND:Landroid/graphics/Paint$Cap;

    invoke-virtual {v2, v0}, Landroid/graphics/Paint;->setStrokeCap(Landroid/graphics/Paint$Cap;)V

    .line 74
    sget-object v0, Landroid/graphics/Paint$Join;->ROUND:Landroid/graphics/Paint$Join;

    invoke-virtual {v2, v0}, Landroid/graphics/Paint;->setStrokeJoin(Landroid/graphics/Paint$Join;)V

    .line 75
    const v0, 0x400ccccd    # 2.2f

    invoke-virtual {v2, v0}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 76
    const/16 v0, 0x73

    invoke-virtual {v2, v0}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 78
    invoke-virtual {v3, v8}, Landroid/graphics/Paint;->setColor(I)V

    .line 79
    sget-object v0, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v3, v0}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 80
    sget-object v0, Landroid/graphics/Paint$Join;->ROUND:Landroid/graphics/Paint$Join;

    invoke-virtual {v3, v0}, Landroid/graphics/Paint;->setStrokeJoin(Landroid/graphics/Paint$Join;)V

    .line 81
    const v0, 0x3fe66666    # 1.8f

    invoke-virtual {v3, v0}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 83
    sget-object v0, Landroid/graphics/Paint$Style;->FILL:Landroid/graphics/Paint$Style;

    invoke-virtual {v4, v0}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 85
    sget-object v0, Landroid/graphics/Paint$Style;->FILL:Landroid/graphics/Paint$Style;

    invoke-virtual {v5, v0}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 86
    const-string v0, "navdy_vehicle_marker"

    invoke-direct {p0, p1, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v0

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleMarkerBitmap:Landroid/graphics/Bitmap;

    .line 87
    const/4 v0, 0x6

    new-array v2, v0, [Landroid/graphics/Bitmap;

    .line 88
    const-string v3, "navdy_vehicle_marker_left_4"

    invoke-direct {p0, p1, v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v3

    aput-object v3, v2, v9

    .line 89
    const-string v3, "navdy_vehicle_marker_left_8"

    invoke-direct {p0, p1, v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v3

    aput-object v3, v2, v1

    .line 90
    const-string v3, "navdy_vehicle_marker_left_12"

    invoke-direct {p0, p1, v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v3

    const/4 v4, 0x2

    aput-object v3, v2, v4

    .line 91
    const-string v3, "navdy_vehicle_marker_left_16"

    invoke-direct {p0, p1, v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v3

    aput-object v3, v2, v7

    .line 92
    const-string v3, "navdy_vehicle_marker_left_20"

    invoke-direct {p0, p1, v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v3

    const/4 v5, 0x4

    aput-object v3, v2, v5

    .line 93
    const-string v3, "navdy_vehicle_marker_left_24"

    invoke-direct {p0, p1, v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v3

    const/4 v6, 0x5

    aput-object v3, v2, v6

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleLeftMarkerBitmaps:[Landroid/graphics/Bitmap;

    .line 95
    new-array v0, v0, [Landroid/graphics/Bitmap;

    .line 96
    const-string v2, "navdy_vehicle_marker_right_4"

    invoke-direct {p0, p1, v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v2

    aput-object v2, v0, v9

    .line 97
    const-string v2, "navdy_vehicle_marker_right_8"

    invoke-direct {p0, p1, v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v2

    aput-object v2, v0, v1

    .line 98
    const-string v1, "navdy_vehicle_marker_right_12"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v1

    aput-object v1, v0, v4

    .line 99
    const-string v1, "navdy_vehicle_marker_right_16"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v1

    aput-object v1, v0, v7

    .line 100
    const-string v1, "navdy_vehicle_marker_right_20"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v1

    aput-object v1, v0, v5

    .line 101
    const-string v1, "navdy_vehicle_marker_right_24"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object p1

    aput-object p1, v0, v6

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRightMarkerBitmaps:[Landroid/graphics/Bitmap;

    .line 103
    invoke-virtual {p0, v9}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setWillNotDraw(Z)V

    .line 104
    const/16 p1, 0x8

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setVisibility(I)V

    .line 105
    return-void
.end method

.method private static clamp01(F)F
    .registers 2

    .line 338
    const/high16 v0, 0x3f800000    # 1.0f

    invoke-static {v0, p0}, Ljava/lang/Math;->min(FF)F

    move-result p0

    const/4 v0, 0x0

    invoke-static {v0, p0}, Ljava/lang/Math;->max(FF)F

    move-result p0

    return p0
.end method

.method private clearGeometry()V
    .registers 3

    .line 316
    const/4 v0, 0x0

    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 317
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    .line 318
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeft:[F

    .line 319
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    .line 320
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    .line 321
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRight:[F

    .line 322
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    .line 323
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    .line 324
    new-array v0, v0, [F

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    .line 325
    const/4 v0, 0x0

    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftProb:F

    .line 326
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftProb:F

    .line 327
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightProb:F

    .line 328
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightProb:F

    .line 329
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeftProb:F

    .line 330
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRightProb:F

    .line 331
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    .line 332
    const-wide/16 v0, 0x0

    iput-wide v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    .line 333
    const/16 v0, 0x8

    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setVisibility(I)V

    .line 334
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->invalidate()V

    .line 335
    return-void
.end method

.method private drawLane(Landroid/graphics/Canvas;[FF)V
    .registers 6

    .line 212
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_25

    const v0, 0x3d4ccccd    # 0.05f

    cmpg-float v0, p3, v0

    if-gez v0, :cond_e

    goto :goto_25

    .line 215
    :cond_e
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    const/high16 v1, 0x43610000    # 225.0f

    mul-float p3, p3, v1

    const/high16 v1, 0x41f00000    # 30.0f

    add-float/2addr p3, v1

    float-to-int p3, p3

    invoke-virtual {v0, p3}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 216
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object p2

    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p2, p3}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 217
    return-void

    .line 213
    :cond_25
    :goto_25
    return-void
.end method

.method private drawRoadEdge(Landroid/graphics/Canvas;[FF)V
    .registers 6

    .line 220
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_21

    const/high16 v0, 0x3f000000    # 0.5f

    cmpg-float v0, p3, v0

    if-gez v0, :cond_d

    goto :goto_21

    .line 223
    :cond_d
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    const/high16 v1, 0x430c0000    # 140.0f

    mul-float p3, p3, v1

    float-to-int p3, p3

    invoke-virtual {v0, p3}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 224
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object p2

    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p2, p3}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 225
    return-void

    .line 221
    :cond_21
    :goto_21
    return-void
.end method

.method private drawVehicle(Landroid/graphics/Canvas;FFFIIF)V
    .registers 13

    .line 255
    const/high16 v0, 0x42a00000    # 80.0f

    div-float/2addr p4, v0

    const/high16 v0, 0x3f800000    # 1.0f

    sub-float/2addr v0, p4

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p4

    .line 256
    const/high16 v0, 0x423a0000    # 46.5f

    mul-float p4, p4, v0

    const/high16 v0, 0x41400000    # 12.0f

    add-float/2addr p4, v0

    .line 257
    const v0, 0x3fc66666    # 1.55f

    mul-float v0, v0, p4

    .line 259
    const/4 v1, 0x2

    const/16 v2, 0xff

    if-ne p5, v1, :cond_30

    .line 260
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    const v1, -0xff1a01

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColor(I)V

    .line 261
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFusedFilter:Landroid/graphics/LightingColorFilter;

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 262
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    invoke-virtual {p5, v2}, Landroid/graphics/Paint;->setAlpha(I)V

    goto :goto_5e

    .line 263
    :cond_30
    const/4 v1, 0x1

    if-ne p5, v1, :cond_48

    .line 264
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    const v1, -0xff19ba

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColor(I)V

    .line 265
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleVisionFilter:Landroid/graphics/LightingColorFilter;

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 266
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    invoke-virtual {p5, v2}, Landroid/graphics/Paint;->setAlpha(I)V

    goto :goto_5e

    .line 268
    :cond_48
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    const v1, -0x22000001

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColor(I)V

    .line 269
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRadarFilter:Landroid/graphics/LightingColorFilter;

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 270
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    const/16 v1, 0xdd

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 273
    :goto_5e
    new-instance p5, Landroid/graphics/RectF;

    const v1, 0x3f51eb85    # 0.82f

    mul-float v1, v1, p4

    sub-float v2, p2, v1

    const v3, 0x3f0ccccd    # 0.55f

    mul-float v3, v3, v0

    sub-float v3, p3, v3

    add-float/2addr v1, p2

    const v4, 0x3ee66666    # 0.45f

    mul-float v0, v0, v4

    add-float/2addr p3, v0

    invoke-direct {p5, v2, v3, v1, p3}, Landroid/graphics/RectF;-><init>(FFFF)V

    .line 278
    invoke-direct {p0, p7, p6, p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleMarkerForYaw(FIF)Landroid/graphics/Bitmap;

    move-result-object p2

    .line 279
    if-eqz p2, :cond_85

    .line 280
    const/4 p3, 0x0

    iget-object p4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p2, p3, p5, p4}, Landroid/graphics/Canvas;->drawBitmap(Landroid/graphics/Bitmap;Landroid/graphics/Rect;Landroid/graphics/RectF;Landroid/graphics/Paint;)V

    goto :goto_8f

    .line 282
    :cond_85
    const p2, 0x3e75c28f    # 0.24f

    mul-float p4, p4, p2

    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p5, p4, p4, p2}, Landroid/graphics/Canvas;->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V

    .line 284
    :goto_8f
    return-void
.end method

.method private drawVehicles(Landroid/graphics/Canvas;)V
    .registers 14

    .line 245
    const/4 v0, 0x0

    :goto_1
    add-int/lit8 v1, v0, 0x5

    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    array-length v3, v2

    if-ge v1, v3, :cond_26

    .line 246
    aget v6, v2, v0

    add-int/lit8 v3, v0, 0x1

    aget v7, v2, v3

    add-int/lit8 v3, v0, 0x2

    aget v8, v2, v3

    add-int/lit8 v3, v0, 0x3

    aget v3, v2, v3

    float-to-int v9, v3

    add-int/lit8 v3, v0, 0x4

    aget v3, v2, v3

    float-to-int v10, v3

    aget v11, v2, v1

    move-object v4, p0

    move-object v5, p1

    invoke-direct/range {v4 .. v11}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawVehicle(Landroid/graphics/Canvas;FFFIIF)V

    .line 245
    add-int/lit8 v0, v0, 0x6

    goto :goto_1

    .line 250
    :cond_26
    return-void
.end method

.method private static linePath([F)Landroid/graphics/Path;
    .registers 5

    .line 342
    new-instance v0, Landroid/graphics/Path;

    invoke-direct {v0}, Landroid/graphics/Path;-><init>()V

    .line 343
    const/4 v1, 0x0

    aget v1, p0, v1

    const/4 v2, 0x1

    aget v2, p0, v2

    invoke-virtual {v0, v1, v2}, Landroid/graphics/Path;->moveTo(FF)V

    .line 344
    const/4 v1, 0x2

    :goto_f
    array-length v2, p0

    if-ge v1, v2, :cond_1e

    .line 345
    aget v2, p0, v1

    add-int/lit8 v3, v1, 0x1

    aget v3, p0, v3

    invoke-virtual {v0, v2, v3}, Landroid/graphics/Path;->lineTo(FF)V

    .line 344
    add-int/lit8 v1, v1, 0x2

    goto :goto_f

    .line 347
    :cond_1e
    return-object v0
.end method

.method private loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;
    .registers 5

    .line 108
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->getResources()Landroid/content/res/Resources;

    move-result-object v0

    .line 109
    invoke-virtual {p1}, Landroid/content/Context;->getPackageName()Ljava/lang/String;

    move-result-object p1

    .line 108
    const-string v1, "drawable"

    invoke-virtual {v0, p2, v1, p1}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I

    move-result p1

    .line 110
    if-nez p1, :cond_12

    const/4 p1, 0x0

    goto :goto_1a

    :cond_12
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->getResources()Landroid/content/res/Resources;

    move-result-object p2

    invoke-static {p2, p1}, Landroid/graphics/BitmapFactory;->decodeResource(Landroid/content/res/Resources;I)Landroid/graphics/Bitmap;

    move-result-object p1

    :goto_1a
    return-object p1
.end method

.method private static readPoints(Lorg/json/JSONArray;)[F
    .registers 5

    .line 351
    const/4 v0, 0x0

    if-eqz p0, :cond_2d

    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    const/4 v2, 0x4

    if-lt v1, v2, :cond_2d

    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    and-int/lit8 v1, v1, 0x1

    if-eqz v1, :cond_13

    goto :goto_2d

    .line 354
    :cond_13
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    new-array v1, v1, [F

    .line 355
    nop

    :goto_1a
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v2

    if-ge v0, v2, :cond_2c

    .line 356
    const-wide/16 v2, 0x0

    invoke-virtual {p0, v0, v2, v3}, Lorg/json/JSONArray;->optDouble(ID)D

    move-result-wide v2

    double-to-float v2, v2

    aput v2, v1, v0

    .line 355
    add-int/lit8 v0, v0, 0x1

    goto :goto_1a

    .line 358
    :cond_2c
    return-object v1

    .line 352
    :cond_2d
    :goto_2d
    new-array p0, v0, [F

    return-object p0
.end method

.method private static readVehicles(Lorg/json/JSONArray;)[F
    .registers 13

    .line 362
    const/4 v0, 0x0

    if-eqz p0, :cond_b7

    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    if-nez v1, :cond_b

    goto/16 :goto_b7

    .line 365
    :cond_b
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    mul-int/lit8 v1, v1, 0x6

    new-array v2, v1, [F

    .line 366
    nop

    .line 367
    const/4 v3, 0x0

    const/4 v4, 0x0

    :goto_16
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v5

    if-ge v3, v5, :cond_ae

    .line 368
    invoke-virtual {p0, v3}, Lorg/json/JSONArray;->optJSONObject(I)Lorg/json/JSONObject;

    move-result-object v5

    .line 369
    if-nez v5, :cond_24

    .line 370
    goto/16 :goto_aa

    .line 372
    :cond_24
    const-string v6, "source"

    const-string v7, "radar"

    invoke-virtual {v5, v6, v7}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v6

    .line 373
    const-string v7, "fused"

    invoke-virtual {v7, v6}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v7

    const/4 v8, 0x1

    if-eqz v7, :cond_37

    const/4 v6, 0x2

    goto :goto_42

    :cond_37
    const-string v7, "vision"

    invoke-virtual {v7, v6}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v6

    if-eqz v6, :cond_41

    const/4 v6, 0x1

    goto :goto_42

    :cond_41
    const/4 v6, 0x0

    .line 374
    :goto_42
    const-string v7, "lane"

    const-string v9, "center"

    invoke-virtual {v5, v7, v9}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v7

    .line 375
    const-string v9, "left"

    invoke-virtual {v9, v7}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v9

    if-eqz v9, :cond_54

    const/4 v8, -0x1

    goto :goto_5e

    :cond_54
    const-string v9, "right"

    invoke-virtual {v9, v7}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v7

    if-eqz v7, :cond_5d

    goto :goto_5e

    :cond_5d
    const/4 v8, 0x0

    .line 376
    :goto_5e
    add-int/lit8 v7, v4, 0x1

    const-string v9, "screenX"

    const-wide/high16 v10, 0x4064000000000000L    # 160.0

    invoke-virtual {v5, v9, v10, v11}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v9

    double-to-float v9, v9

    aput v9, v2, v4

    .line 377
    add-int/lit8 v4, v7, 0x1

    const-string v9, "screenY"

    const-wide/high16 v10, 0x4020000000000000L    # 8.0

    invoke-virtual {v5, v9, v10, v11}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v9

    double-to-float v9, v9

    aput v9, v2, v7

    .line 378
    add-int/lit8 v7, v4, 0x1

    const-string v9, "distanceM"

    const-wide/high16 v10, 0x4054000000000000L    # 80.0

    invoke-virtual {v5, v9, v10, v11}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v9

    double-to-float v9, v9

    const/4 v10, 0x0

    invoke-static {v10, v9}, Ljava/lang/Math;->max(FF)F

    move-result v9

    aput v9, v2, v4

    .line 379
    add-int/lit8 v4, v7, 0x1

    int-to-float v6, v6

    aput v6, v2, v7

    .line 380
    add-int/lit8 v6, v4, 0x1

    int-to-float v7, v8

    aput v7, v2, v4

    .line 381
    add-int/lit8 v4, v6, 0x1

    const-string v7, "yawDeg"

    invoke-virtual {v5, v7}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result v8

    if-eqz v8, :cond_a6

    .line 382
    const-wide/16 v8, 0x0

    invoke-virtual {v5, v7, v8, v9}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v7

    double-to-float v5, v7

    goto :goto_a8

    :cond_a6
    const/high16 v5, 0x7fc00000    # Float.NaN

    :goto_a8
    aput v5, v2, v6

    .line 367
    :goto_aa
    add-int/lit8 v3, v3, 0x1

    goto/16 :goto_16

    .line 384
    :cond_ae
    if-ne v4, v1, :cond_b1

    .line 385
    return-object v2

    .line 387
    :cond_b1
    new-array p0, v4, [F

    .line 388
    invoke-static {v2, v0, p0, v0, v4}, Ljava/lang/System;->arraycopy(Ljava/lang/Object;ILjava/lang/Object;II)V

    .line 389
    return-object p0

    .line 363
    :cond_b7
    :goto_b7
    new-array p0, v0, [F

    return-object p0
.end method

.method private updateDashPhase()V
    .registers 8

    .line 228
    invoke-static {}, Landroid/os/SystemClock;->uptimeMillis()J

    move-result-wide v0

    .line 229
    iget-wide v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    const-wide/16 v4, 0x0

    cmp-long v6, v2, v4

    if-nez v6, :cond_f

    .line 230
    iput-wide v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    .line 231
    return-void

    .line 234
    :cond_f
    sub-long v2, v0, v2

    const-wide/16 v4, 0x96

    invoke-static {v2, v3, v4, v5}, Ljava/lang/Math;->min(JJ)J

    move-result-wide v2

    .line 235
    iput-wide v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    .line 236
    iget v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    const/high16 v1, 0x3f800000    # 1.0f

    cmpg-float v1, v0, v1

    if-gtz v1, :cond_22

    .line 237
    return-void

    .line 240
    :cond_22
    const v1, 0x3f4ccccd    # 0.8f

    mul-float v0, v0, v1

    const/high16 v1, 0x41900000    # 18.0f

    invoke-static {v1, v0}, Ljava/lang/Math;->max(FF)F

    move-result v0

    const/high16 v1, 0x42a00000    # 80.0f

    invoke-static {v1, v0}, Ljava/lang/Math;->min(FF)F

    move-result v0

    .line 241
    iget v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashPhase:F

    long-to-float v2, v2

    mul-float v2, v2, v0

    const/high16 v0, 0x447a0000    # 1000.0f

    div-float/2addr v2, v0

    add-float/2addr v4, v2

    rem-float/2addr v4, v1

    iput v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashPhase:F

    .line 242
    return-void
.end method

.method private static validLine([F)Z
    .registers 3

    .line 393
    if-eqz p0, :cond_c

    array-length v0, p0

    const/4 v1, 0x4

    if-lt v0, v1, :cond_c

    array-length p0, p0

    const/4 v0, 0x1

    and-int/2addr p0, v0

    if-nez p0, :cond_c

    goto :goto_d

    :cond_c
    const/4 v0, 0x0

    :goto_d
    return v0
.end method

.method private vehicleMarkerForYaw(FIF)Landroid/graphics/Bitmap;
    .registers 8

    .line 287
    invoke-static {p1}, Ljava/lang/Float;->isNaN(F)Z

    move-result v0

    const/4 v1, 0x0

    const/high16 v2, 0x40800000    # 4.0f

    const/high16 v3, 0x41c00000    # 24.0f

    if-eqz v0, :cond_3b

    .line 288
    const/high16 p1, 0x43200000    # 160.0f

    sub-float/2addr p3, p1

    invoke-static {p3}, Ljava/lang/Math;->abs(F)F

    move-result p1

    .line 290
    cmpg-float p3, p1, v3

    if-ltz p3, :cond_37

    if-nez p2, :cond_19

    goto :goto_37

    .line 292
    :cond_19
    const/high16 p3, 0x42400000    # 48.0f

    cmpg-float p3, p1, p3

    if-gez p3, :cond_22

    .line 293
    const/high16 p1, 0x40800000    # 4.0f

    goto :goto_38

    .line 294
    :cond_22
    const/high16 p3, 0x42900000    # 72.0f

    cmpg-float p3, p1, p3

    if-gez p3, :cond_2b

    .line 295
    const/high16 p1, 0x41000000    # 8.0f

    goto :goto_38

    .line 296
    :cond_2b
    const/high16 p3, 0x42d00000    # 104.0f

    cmpg-float p1, p1, p3

    if-gez p1, :cond_34

    .line 297
    const/high16 p1, 0x41400000    # 12.0f

    goto :goto_38

    .line 299
    :cond_34
    const/high16 p1, 0x41800000    # 16.0f

    goto :goto_38

    .line 291
    :cond_37
    :goto_37
    const/4 p1, 0x0

    .line 301
    :goto_38
    if-gez p2, :cond_3b

    neg-float p1, p1

    .line 304
    :cond_3b
    invoke-static {p1}, Ljava/lang/Math;->abs(F)F

    move-result p2

    invoke-static {v3, p2}, Ljava/lang/Math;->min(FF)F

    move-result p2

    .line 305
    const/high16 p3, 0x40000000    # 2.0f

    cmpg-float p3, p2, p3

    if-gez p3, :cond_4c

    .line 306
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleMarkerBitmap:Landroid/graphics/Bitmap;

    return-object p1

    .line 308
    :cond_4c
    div-float/2addr p2, v2

    invoke-static {p2}, Ljava/lang/Math;->round(F)I

    move-result p2

    add-int/lit8 p2, p2, -0x1

    const/4 p3, 0x0

    invoke-static {p3, p2}, Ljava/lang/Math;->max(II)I

    move-result p2

    const/4 p3, 0x5

    invoke-static {p3, p2}, Ljava/lang/Math;->min(II)I

    move-result p2

    .line 309
    cmpg-float p1, p1, v1

    if-gez p1, :cond_66

    .line 310
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleLeftMarkerBitmaps:[Landroid/graphics/Bitmap;

    aget-object p1, p1, p2

    goto :goto_6a

    .line 311
    :cond_66
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRightMarkerBitmaps:[Landroid/graphics/Bitmap;

    aget-object p1, p1, p2

    .line 312
    :goto_6a
    if-nez p1, :cond_6e

    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleMarkerBitmap:Landroid/graphics/Bitmap;

    :cond_6e
    return-object p1
.end method


# virtual methods
.method protected onDraw(Landroid/graphics/Canvas;)V
    .registers 7

    .line 181
    invoke-super {p0, p1}, Landroid/view/View;->onDraw(Landroid/graphics/Canvas;)V

    .line 182
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_9a

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-nez v0, :cond_15

    goto/16 :goto_9a

    .line 186
    :cond_15
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    .line 187
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    array-length v1, v1

    add-int/lit8 v1, v1, -0x2

    :goto_20
    if-ltz v1, :cond_30

    .line 188
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    aget v3, v2, v1

    add-int/lit8 v4, v1, 0x1

    aget v2, v2, v4

    invoke-virtual {v0, v3, v2}, Landroid/graphics/Path;->lineTo(FF)V

    .line 187
    add-int/lit8 v1, v1, -0x2

    goto :goto_20

    .line 190
    :cond_30
    invoke-virtual {v0}, Landroid/graphics/Path;->close()V

    .line 191
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 192
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 193
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 195
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeftProb:F

    invoke-direct {p0, p1, v0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawRoadEdge(Landroid/graphics/Canvas;[FF)V

    .line 196
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRightProb:F

    invoke-direct {p0, p1, v0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawRoadEdge(Landroid/graphics/Canvas;[FF)V

    .line 198
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->updateDashPhase()V

    .line 199
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    new-instance v1, Landroid/graphics/DashPathEffect;

    sget-object v2, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->LANE_DASH_PATTERN:[F

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashPhase:F

    invoke-direct {v1, v2, v3}, Landroid/graphics/DashPathEffect;-><init>([FF)V

    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setPathEffect(Landroid/graphics/PathEffect;)Landroid/graphics/PathEffect;

    .line 200
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeft:[F

    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftProb:F

    invoke-direct {p0, p1, v0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLane(Landroid/graphics/Canvas;[FF)V

    .line 201
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftProb:F

    invoke-direct {p0, p1, v0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLane(Landroid/graphics/Canvas;[FF)V

    .line 202
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightProb:F

    invoke-direct {p0, p1, v0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLane(Landroid/graphics/Canvas;[FF)V

    .line 203
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRight:[F

    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightProb:F

    invoke-direct {p0, p1, v0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLane(Landroid/graphics/Canvas;[FF)V

    .line 204
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawVehicles(Landroid/graphics/Canvas;)V

    .line 206
    iget p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    const/high16 v0, 0x3f800000    # 1.0f

    cmpl-float p1, p1, v0

    if-lez p1, :cond_99

    .line 207
    const-wide/16 v0, 0x42

    invoke-virtual {p0, v0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->postInvalidateDelayed(J)V

    .line 209
    :cond_99
    return-void

    .line 183
    :cond_9a
    :goto_9a
    return-void
.end method

.method protected onSizeChanged(IIII)V
    .registers 13

    .line 169
    invoke-super {p0, p1, p2, p3, p4}, Landroid/view/View;->onSizeChanged(IIII)V

    .line 170
    int-to-float p1, p2

    .line 171
    new-instance p2, Landroid/graphics/LinearGradient;

    const/4 v1, 0x0

    const/4 v2, 0x0

    const/4 v3, 0x0

    const v5, 0x22ffffff

    const v6, -0x11000001

    sget-object v7, Landroid/graphics/Shader$TileMode;->CLAMP:Landroid/graphics/Shader$TileMode;

    move-object v0, p2

    move v4, p1

    invoke-direct/range {v0 .. v7}, Landroid/graphics/LinearGradient;-><init>(FFFFIILandroid/graphics/Shader$TileMode;)V

    .line 173
    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    invoke-virtual {p3, p2}, Landroid/graphics/Paint;->setShader(Landroid/graphics/Shader;)Landroid/graphics/Shader;

    .line 174
    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p3, p2}, Landroid/graphics/Paint;->setShader(Landroid/graphics/Shader;)Landroid/graphics/Shader;

    .line 175
    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    new-instance p3, Landroid/graphics/LinearGradient;

    const v5, 0x1100e646

    const v6, -0x66ff19ba

    sget-object v7, Landroid/graphics/Shader$TileMode;->CLAMP:Landroid/graphics/Shader$TileMode;

    move-object v0, p3

    invoke-direct/range {v0 .. v7}, Landroid/graphics/LinearGradient;-><init>(FFFFIILandroid/graphics/Shader$TileMode;)V

    invoke-virtual {p2, p3}, Landroid/graphics/Paint;->setShader(Landroid/graphics/Shader;)Landroid/graphics/Shader;

    .line 177
    return-void
.end method

.method public updatePayload(Ljava/lang/String;Z)V
    .registers 13

    .line 114
    const-string v0, "navPathLeft"

    const-string v1, "navVehicles"

    if-eqz p2, :cond_115

    if-nez p1, :cond_a

    goto/16 :goto_115

    .line 120
    :cond_a
    :try_start_a
    new-instance p2, Lorg/json/JSONObject;

    invoke-direct {p2, p1}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    .line 121
    const-string p1, "vEgoKph"

    const-wide/16 v2, 0x0

    invoke-virtual {p2, p1, v2, v3}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v4

    double-to-float p1, v4

    const/4 v4, 0x0

    invoke-static {v4, p1}, Ljava/lang/Math;->max(FF)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    .line 122
    invoke-virtual {p2, v1}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result p1

    if-eqz p1, :cond_2f

    .line 123
    invoke-virtual {p2, v1}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object p1

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readVehicles(Lorg/json/JSONArray;)[F

    move-result-object p1

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    .line 125
    :cond_2f
    invoke-virtual {p2, v0}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result p1

    if-nez p1, :cond_3f

    .line 126
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->getVisibility()I

    move-result p1

    if-nez p1, :cond_3e

    .line 127
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->invalidate()V

    .line 129
    :cond_3e
    return-void

    .line 132
    :cond_3f
    invoke-virtual {p2, v0}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object p1

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object p1

    .line 133
    const-string v0, "navPathRight"

    invoke-virtual {p2, v0}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v0

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v0

    .line 134
    const-string v1, "navLaneFarLeft"

    invoke-virtual {p2, v1}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v1

    invoke-static {v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v1

    .line 135
    const-string v4, "navLaneLeft"

    invoke-virtual {p2, v4}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v4

    invoke-static {v4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v4

    .line 136
    const-string v5, "navLaneRight"

    invoke-virtual {p2, v5}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v5

    invoke-static {v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v5

    .line 137
    const-string v6, "navLaneFarRight"

    invoke-virtual {p2, v6}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v6

    invoke-static {v6}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v6

    .line 138
    const-string v7, "navRoadEdgeLeft"

    invoke-virtual {p2, v7}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v7

    invoke-static {v7}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v7

    .line 139
    const-string v8, "navRoadEdgeRight"

    invoke-virtual {p2, v8}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v8

    invoke-static {v8}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v8

    .line 140
    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v9

    if-eqz v9, :cond_10c

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v9

    if-eqz v9, :cond_10c

    .line 141
    invoke-static {v4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v9

    if-eqz v9, :cond_10c

    invoke-static {v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v9

    if-nez v9, :cond_a6

    goto :goto_10c

    .line 146
    :cond_a6
    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 147
    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    .line 148
    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeft:[F

    .line 149
    iput-object v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    .line 150
    iput-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    .line 151
    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRight:[F

    .line 152
    iput-object v7, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    .line 153
    iput-object v8, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    .line 154
    const-string p1, "navLaneFarLeftProb"

    invoke-virtual {p2, p1, v2, v3}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p1, v0

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftProb:F

    .line 155
    const-string p1, "navLaneLeftProb"

    invoke-virtual {p2, p1, v2, v3}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p1, v0

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftProb:F

    .line 156
    const-string p1, "navLaneRightProb"

    invoke-virtual {p2, p1, v2, v3}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p1, v0

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightProb:F

    .line 157
    const-string p1, "navLaneFarRightProb"

    invoke-virtual {p2, p1, v2, v3}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p1, v0

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightProb:F

    .line 158
    const-string p1, "navRoadEdgeLeftProb"

    invoke-virtual {p2, p1, v2, v3}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p1, v0

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeftProb:F

    .line 159
    const-string p1, "navRoadEdgeRightProb"

    invoke-virtual {p2, p1, v2, v3}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide p1

    double-to-float p1, p1

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRightProb:F

    .line 160
    const/4 p1, 0x0

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setVisibility(I)V

    .line 161
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->invalidate()V

    .line 164
    goto :goto_114

    .line 142
    :cond_10c
    :goto_10c
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V
    :try_end_10f
    .catch Ljava/lang/Exception; {:try_start_a .. :try_end_10f} :catch_110

    .line 143
    return-void

    .line 162
    :catch_110
    move-exception p1

    .line 163
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V

    .line 165
    :goto_114
    return-void

    .line 115
    :cond_115
    :goto_115
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V

    .line 116
    return-void
.end method
