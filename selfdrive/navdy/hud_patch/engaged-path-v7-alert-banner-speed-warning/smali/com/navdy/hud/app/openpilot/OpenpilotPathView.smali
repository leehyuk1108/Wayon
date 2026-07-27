.class public final Lcom/navdy/hud/app/openpilot/OpenpilotPathView;
.super Landroid/view/View;
.source "OpenpilotPathView.java"


# static fields
.field private static final COLOR_GREEN:I = -0xff19ba

.field private static final COLOR_LANE_CLEAR:I = -0x1

.field private static final COLOR_LANE_DANGER:I = -0xdfd8

.field private static final COLOR_VEHICLE_FUSED:I = -0xff1a01

.field private static final COLOR_VEHICLE_RADAR:I = -0x22000001

.field private static final COLOR_VEHICLE_VISION:I = -0xff19ba

.field private static final DASH_FRAME_MS:J = 0x42L

.field private static final LANE_DASH_CYCLE:F = 80.0f

.field private static final LANE_DASH_PATTERN:[F

.field private static final LANE_RISK_FILTER_STEPS:I = 0xa

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

.field private final laneRiskFilters:[Landroid/graphics/LightingColorFilter;

.field private laneRiskLeft:F

.field private laneRiskRight:F

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
    .locals 1

    .line 27
    const/4 v0, 0x2

    new-array v0, v0, [F

    fill-array-data v0, :array_0

    sput-object v0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->LANE_DASH_PATTERN:[F

    return-void

    nop

    :array_0
    .array-data 4
        0x42600000    # 56.0f
        0x41c00000    # 24.0f
    .end array-data
.end method

.method public constructor <init>(Landroid/content/Context;)V
    .locals 10

    .line 72
    invoke-direct {p0, p1}, Landroid/view/View;-><init>(Landroid/content/Context;)V

    .line 33
    new-instance v0, Landroid/graphics/Paint;

    const/4 v1, 0x1

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    .line 34
    new-instance v2, Landroid/graphics/Paint;

    invoke-direct {v2, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    .line 35
    new-instance v2, Landroid/graphics/Paint;

    invoke-direct {v2, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    .line 36
    new-instance v2, Landroid/graphics/Paint;

    invoke-direct {v2, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    .line 37
    new-instance v2, Landroid/graphics/Paint;

    invoke-direct {v2, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    .line 38
    new-instance v2, Landroid/graphics/Paint;

    const/4 v3, 0x3

    invoke-direct {v2, v3}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    .line 40
    const/16 v2, 0xb

    new-array v2, v2, [Landroid/graphics/LightingColorFilter;

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskFilters:[Landroid/graphics/LightingColorFilter;

    .line 42
    new-instance v2, Landroid/graphics/LightingColorFilter;

    const/4 v4, -0x1

    const/4 v5, 0x0

    invoke-direct {v2, v4, v5}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRadarFilter:Landroid/graphics/LightingColorFilter;

    .line 43
    new-instance v2, Landroid/graphics/LightingColorFilter;

    const v6, -0xff19ba

    invoke-direct {v2, v6, v5}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleVisionFilter:Landroid/graphics/LightingColorFilter;

    .line 45
    new-instance v2, Landroid/graphics/LightingColorFilter;

    const v7, -0xff1a01

    invoke-direct {v2, v7, v5}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFusedFilter:Landroid/graphics/LightingColorFilter;

    .line 50
    new-array v2, v5, [F

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeft:[F

    .line 52
    new-array v2, v5, [F

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    .line 55
    new-array v2, v5, [F

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    .line 58
    new-array v2, v5, [F

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRight:[F

    .line 60
    new-array v2, v5, [F

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 61
    new-array v2, v5, [F

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    .line 62
    new-array v2, v5, [F

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    .line 64
    new-array v2, v5, [F

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    .line 66
    new-array v2, v5, [F

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    .line 74
    sget-object v2, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v0, v2}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 75
    sget-object v2, Landroid/graphics/Paint$Cap;->ROUND:Landroid/graphics/Paint$Cap;

    invoke-virtual {v0, v2}, Landroid/graphics/Paint;->setStrokeCap(Landroid/graphics/Paint$Cap;)V

    .line 76
    sget-object v2, Landroid/graphics/Paint$Join;->ROUND:Landroid/graphics/Paint$Join;

    invoke-virtual {v0, v2}, Landroid/graphics/Paint;->setStrokeJoin(Landroid/graphics/Paint$Join;)V

    .line 77
    const v2, 0x404ccccd    # 3.2f

    invoke-virtual {v0, v2}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 78
    const/4 v0, 0x0

    :goto_0
    const/16 v2, 0xa

    if-gt v0, v2, :cond_0

    .line 79
    int-to-float v2, v0

    const/high16 v7, 0x41200000    # 10.0f

    div-float/2addr v2, v7

    .line 80
    iget-object v7, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskFilters:[Landroid/graphics/LightingColorFilter;

    new-instance v8, Landroid/graphics/LightingColorFilter;

    const v9, -0xdfd8

    invoke-static {v4, v9, v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->blendColor(IIF)I

    move-result v2

    invoke-direct {v8, v2, v5}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    aput-object v8, v7, v0

    .line 78
    add-int/lit8 v0, v0, 0x1

    goto :goto_0

    .line 84
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    sget-object v2, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v0, v2}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 85
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    sget-object v2, Landroid/graphics/Paint$Cap;->ROUND:Landroid/graphics/Paint$Cap;

    invoke-virtual {v0, v2}, Landroid/graphics/Paint;->setStrokeCap(Landroid/graphics/Paint$Cap;)V

    .line 86
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    sget-object v2, Landroid/graphics/Paint$Join;->ROUND:Landroid/graphics/Paint$Join;

    invoke-virtual {v0, v2}, Landroid/graphics/Paint;->setStrokeJoin(Landroid/graphics/Paint$Join;)V

    .line 87
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    const v2, 0x40333333    # 2.8f

    invoke-virtual {v0, v2}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 88
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    const/16 v2, 0x73

    invoke-virtual {v0, v2}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 90
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {v0, v6}, Landroid/graphics/Paint;->setColor(I)V

    .line 91
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    sget-object v2, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v0, v2}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 92
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    sget-object v2, Landroid/graphics/Paint$Join;->ROUND:Landroid/graphics/Paint$Join;

    invoke-virtual {v0, v2}, Landroid/graphics/Paint;->setStrokeJoin(Landroid/graphics/Paint$Join;)V

    .line 93
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    const v2, 0x3fe66666    # 1.8f

    invoke-virtual {v0, v2}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 95
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    sget-object v2, Landroid/graphics/Paint$Style;->FILL:Landroid/graphics/Paint$Style;

    invoke-virtual {v0, v2}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 97
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    sget-object v2, Landroid/graphics/Paint$Style;->FILL:Landroid/graphics/Paint$Style;

    invoke-virtual {v0, v2}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 98
    const-string v0, "navdy_vehicle_marker"

    invoke-direct {p0, p1, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v0

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleMarkerBitmap:Landroid/graphics/Bitmap;

    .line 99
    const/4 v0, 0x6

    new-array v2, v0, [Landroid/graphics/Bitmap;

    .line 100
    const-string v4, "navdy_vehicle_marker_left_4"

    invoke-direct {p0, p1, v4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v4

    aput-object v4, v2, v5

    .line 101
    const-string v4, "navdy_vehicle_marker_left_8"

    invoke-direct {p0, p1, v4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v4

    aput-object v4, v2, v1

    .line 102
    const-string v4, "navdy_vehicle_marker_left_12"

    invoke-direct {p0, p1, v4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v4

    const/4 v6, 0x2

    aput-object v4, v2, v6

    .line 103
    const-string v4, "navdy_vehicle_marker_left_16"

    invoke-direct {p0, p1, v4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v4

    aput-object v4, v2, v3

    .line 104
    const-string v4, "navdy_vehicle_marker_left_20"

    invoke-direct {p0, p1, v4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v4

    const/4 v7, 0x4

    aput-object v4, v2, v7

    .line 105
    const-string v4, "navdy_vehicle_marker_left_24"

    invoke-direct {p0, p1, v4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v4

    const/4 v8, 0x5

    aput-object v4, v2, v8

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleLeftMarkerBitmaps:[Landroid/graphics/Bitmap;

    .line 107
    new-array v0, v0, [Landroid/graphics/Bitmap;

    .line 108
    const-string v2, "navdy_vehicle_marker_right_4"

    invoke-direct {p0, p1, v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v2

    aput-object v2, v0, v5

    .line 109
    const-string v2, "navdy_vehicle_marker_right_8"

    invoke-direct {p0, p1, v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v2

    aput-object v2, v0, v1

    .line 110
    const-string v1, "navdy_vehicle_marker_right_12"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v1

    aput-object v1, v0, v6

    .line 111
    const-string v1, "navdy_vehicle_marker_right_16"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v1

    aput-object v1, v0, v3

    .line 112
    const-string v1, "navdy_vehicle_marker_right_20"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v1

    aput-object v1, v0, v7

    .line 113
    const-string v1, "navdy_vehicle_marker_right_24"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object p1

    aput-object p1, v0, v8

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRightMarkerBitmaps:[Landroid/graphics/Bitmap;

    .line 115
    invoke-virtual {p0, v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setWillNotDraw(Z)V

    .line 116
    const/16 p1, 0x8

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setVisibility(I)V

    .line 117
    return-void
.end method

.method private static blendColor(IIF)I
    .locals 4

    .line 365
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p2

    .line 366
    shr-int/lit8 v0, p0, 0x10

    and-int/lit16 v0, v0, 0xff

    int-to-float v0, v0

    const/high16 v1, 0x3f800000    # 1.0f

    sub-float/2addr v1, p2

    mul-float v0, v0, v1

    shr-int/lit8 v2, p1, 0x10

    and-int/lit16 v2, v2, 0xff

    int-to-float v2, v2

    mul-float v2, v2, p2

    add-float/2addr v0, v2

    invoke-static {v0}, Ljava/lang/Math;->round(F)I

    move-result v0

    .line 368
    shr-int/lit8 v2, p0, 0x8

    and-int/lit16 v2, v2, 0xff

    int-to-float v2, v2

    mul-float v2, v2, v1

    shr-int/lit8 v3, p1, 0x8

    and-int/lit16 v3, v3, 0xff

    int-to-float v3, v3

    mul-float v3, v3, p2

    add-float/2addr v2, v3

    invoke-static {v2}, Ljava/lang/Math;->round(F)I

    move-result v2

    .line 370
    and-int/lit16 p0, p0, 0xff

    int-to-float p0, p0

    mul-float p0, p0, v1

    and-int/lit16 p1, p1, 0xff

    int-to-float p1, p1

    mul-float p1, p1, p2

    add-float/2addr p0, p1

    invoke-static {p0}, Ljava/lang/Math;->round(F)I

    move-result p0

    .line 371
    const/high16 p1, -0x1000000

    shl-int/lit8 p2, v0, 0x10

    or-int/2addr p1, p2

    shl-int/lit8 p2, v2, 0x8

    or-int/2addr p1, p2

    or-int/2addr p0, p1

    return p0
.end method

.method private static clamp01(F)F
    .locals 1

    .line 361
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

    .line 337
    const/4 v0, 0x0

    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 338
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    .line 339
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeft:[F

    .line 340
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    .line 341
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    .line 342
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRight:[F

    .line 343
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    .line 344
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    .line 345
    new-array v0, v0, [F

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    .line 346
    const/4 v0, 0x0

    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftProb:F

    .line 347
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftProb:F

    .line 348
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskLeft:F

    .line 349
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightProb:F

    .line 350
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskRight:F

    .line 351
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightProb:F

    .line 352
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeftProb:F

    .line 353
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRightProb:F

    .line 354
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    .line 355
    const-wide/16 v0, 0x0

    iput-wide v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    .line 356
    const/16 v0, 0x8

    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setVisibility(I)V

    .line 357
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->invalidate()V

    .line 358
    return-void
.end method

.method private drawLane(Landroid/graphics/Canvas;[FFF)V
    .locals 2

    .line 230
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_1

    const v0, 0x3d4ccccd    # 0.05f

    cmpg-float v0, p3, v0

    if-gez v0, :cond_0

    goto :goto_0

    .line 233
    :cond_0
    nop

    .line 234
    invoke-static {p4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p4

    const/high16 v0, 0x41200000    # 10.0f

    mul-float p4, p4, v0

    invoke-static {p4}, Ljava/lang/Math;->round(F)I

    move-result p4

    const/4 v0, 0x0

    invoke-static {v0, p4}, Ljava/lang/Math;->max(II)I

    move-result p4

    .line 233
    const/16 v0, 0xa

    invoke-static {v0, p4}, Ljava/lang/Math;->min(II)I

    move-result p4

    .line 235
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskFilters:[Landroid/graphics/LightingColorFilter;

    aget-object p4, v1, p4

    invoke-virtual {v0, p4}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 236
    iget-object p4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    const/high16 v0, 0x43610000    # 225.0f

    mul-float p3, p3, v0

    const/high16 v0, 0x41f00000    # 30.0f

    add-float/2addr p3, v0

    float-to-int p3, p3

    invoke-virtual {p4, p3}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 237
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object p2

    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p2, p3}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 238
    return-void

    .line 231
    :cond_1
    :goto_0
    return-void
.end method

.method private drawRoadEdge(Landroid/graphics/Canvas;[FF)V
    .locals 2

    .line 241
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_1

    const/high16 v0, 0x3f000000    # 0.5f

    cmpg-float v0, p3, v0

    if-gez v0, :cond_0

    goto :goto_0

    .line 244
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    const/high16 v1, 0x43520000    # 210.0f

    mul-float p3, p3, v1

    const/high16 v1, 0x41c80000    # 25.0f

    add-float/2addr p3, v1

    float-to-int p3, p3

    invoke-virtual {v0, p3}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 245
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object p2

    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p2, p3}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 246
    return-void

    .line 242
    :cond_1
    :goto_0
    return-void
.end method

.method private drawVehicle(Landroid/graphics/Canvas;FFFIIF)V
    .locals 5

    .line 276
    const/high16 v0, 0x42a00000    # 80.0f

    div-float/2addr p4, v0

    const/high16 v0, 0x3f800000    # 1.0f

    sub-float/2addr v0, p4

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p4

    .line 277
    const/high16 v0, 0x423a0000    # 46.5f

    mul-float p4, p4, v0

    const/high16 v0, 0x41400000    # 12.0f

    add-float/2addr p4, v0

    .line 278
    const v0, 0x3fc66666    # 1.55f

    mul-float v0, v0, p4

    .line 280
    const/4 v1, 0x2

    const/16 v2, 0xff

    if-ne p5, v1, :cond_0

    .line 281
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    const v1, -0xff1a01

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColor(I)V

    .line 282
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFusedFilter:Landroid/graphics/LightingColorFilter;

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 283
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    invoke-virtual {p5, v2}, Landroid/graphics/Paint;->setAlpha(I)V

    goto :goto_0

    .line 284
    :cond_0
    const/4 v1, 0x1

    if-ne p5, v1, :cond_1

    .line 285
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    const v1, -0xff19ba

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColor(I)V

    .line 286
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleVisionFilter:Landroid/graphics/LightingColorFilter;

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 287
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    invoke-virtual {p5, v2}, Landroid/graphics/Paint;->setAlpha(I)V

    goto :goto_0

    .line 289
    :cond_1
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    const v1, -0x22000001

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColor(I)V

    .line 290
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRadarFilter:Landroid/graphics/LightingColorFilter;

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 291
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    const/16 v1, 0xdd

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 294
    :goto_0
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

    .line 299
    invoke-direct {p0, p7, p6, p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleMarkerForYaw(FIF)Landroid/graphics/Bitmap;

    move-result-object p2

    .line 300
    if-eqz p2, :cond_2

    .line 301
    const/4 p3, 0x0

    iget-object p4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p2, p3, p5, p4}, Landroid/graphics/Canvas;->drawBitmap(Landroid/graphics/Bitmap;Landroid/graphics/Rect;Landroid/graphics/RectF;Landroid/graphics/Paint;)V

    goto :goto_1

    .line 303
    :cond_2
    const p2, 0x3e75c28f    # 0.24f

    mul-float p4, p4, p2

    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p5, p4, p4, p2}, Landroid/graphics/Canvas;->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V

    .line 305
    :goto_1
    return-void
.end method

.method private drawVehicles(Landroid/graphics/Canvas;)V
    .locals 12

    .line 266
    const/4 v0, 0x0

    :goto_0
    add-int/lit8 v1, v0, 0x5

    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    array-length v3, v2

    if-ge v1, v3, :cond_0

    .line 267
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

    .line 266
    add-int/lit8 v0, v0, 0x6

    goto :goto_0

    .line 271
    :cond_0
    return-void
.end method

.method private static linePath([F)Landroid/graphics/Path;
    .locals 4

    .line 375
    new-instance v0, Landroid/graphics/Path;

    invoke-direct {v0}, Landroid/graphics/Path;-><init>()V

    .line 376
    const/4 v1, 0x0

    aget v1, p0, v1

    const/4 v2, 0x1

    aget v2, p0, v2

    invoke-virtual {v0, v1, v2}, Landroid/graphics/Path;->moveTo(FF)V

    .line 377
    const/4 v1, 0x2

    :goto_0
    array-length v2, p0

    if-ge v1, v2, :cond_0

    .line 378
    aget v2, p0, v1

    add-int/lit8 v3, v1, 0x1

    aget v3, p0, v3

    invoke-virtual {v0, v2, v3}, Landroid/graphics/Path;->lineTo(FF)V

    .line 377
    add-int/lit8 v1, v1, 0x2

    goto :goto_0

    .line 380
    :cond_0
    return-object v0
.end method

.method private loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;
    .locals 2

    .line 120
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->getResources()Landroid/content/res/Resources;

    move-result-object v0

    .line 121
    invoke-virtual {p1}, Landroid/content/Context;->getPackageName()Ljava/lang/String;

    move-result-object p1

    .line 120
    const-string v1, "drawable"

    invoke-virtual {v0, p2, v1, p1}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I

    move-result p1

    .line 122
    if-nez p1, :cond_0

    const/4 p1, 0x0

    goto :goto_0

    :cond_0
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->getResources()Landroid/content/res/Resources;

    move-result-object p2

    invoke-static {p2, p1}, Landroid/graphics/BitmapFactory;->decodeResource(Landroid/content/res/Resources;I)Landroid/graphics/Bitmap;

    move-result-object p1

    :goto_0
    return-object p1
.end method

.method private static readPoints(Lorg/json/JSONArray;)[F
    .locals 4

    .line 384
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

    .line 387
    :cond_0
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    new-array v1, v1, [F

    .line 388
    nop

    :goto_0
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v2

    if-ge v0, v2, :cond_1

    .line 389
    const-wide/16 v2, 0x0

    invoke-virtual {p0, v0, v2, v3}, Lorg/json/JSONArray;->optDouble(ID)D

    move-result-wide v2

    double-to-float v2, v2

    aput v2, v1, v0

    .line 388
    add-int/lit8 v0, v0, 0x1

    goto :goto_0

    .line 391
    :cond_1
    return-object v1

    .line 385
    :cond_2
    :goto_1
    new-array p0, v0, [F

    return-object p0
.end method

.method private static readVehicles(Lorg/json/JSONArray;)[F
    .locals 12

    .line 395
    const/4 v0, 0x0

    if-eqz p0, :cond_9

    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    if-nez v1, :cond_0

    goto/16 :goto_5

    .line 398
    :cond_0
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    mul-int/lit8 v1, v1, 0x6

    new-array v2, v1, [F

    .line 399
    nop

    .line 400
    const/4 v3, 0x0

    const/4 v4, 0x0

    :goto_0
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v5

    if-ge v3, v5, :cond_7

    .line 401
    invoke-virtual {p0, v3}, Lorg/json/JSONArray;->optJSONObject(I)Lorg/json/JSONObject;

    move-result-object v5

    .line 402
    if-nez v5, :cond_1

    .line 403
    goto/16 :goto_4

    .line 405
    :cond_1
    const-string v6, "source"

    const-string v7, "radar"

    invoke-virtual {v5, v6, v7}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v6

    .line 406
    const-string v7, "fused"

    invoke-virtual {v7, v6}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v7

    const/4 v8, 0x1

    if-eqz v7, :cond_2

    const/4 v6, 0x2

    goto :goto_1

    :cond_2
    const-string v7, "vision"

    invoke-virtual {v7, v6}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v6

    if-eqz v6, :cond_3

    const/4 v6, 0x1

    goto :goto_1

    :cond_3
    const/4 v6, 0x0

    .line 407
    :goto_1
    const-string v7, "lane"

    const-string v9, "center"

    invoke-virtual {v5, v7, v9}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v7

    .line 408
    const-string v9, "left"

    invoke-virtual {v9, v7}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v9

    if-eqz v9, :cond_4

    const/4 v8, -0x1

    goto :goto_2

    :cond_4
    const-string v9, "right"

    invoke-virtual {v9, v7}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v7

    if-eqz v7, :cond_5

    goto :goto_2

    :cond_5
    const/4 v8, 0x0

    .line 409
    :goto_2
    add-int/lit8 v7, v4, 0x1

    const-string v9, "screenX"

    const-wide/high16 v10, 0x4064000000000000L    # 160.0

    invoke-virtual {v5, v9, v10, v11}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v9

    double-to-float v9, v9

    aput v9, v2, v4

    .line 410
    add-int/lit8 v4, v7, 0x1

    const-string v9, "screenY"

    const-wide/high16 v10, 0x4020000000000000L    # 8.0

    invoke-virtual {v5, v9, v10, v11}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v9

    double-to-float v9, v9

    aput v9, v2, v7

    .line 411
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

    .line 412
    add-int/lit8 v4, v7, 0x1

    int-to-float v6, v6

    aput v6, v2, v7

    .line 413
    add-int/lit8 v6, v4, 0x1

    int-to-float v7, v8

    aput v7, v2, v4

    .line 414
    add-int/lit8 v4, v6, 0x1

    const-string v7, "yawDeg"

    invoke-virtual {v5, v7}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result v8

    if-eqz v8, :cond_6

    .line 415
    const-wide/16 v8, 0x0

    invoke-virtual {v5, v7, v8, v9}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v7

    double-to-float v5, v7

    goto :goto_3

    :cond_6
    const/high16 v5, 0x7fc00000    # Float.NaN

    :goto_3
    aput v5, v2, v6

    .line 400
    :goto_4
    add-int/lit8 v3, v3, 0x1

    goto/16 :goto_0

    .line 417
    :cond_7
    if-ne v4, v1, :cond_8

    .line 418
    return-object v2

    .line 420
    :cond_8
    new-array p0, v4, [F

    .line 421
    invoke-static {v2, v0, p0, v0, v4}, Ljava/lang/System;->arraycopy(Ljava/lang/Object;ILjava/lang/Object;II)V

    .line 422
    return-object p0

    .line 396
    :cond_9
    :goto_5
    new-array p0, v0, [F

    return-object p0
.end method

.method private updateDashPhase()V
    .locals 7

    .line 249
    invoke-static {}, Landroid/os/SystemClock;->uptimeMillis()J

    move-result-wide v0

    .line 250
    iget-wide v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    const-wide/16 v4, 0x0

    cmp-long v6, v2, v4

    if-nez v6, :cond_0

    .line 251
    iput-wide v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    .line 252
    return-void

    .line 255
    :cond_0
    sub-long v2, v0, v2

    const-wide/16 v4, 0x96

    invoke-static {v2, v3, v4, v5}, Ljava/lang/Math;->min(JJ)J

    move-result-wide v2

    .line 256
    iput-wide v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    .line 257
    iget v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    const/high16 v1, 0x3f800000    # 1.0f

    cmpg-float v1, v0, v1

    if-gtz v1, :cond_1

    .line 258
    return-void

    .line 261
    :cond_1
    const v1, 0x3f4ccccd    # 0.8f

    mul-float v0, v0, v1

    const/high16 v1, 0x41900000    # 18.0f

    invoke-static {v1, v0}, Ljava/lang/Math;->max(FF)F

    move-result v0

    const/high16 v1, 0x42a00000    # 80.0f

    invoke-static {v1, v0}, Ljava/lang/Math;->min(FF)F

    move-result v0

    .line 262
    iget v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashPhase:F

    long-to-float v2, v2

    mul-float v2, v2, v0

    const/high16 v0, 0x447a0000    # 1000.0f

    div-float/2addr v2, v0

    add-float/2addr v4, v2

    rem-float/2addr v4, v1

    iput v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashPhase:F

    .line 263
    return-void
.end method

.method private static validLine([F)Z
    .locals 2

    .line 426
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

.method private vehicleMarkerForYaw(FIF)Landroid/graphics/Bitmap;
    .locals 4

    .line 308
    invoke-static {p1}, Ljava/lang/Float;->isNaN(F)Z

    move-result v0

    const/4 v1, 0x0

    const/high16 v2, 0x40800000    # 4.0f

    const/high16 v3, 0x41c00000    # 24.0f

    if-eqz v0, :cond_5

    .line 309
    const/high16 p1, 0x43200000    # 160.0f

    sub-float/2addr p3, p1

    invoke-static {p3}, Ljava/lang/Math;->abs(F)F

    move-result p1

    .line 311
    cmpg-float p3, p1, v3

    if-ltz p3, :cond_4

    if-nez p2, :cond_0

    goto :goto_0

    .line 313
    :cond_0
    const/high16 p3, 0x42400000    # 48.0f

    cmpg-float p3, p1, p3

    if-gez p3, :cond_1

    .line 314
    const/high16 p1, 0x40800000    # 4.0f

    goto :goto_1

    .line 315
    :cond_1
    const/high16 p3, 0x42900000    # 72.0f

    cmpg-float p3, p1, p3

    if-gez p3, :cond_2

    .line 316
    const/high16 p1, 0x41000000    # 8.0f

    goto :goto_1

    .line 317
    :cond_2
    const/high16 p3, 0x42d00000    # 104.0f

    cmpg-float p1, p1, p3

    if-gez p1, :cond_3

    .line 318
    const/high16 p1, 0x41400000    # 12.0f

    goto :goto_1

    .line 320
    :cond_3
    const/high16 p1, 0x41800000    # 16.0f

    goto :goto_1

    .line 312
    :cond_4
    :goto_0
    const/4 p1, 0x0

    .line 322
    :goto_1
    if-gez p2, :cond_5

    neg-float p1, p1

    .line 325
    :cond_5
    invoke-static {p1}, Ljava/lang/Math;->abs(F)F

    move-result p2

    invoke-static {v3, p2}, Ljava/lang/Math;->min(FF)F

    move-result p2

    .line 326
    const/high16 p3, 0x40000000    # 2.0f

    cmpg-float p3, p2, p3

    if-gez p3, :cond_6

    .line 327
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleMarkerBitmap:Landroid/graphics/Bitmap;

    return-object p1

    .line 329
    :cond_6
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

    .line 330
    cmpg-float p1, p1, v1

    if-gez p1, :cond_7

    .line 331
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleLeftMarkerBitmaps:[Landroid/graphics/Bitmap;

    aget-object p1, p1, p2

    goto :goto_2

    .line 332
    :cond_7
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRightMarkerBitmaps:[Landroid/graphics/Bitmap;

    aget-object p1, p1, p2

    .line 333
    :goto_2
    if-nez p1, :cond_8

    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleMarkerBitmap:Landroid/graphics/Bitmap;

    :cond_8
    return-object p1
.end method


# virtual methods
.method protected onDraw(Landroid/graphics/Canvas;)V
    .locals 5

    .line 199
    invoke-super {p0, p1}, Landroid/view/View;->onDraw(Landroid/graphics/Canvas;)V

    .line 200
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_3

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-nez v0, :cond_0

    goto/16 :goto_1

    .line 204
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    .line 205
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    array-length v1, v1

    add-int/lit8 v1, v1, -0x2

    :goto_0
    if-ltz v1, :cond_1

    .line 206
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    aget v3, v2, v1

    add-int/lit8 v4, v1, 0x1

    aget v2, v2, v4

    invoke-virtual {v0, v3, v2}, Landroid/graphics/Path;->lineTo(FF)V

    .line 205
    add-int/lit8 v1, v1, -0x2

    goto :goto_0

    .line 208
    :cond_1
    invoke-virtual {v0}, Landroid/graphics/Path;->close()V

    .line 209
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 210
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 211
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 213
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeftProb:F

    invoke-direct {p0, p1, v0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawRoadEdge(Landroid/graphics/Canvas;[FF)V

    .line 214
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRightProb:F

    invoke-direct {p0, p1, v0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawRoadEdge(Landroid/graphics/Canvas;[FF)V

    .line 216
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->updateDashPhase()V

    .line 217
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    new-instance v1, Landroid/graphics/DashPathEffect;

    sget-object v2, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->LANE_DASH_PATTERN:[F

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashPhase:F

    invoke-direct {v1, v2, v3}, Landroid/graphics/DashPathEffect;-><init>([FF)V

    invoke-virtual {v0, v1}, Landroid/graphics/Paint;->setPathEffect(Landroid/graphics/PathEffect;)Landroid/graphics/PathEffect;

    .line 218
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeft:[F

    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftProb:F

    const/4 v2, 0x0

    invoke-direct {p0, p1, v0, v1, v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLane(Landroid/graphics/Canvas;[FFF)V

    .line 219
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftProb:F

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskLeft:F

    invoke-direct {p0, p1, v0, v1, v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLane(Landroid/graphics/Canvas;[FFF)V

    .line 220
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightProb:F

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskRight:F

    invoke-direct {p0, p1, v0, v1, v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLane(Landroid/graphics/Canvas;[FFF)V

    .line 221
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRight:[F

    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightProb:F

    invoke-direct {p0, p1, v0, v1, v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLane(Landroid/graphics/Canvas;[FFF)V

    .line 222
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawVehicles(Landroid/graphics/Canvas;)V

    .line 224
    iget p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    const/high16 v0, 0x3f800000    # 1.0f

    cmpl-float p1, p1, v0

    if-lez p1, :cond_2

    .line 225
    const-wide/16 v0, 0x42

    invoke-virtual {p0, v0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->postInvalidateDelayed(J)V

    .line 227
    :cond_2
    return-void

    .line 201
    :cond_3
    :goto_1
    return-void
.end method

.method protected onSizeChanged(IIII)V
    .locals 8

    .line 187
    invoke-super {p0, p1, p2, p3, p4}, Landroid/view/View;->onSizeChanged(IIII)V

    .line 188
    int-to-float p1, p2

    .line 189
    new-instance p2, Landroid/graphics/LinearGradient;

    const/4 v1, 0x0

    const/4 v2, 0x0

    const/4 v3, 0x0

    const v5, 0x55ffffff

    const v6, -0x1

    sget-object v7, Landroid/graphics/Shader$TileMode;->CLAMP:Landroid/graphics/Shader$TileMode;

    move-object v0, p2

    move v4, p1

    invoke-direct/range {v0 .. v7}, Landroid/graphics/LinearGradient;-><init>(FFFFIILandroid/graphics/Shader$TileMode;)V

    .line 191
    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    invoke-virtual {p3, p2}, Landroid/graphics/Paint;->setShader(Landroid/graphics/Shader;)Landroid/graphics/Shader;

    .line 192
    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p3, p2}, Landroid/graphics/Paint;->setShader(Landroid/graphics/Shader;)Landroid/graphics/Shader;

    .line 193
    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    new-instance p3, Landroid/graphics/LinearGradient;

    const v5, 0x1100e646

    const v6, -0x66ff19ba

    sget-object v7, Landroid/graphics/Shader$TileMode;->CLAMP:Landroid/graphics/Shader$TileMode;

    move-object v0, p3

    invoke-direct/range {v0 .. v7}, Landroid/graphics/LinearGradient;-><init>(FFFFIILandroid/graphics/Shader$TileMode;)V

    invoke-virtual {p2, p3}, Landroid/graphics/Paint;->setShader(Landroid/graphics/Shader;)Landroid/graphics/Shader;

    .line 195
    return-void
.end method

.method public updatePayload(Ljava/lang/String;Z)V
    .locals 10

    .line 126
    const-string v0, "navPathLeft"

    const-string v1, "navLaneRiskRight"

    const-string v2, "navLaneRiskLeft"

    const-string v3, "navVehicles"

    if-eqz p2, :cond_8

    if-nez p1, :cond_0

    goto/16 :goto_2

    .line 132
    :cond_0
    :try_start_0
    new-instance p2, Lorg/json/JSONObject;

    invoke-direct {p2, p1}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    .line 133
    const-string p1, "vEgoKph"

    const-wide/16 v4, 0x0

    invoke-virtual {p2, p1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v6

    double-to-float p1, v6

    const/4 v6, 0x0

    invoke-static {v6, p1}, Ljava/lang/Math;->max(FF)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    .line 134
    invoke-virtual {p2, v3}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result p1

    if-eqz p1, :cond_1

    .line 135
    invoke-virtual {p2, v3}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object p1

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readVehicles(Lorg/json/JSONArray;)[F

    move-result-object p1

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    .line 137
    :cond_1
    invoke-virtual {p2, v2}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result p1

    if-eqz p1, :cond_2

    .line 138
    invoke-virtual {p2, v2, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v2

    double-to-float p1, v2

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskLeft:F

    .line 140
    :cond_2
    invoke-virtual {p2, v1}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result p1

    if-eqz p1, :cond_3

    .line 141
    invoke-virtual {p2, v1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v1

    double-to-float p1, v1

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskRight:F

    .line 143
    :cond_3
    invoke-virtual {p2, v0}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result p1

    if-nez p1, :cond_5

    .line 144
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->getVisibility()I

    move-result p1

    if-nez p1, :cond_4

    .line 145
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->invalidate()V

    .line 147
    :cond_4
    return-void

    .line 150
    :cond_5
    invoke-virtual {p2, v0}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object p1

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object p1

    .line 151
    const-string v0, "navPathRight"

    invoke-virtual {p2, v0}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v0

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v0

    .line 152
    const-string v1, "navLaneFarLeft"

    invoke-virtual {p2, v1}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v1

    invoke-static {v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v1

    .line 153
    const-string v2, "navLaneLeft"

    invoke-virtual {p2, v2}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v2

    invoke-static {v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v2

    .line 154
    const-string v3, "navLaneRight"

    invoke-virtual {p2, v3}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v3

    invoke-static {v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v3

    .line 155
    const-string v6, "navLaneFarRight"

    invoke-virtual {p2, v6}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v6

    invoke-static {v6}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v6

    .line 156
    const-string v7, "navRoadEdgeLeft"

    invoke-virtual {p2, v7}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v7

    invoke-static {v7}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v7

    .line 157
    const-string v8, "navRoadEdgeRight"

    invoke-virtual {p2, v8}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v8

    invoke-static {v8}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v8

    .line 158
    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v9

    if-eqz v9, :cond_7

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v9

    if-eqz v9, :cond_7

    .line 159
    invoke-static {v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v9

    if-eqz v9, :cond_7

    invoke-static {v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v9

    if-nez v9, :cond_6

    goto :goto_0

    .line 164
    :cond_6
    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 165
    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    .line 166
    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeft:[F

    .line 167
    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    .line 168
    iput-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    .line 169
    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRight:[F

    .line 170
    iput-object v7, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    .line 171
    iput-object v8, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    .line 172
    const-string p1, "navLaneFarLeftProb"

    invoke-virtual {p2, p1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p1, v0

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftProb:F

    .line 173
    const-string p1, "navLaneLeftProb"

    invoke-virtual {p2, p1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p1, v0

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftProb:F

    .line 174
    const-string p1, "navLaneRightProb"

    invoke-virtual {p2, p1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p1, v0

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightProb:F

    .line 175
    const-string p1, "navLaneFarRightProb"

    invoke-virtual {p2, p1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p1, v0

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightProb:F

    .line 176
    const-string p1, "navRoadEdgeLeftProb"

    invoke-virtual {p2, p1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p1, v0

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeftProb:F

    .line 177
    const-string p1, "navRoadEdgeRightProb"

    invoke-virtual {p2, p1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide p1

    double-to-float p1, p1

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRightProb:F

    .line 178
    const/4 p1, 0x0

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setVisibility(I)V

    .line 179
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->invalidate()V

    .line 182
    goto :goto_1

    .line 160
    :cond_7
    :goto_0
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 161
    return-void

    .line 180
    :catch_0
    move-exception p1

    .line 181
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V

    .line 183
    :goto_1
    return-void

    .line 127
    :cond_8
    :goto_2
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V

    .line 128
    return-void
.end method
