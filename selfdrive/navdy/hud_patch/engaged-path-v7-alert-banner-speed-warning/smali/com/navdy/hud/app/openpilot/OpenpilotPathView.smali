.class public final Lcom/navdy/hud/app/openpilot/OpenpilotPathView;
.super Landroid/view/View;
.source "OpenpilotPathView.java"

# interfaces
.implements Ljava/lang/Runnable;


# static fields
.field private static final COLOR_GREEN:I = -0xff19ba

.field private static final COLOR_LANE_CENTER:I = -0x2bc5

.field private static final COLOR_LANE_CLEAR:I = -0x1

.field private static final COLOR_LANE_DANGER:I = -0xdfd8

.field private static final COLOR_VEHICLE_LONGITUDINAL_LEAD:I = -0xff1a01

.field private static final COLOR_VEHICLE_RADAR:I = -0x22000001

.field private static final COLOR_VEHICLE_VISION:I = -0xff19ba

.field private static final DASH_FRAME_MS:J = 0x42L

.field private static final LANE_DASH_CYCLE:F = 80.0f

.field private static final LANE_DASH_PATTERN:[F

.field private static final LANE_RISK_FILTER_STEPS:I = 0xa

.field private static final ROAD_EDGE_MIN_CONFIDENCE:F = 0.5f


# instance fields
.field private final centerLaneRiskFilters:[Landroid/graphics/LightingColorFilter;

.field private dashFrameScheduled:Z

.field private dashPhase:F

.field private laneDashEffect:Landroid/graphics/DashPathEffect;

.field private laneFarLeft:[F

.field private laneFarLeftProb:F

.field private laneFarLeftType:Ljava/lang/String;

.field private laneFarRight:[F

.field private laneFarRightProb:F

.field private laneFarRightType:Ljava/lang/String;

.field private laneLeft:[F

.field private laneLeftProb:F

.field private laneLeftType:Ljava/lang/String;

.field private final lanePaint:Landroid/graphics/Paint;

.field private laneRight:[F

.field private laneRightProb:F

.field private laneRightType:Ljava/lang/String;

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

.field private final vehicleLongitudinalLeadFilter:Landroid/graphics/LightingColorFilter;

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

    .line 28
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
    .locals 11

    .line 81
    invoke-direct {p0, p1}, Landroid/view/View;-><init>(Landroid/content/Context;)V

    .line 34
    new-instance v0, Landroid/graphics/Paint;

    const/4 v1, 0x1

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    .line 35
    new-instance v0, Landroid/graphics/Paint;

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    .line 36
    new-instance v0, Landroid/graphics/Paint;

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    .line 37
    new-instance v0, Landroid/graphics/Paint;

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    .line 38
    new-instance v0, Landroid/graphics/Paint;

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    .line 39
    new-instance v0, Landroid/graphics/Paint;

    const/4 v2, 0x3

    invoke-direct {v0, v2}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    .line 41
    const/16 v0, 0xb

    new-array v3, v0, [Landroid/graphics/LightingColorFilter;

    iput-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskFilters:[Landroid/graphics/LightingColorFilter;

    .line 43
    new-array v0, v0, [Landroid/graphics/LightingColorFilter;

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->centerLaneRiskFilters:[Landroid/graphics/LightingColorFilter;

    .line 45
    new-instance v0, Landroid/graphics/LightingColorFilter;

    const/4 v3, -0x1

    const/4 v4, 0x0

    invoke-direct {v0, v3, v4}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRadarFilter:Landroid/graphics/LightingColorFilter;

    .line 46
    new-instance v0, Landroid/graphics/LightingColorFilter;

    const v5, -0xff19ba

    invoke-direct {v0, v5, v4}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleVisionFilter:Landroid/graphics/LightingColorFilter;

    .line 48
    new-instance v0, Landroid/graphics/LightingColorFilter;

    const v6, -0xff1a01

    invoke-direct {v0, v6, v4}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleLongitudinalLeadFilter:Landroid/graphics/LightingColorFilter;

    .line 53
    new-array v0, v4, [F

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeft:[F

    .line 55
    const-string v0, "unknown"

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftType:Ljava/lang/String;

    .line 56
    new-array v6, v4, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    .line 58
    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftType:Ljava/lang/String;

    .line 60
    new-array v6, v4, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    .line 62
    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightType:Ljava/lang/String;

    .line 64
    new-array v6, v4, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRight:[F

    .line 66
    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightType:Ljava/lang/String;

    .line 67
    new-array v0, v4, [F

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 68
    new-array v0, v4, [F

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    .line 69
    new-array v0, v4, [F

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    .line 71
    new-array v0, v4, [F

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    .line 73
    new-array v0, v4, [F

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    .line 83
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    sget-object v6, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v0, v6}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 84
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    sget-object v6, Landroid/graphics/Paint$Cap;->ROUND:Landroid/graphics/Paint$Cap;

    invoke-virtual {v0, v6}, Landroid/graphics/Paint;->setStrokeCap(Landroid/graphics/Paint$Cap;)V

    .line 85
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    sget-object v6, Landroid/graphics/Paint$Join;->ROUND:Landroid/graphics/Paint$Join;

    invoke-virtual {v0, v6}, Landroid/graphics/Paint;->setStrokeJoin(Landroid/graphics/Paint$Join;)V

    .line 86
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    const v6, 0x404ccccd    # 3.2f

    invoke-virtual {v0, v6}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 87
    const/4 v0, 0x0

    :goto_0
    const/16 v6, 0xa

    const v7, -0xdfd8

    if-gt v0, v6, :cond_0

    .line 88
    int-to-float v6, v0

    const/high16 v8, 0x41200000    # 10.0f

    div-float/2addr v6, v8

    .line 89
    iget-object v8, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskFilters:[Landroid/graphics/LightingColorFilter;

    new-instance v9, Landroid/graphics/LightingColorFilter;

    invoke-static {v3, v7, v6}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->blendColor(IIF)I

    move-result v10

    invoke-direct {v9, v10, v4}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    aput-object v9, v8, v0

    .line 91
    iget-object v8, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->centerLaneRiskFilters:[Landroid/graphics/LightingColorFilter;

    new-instance v9, Landroid/graphics/LightingColorFilter;

    const/16 v10, -0x2bc5

    invoke-static {v10, v7, v6}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->blendColor(IIF)I

    move-result v6

    invoke-direct {v9, v6, v4}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    aput-object v9, v8, v0

    .line 87
    add-int/lit8 v0, v0, 0x1

    goto :goto_0

    .line 95
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    sget-object v3, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v0, v3}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 96
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    sget-object v3, Landroid/graphics/Paint$Cap;->ROUND:Landroid/graphics/Paint$Cap;

    invoke-virtual {v0, v3}, Landroid/graphics/Paint;->setStrokeCap(Landroid/graphics/Paint$Cap;)V

    .line 97
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    sget-object v3, Landroid/graphics/Paint$Join;->ROUND:Landroid/graphics/Paint$Join;

    invoke-virtual {v0, v3}, Landroid/graphics/Paint;->setStrokeJoin(Landroid/graphics/Paint$Join;)V

    .line 98
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    const v3, 0x40333333    # 2.8f

    invoke-virtual {v0, v3}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 99
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    const/16 v3, 0x73

    invoke-virtual {v0, v3}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 100
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    new-instance v3, Landroid/graphics/LightingColorFilter;

    invoke-direct {v3, v7, v4}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    invoke-virtual {v0, v3}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 102
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {v0, v5}, Landroid/graphics/Paint;->setColor(I)V

    .line 103
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    sget-object v3, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v0, v3}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 104
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    sget-object v3, Landroid/graphics/Paint$Join;->ROUND:Landroid/graphics/Paint$Join;

    invoke-virtual {v0, v3}, Landroid/graphics/Paint;->setStrokeJoin(Landroid/graphics/Paint$Join;)V

    .line 105
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    const v3, 0x3fe66666    # 1.8f

    invoke-virtual {v0, v3}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 107
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    sget-object v3, Landroid/graphics/Paint$Style;->FILL:Landroid/graphics/Paint$Style;

    invoke-virtual {v0, v3}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 109
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    sget-object v3, Landroid/graphics/Paint$Style;->FILL:Landroid/graphics/Paint$Style;

    invoke-virtual {v0, v3}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 110
    const-string v0, "navdy_vehicle_marker"

    invoke-direct {p0, p1, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v0

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleMarkerBitmap:Landroid/graphics/Bitmap;

    .line 111
    const/4 v0, 0x6

    new-array v3, v0, [Landroid/graphics/Bitmap;

    .line 112
    const-string v5, "navdy_vehicle_marker_left_4"

    invoke-direct {p0, p1, v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v5

    aput-object v5, v3, v4

    .line 113
    const-string v5, "navdy_vehicle_marker_left_8"

    invoke-direct {p0, p1, v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v5

    aput-object v5, v3, v1

    .line 114
    const-string v5, "navdy_vehicle_marker_left_12"

    invoke-direct {p0, p1, v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v5

    const/4 v6, 0x2

    aput-object v5, v3, v6

    .line 115
    const-string v5, "navdy_vehicle_marker_left_16"

    invoke-direct {p0, p1, v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v5

    aput-object v5, v3, v2

    .line 116
    const-string v5, "navdy_vehicle_marker_left_20"

    invoke-direct {p0, p1, v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v5

    const/4 v7, 0x4

    aput-object v5, v3, v7

    .line 117
    const-string v5, "navdy_vehicle_marker_left_24"

    invoke-direct {p0, p1, v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v5

    const/4 v8, 0x5

    aput-object v5, v3, v8

    iput-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleLeftMarkerBitmaps:[Landroid/graphics/Bitmap;

    .line 119
    new-array v0, v0, [Landroid/graphics/Bitmap;

    .line 120
    const-string v3, "navdy_vehicle_marker_right_4"

    invoke-direct {p0, p1, v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v3

    aput-object v3, v0, v4

    .line 121
    const-string v3, "navdy_vehicle_marker_right_8"

    invoke-direct {p0, p1, v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v3

    aput-object v3, v0, v1

    .line 122
    const-string v1, "navdy_vehicle_marker_right_12"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v1

    aput-object v1, v0, v6

    .line 123
    const-string v1, "navdy_vehicle_marker_right_16"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v1

    aput-object v1, v0, v2

    .line 124
    const-string v1, "navdy_vehicle_marker_right_20"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v1

    aput-object v1, v0, v7

    .line 125
    const-string v1, "navdy_vehicle_marker_right_24"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object p1

    aput-object p1, v0, v8

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRightMarkerBitmaps:[Landroid/graphics/Bitmap;

    .line 127
    invoke-virtual {p0, v4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setWillNotDraw(Z)V

    .line 128
    const/16 p1, 0x8

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setVisibility(I)V

    .line 129
    return-void
.end method

.method private static blendColor(IIF)I
    .locals 4

    .line 418
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p2

    .line 419
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

    .line 421
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

    .line 423
    and-int/lit16 p0, p0, 0xff

    int-to-float p0, p0

    mul-float p0, p0, v1

    and-int/lit16 p1, p1, 0xff

    int-to-float p1, p1

    mul-float p1, p1, p2

    add-float/2addr p0, p1

    invoke-static {p0}, Ljava/lang/Math;->round(F)I

    move-result p0

    .line 424
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

    .line 405
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

    .line 375
    invoke-virtual {p0, p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->removeCallbacks(Ljava/lang/Runnable;)Z

    .line 376
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashFrameScheduled:Z

    .line 377
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 378
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    .line 379
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeft:[F

    .line 380
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    .line 381
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    .line 382
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRight:[F

    .line 383
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    .line 384
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    .line 385
    new-array v0, v0, [F

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    .line 386
    const/4 v0, 0x0

    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftProb:F

    .line 387
    const-string v1, "unknown"

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftType:Ljava/lang/String;

    .line 388
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftProb:F

    .line 389
    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftType:Ljava/lang/String;

    .line 390
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskLeft:F

    .line 391
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightProb:F

    .line 392
    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightType:Ljava/lang/String;

    .line 393
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskRight:F

    .line 394
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightProb:F

    .line 395
    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightType:Ljava/lang/String;

    .line 396
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeftProb:F

    .line 397
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRightProb:F

    .line 398
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    .line 399
    const-wide/16 v0, 0x0

    iput-wide v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    .line 400
    const/16 v0, 0x8

    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setVisibility(I)V

    .line 401
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->invalidate()V

    .line 402
    return-void
.end method

.method private drawLane(Landroid/graphics/Canvas;[FFFLjava/lang/String;)V
    .locals 4

    .line 264
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_6

    const v0, 0x3d4ccccd    # 0.05f

    cmpg-float v0, p3, v0

    if-gez v0, :cond_0

    goto :goto_3

    .line 267
    :cond_0
    nop

    .line 268
    invoke-static {p4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p4

    const/high16 v0, 0x41200000    # 10.0f

    mul-float p4, p4, v0

    invoke-static {p4}, Ljava/lang/Math;->round(F)I

    move-result p4

    const/4 v0, 0x0

    invoke-static {v0, p4}, Ljava/lang/Math;->max(II)I

    move-result p4

    .line 267
    const/16 v1, 0xa

    invoke-static {v1, p4}, Ljava/lang/Math;->min(II)I

    move-result p4

    .line 269
    const/4 v1, 0x1

    if-eqz p5, :cond_1

    const-string v2, "center"

    invoke-virtual {p5, v2}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z

    move-result v2

    if-eqz v2, :cond_1

    const/4 v2, 0x1

    goto :goto_0

    :cond_1
    const/4 v2, 0x0

    .line 270
    :goto_0
    const-string v3, "solid"

    invoke-virtual {v3, p5}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v3

    if-nez v3, :cond_2

    const-string v3, "centerSolid"

    invoke-virtual {v3, p5}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p5

    if-eqz p5, :cond_3

    :cond_2
    const/4 v0, 0x1

    .line 271
    :cond_3
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    if-eqz v0, :cond_4

    const/4 v0, 0x0

    goto :goto_1

    :cond_4
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneDashEffect:Landroid/graphics/DashPathEffect;

    :goto_1
    invoke-virtual {p5, v0}, Landroid/graphics/Paint;->setPathEffect(Landroid/graphics/PathEffect;)Landroid/graphics/PathEffect;

    .line 272
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    .line 273
    if-eqz v2, :cond_5

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->centerLaneRiskFilters:[Landroid/graphics/LightingColorFilter;

    aget-object p4, v0, p4

    goto :goto_2

    :cond_5
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskFilters:[Landroid/graphics/LightingColorFilter;

    aget-object p4, v0, p4

    .line 272
    :goto_2
    invoke-virtual {p5, p4}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 274
    iget-object p4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    const/high16 p5, 0x43610000    # 225.0f

    mul-float p3, p3, p5

    const/high16 p5, 0x41f00000    # 30.0f

    add-float/2addr p3, p5

    float-to-int p3, p3

    invoke-virtual {p4, p3}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 275
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object p2

    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p2, p3}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 276
    return-void

    .line 265
    :cond_6
    :goto_3
    return-void
.end method

.method private drawRoadEdge(Landroid/graphics/Canvas;[FF)V
    .locals 2

    .line 279
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_1

    const/high16 v0, 0x3f000000    # 0.5f

    cmpg-float v0, p3, v0

    if-gez v0, :cond_0

    goto :goto_0

    .line 282
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    const/high16 v1, 0x43520000    # 210.0f

    mul-float p3, p3, v1

    const/high16 v1, 0x41c80000    # 25.0f

    add-float/2addr p3, v1

    float-to-int p3, p3

    invoke-virtual {v0, p3}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 283
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object p2

    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p2, p3}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 284
    return-void

    .line 280
    :cond_1
    :goto_0
    return-void
.end method

.method private drawVehicle(Landroid/graphics/Canvas;FFFIIF)V
    .locals 5

    .line 314
    const/high16 v0, 0x42a00000    # 80.0f

    div-float/2addr p4, v0

    const/high16 v0, 0x3f800000    # 1.0f

    sub-float/2addr v0, p4

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p4

    .line 315
    const/high16 v0, 0x423a0000    # 46.5f

    mul-float p4, p4, v0

    const/high16 v0, 0x41400000    # 12.0f

    add-float/2addr p4, v0

    .line 316
    const v0, 0x3fc66666    # 1.55f

    mul-float v0, v0, p4

    .line 318
    const/4 v1, 0x2

    const/16 v2, 0xff

    if-ne p5, v1, :cond_0

    .line 319
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    const v1, -0xff1a01

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColor(I)V

    .line 320
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleLongitudinalLeadFilter:Landroid/graphics/LightingColorFilter;

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 321
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    invoke-virtual {p5, v2}, Landroid/graphics/Paint;->setAlpha(I)V

    goto :goto_0

    .line 322
    :cond_0
    const/4 v1, 0x1

    if-ne p5, v1, :cond_1

    .line 323
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    const v1, -0xff19ba

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColor(I)V

    .line 324
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleVisionFilter:Landroid/graphics/LightingColorFilter;

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 325
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    invoke-virtual {p5, v2}, Landroid/graphics/Paint;->setAlpha(I)V

    goto :goto_0

    .line 327
    :cond_1
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    const v1, -0x22000001

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColor(I)V

    .line 328
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRadarFilter:Landroid/graphics/LightingColorFilter;

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 329
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    const/16 v1, 0xdd

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 332
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

    .line 337
    invoke-direct {p0, p7, p6, p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleMarkerForYaw(FIF)Landroid/graphics/Bitmap;

    move-result-object p2

    .line 338
    if-eqz p2, :cond_2

    .line 339
    const/4 p3, 0x0

    iget-object p4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p2, p3, p5, p4}, Landroid/graphics/Canvas;->drawBitmap(Landroid/graphics/Bitmap;Landroid/graphics/Rect;Landroid/graphics/RectF;Landroid/graphics/Paint;)V

    goto :goto_1

    .line 341
    :cond_2
    const p2, 0x3e75c28f    # 0.24f

    mul-float p4, p4, p2

    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p5, p4, p4, p2}, Landroid/graphics/Canvas;->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V

    .line 343
    :goto_1
    return-void
.end method

.method private drawVehicles(Landroid/graphics/Canvas;)V
    .locals 11

    .line 304
    const/4 v0, 0x0

    :goto_0
    add-int/lit8 v1, v0, 0x5

    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    array-length v2, v2

    if-ge v1, v2, :cond_0

    .line 305
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    aget v5, v2, v0

    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    add-int/lit8 v3, v0, 0x1

    aget v6, v2, v3

    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    add-int/lit8 v3, v0, 0x2

    aget v7, v2, v3

    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    add-int/lit8 v3, v0, 0x3

    aget v2, v2, v3

    float-to-int v8, v2

    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    add-int/lit8 v3, v0, 0x4

    aget v2, v2, v3

    float-to-int v9, v2

    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    aget v10, v2, v1

    move-object v3, p0

    move-object v4, p1

    invoke-direct/range {v3 .. v10}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawVehicle(Landroid/graphics/Canvas;FFFIIF)V

    .line 304
    add-int/lit8 v0, v0, 0x6

    goto :goto_0

    .line 309
    :cond_0
    return-void
.end method

.method private static linePath([F)Landroid/graphics/Path;
    .locals 4

    .line 428
    new-instance v0, Landroid/graphics/Path;

    invoke-direct {v0}, Landroid/graphics/Path;-><init>()V

    .line 429
    const/4 v1, 0x0

    aget v1, p0, v1

    const/4 v2, 0x1

    aget v2, p0, v2

    invoke-virtual {v0, v1, v2}, Landroid/graphics/Path;->moveTo(FF)V

    .line 430
    const/4 v1, 0x2

    :goto_0
    array-length v2, p0

    if-ge v1, v2, :cond_0

    .line 431
    aget v2, p0, v1

    add-int/lit8 v3, v1, 0x1

    aget v3, p0, v3

    invoke-virtual {v0, v2, v3}, Landroid/graphics/Path;->lineTo(FF)V

    .line 430
    add-int/lit8 v1, v1, 0x2

    goto :goto_0

    .line 433
    :cond_0
    return-object v0
.end method

.method private loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;
    .locals 2

    .line 132
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->getResources()Landroid/content/res/Resources;

    move-result-object v0

    .line 133
    invoke-virtual {p1}, Landroid/content/Context;->getPackageName()Ljava/lang/String;

    move-result-object p1

    .line 132
    const-string v1, "drawable"

    invoke-virtual {v0, p2, v1, p1}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I

    move-result p1

    .line 134
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

.method private static readLaneType(Lorg/json/JSONObject;Ljava/lang/String;)Ljava/lang/String;
    .locals 1

    .line 409
    const-string v0, "unknown"

    invoke-virtual {p0, p1, v0}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    .line 410
    const-string p1, "solid"

    invoke-virtual {p1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p1

    if-nez p1, :cond_1

    const-string p1, "dashed"

    invoke-virtual {p1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p1

    if-nez p1, :cond_1

    .line 411
    const-string p1, "centerSolid"

    invoke-virtual {p1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p1

    if-nez p1, :cond_1

    const-string p1, "centerDashed"

    invoke-virtual {p1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p1

    if-eqz p1, :cond_0

    goto :goto_0

    .line 414
    :cond_0
    return-object v0

    .line 412
    :cond_1
    :goto_0
    return-object p0
.end method

.method private static readPoints(Lorg/json/JSONArray;)[F
    .locals 4

    .line 437
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

    .line 440
    :cond_0
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    new-array v1, v1, [F

    .line 441
    nop

    :goto_0
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v2

    if-ge v0, v2, :cond_1

    .line 442
    const-wide/16 v2, 0x0

    invoke-virtual {p0, v0, v2, v3}, Lorg/json/JSONArray;->optDouble(ID)D

    move-result-wide v2

    double-to-float v2, v2

    aput v2, v1, v0

    .line 441
    add-int/lit8 v0, v0, 0x1

    goto :goto_0

    .line 444
    :cond_1
    return-object v1

    .line 438
    :cond_2
    :goto_1
    new-array p0, v0, [F

    return-object p0
.end method

.method private static readVehicles(Lorg/json/JSONArray;)[F
    .locals 12

    .line 448
    const/4 v0, 0x0

    if-eqz p0, :cond_9

    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    if-nez v1, :cond_0

    goto/16 :goto_5

    .line 451
    :cond_0
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    mul-int/lit8 v1, v1, 0x6

    new-array v2, v1, [F

    .line 452
    nop

    .line 453
    const/4 v3, 0x0

    const/4 v4, 0x0

    :goto_0
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v5

    if-ge v3, v5, :cond_7

    .line 454
    invoke-virtual {p0, v3}, Lorg/json/JSONArray;->optJSONObject(I)Lorg/json/JSONObject;

    move-result-object v5

    .line 455
    if-nez v5, :cond_1

    .line 456
    goto/16 :goto_4

    .line 458
    :cond_1
    const-string v6, "longitudinalLead"

    invoke-virtual {v5, v6, v0}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v6

    const/4 v8, 0x1

    if-eqz v6, :cond_2

    const/4 v6, 0x2

    goto :goto_1

    :cond_2
    const-string v6, "source"

    const-string v7, "radar"

    invoke-virtual {v5, v6, v7}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v6

    .line 459
    const-string v7, "vision"

    invoke-virtual {v7, v6}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v6

    if-eqz v6, :cond_3

    const/4 v6, 0x1

    goto :goto_1

    :cond_3
    const/4 v6, 0x0

    .line 460
    :goto_1
    const-string v7, "lane"

    const-string v9, "center"

    invoke-virtual {v5, v7, v9}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v7

    .line 461
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

    .line 462
    :goto_2
    add-int/lit8 v7, v4, 0x1

    const-string v9, "screenX"

    const-wide/high16 v10, 0x4064000000000000L    # 160.0

    invoke-virtual {v5, v9, v10, v11}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v9

    double-to-float v9, v9

    aput v9, v2, v4

    .line 463
    add-int/lit8 v4, v7, 0x1

    const-string v9, "screenY"

    const-wide/high16 v10, 0x4020000000000000L    # 8.0

    invoke-virtual {v5, v9, v10, v11}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v9

    double-to-float v9, v9

    aput v9, v2, v7

    .line 464
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

    .line 465
    add-int/lit8 v4, v7, 0x1

    int-to-float v6, v6

    aput v6, v2, v7

    .line 466
    add-int/lit8 v6, v4, 0x1

    int-to-float v7, v8

    aput v7, v2, v4

    .line 467
    add-int/lit8 v4, v6, 0x1

    const-string v7, "yawDeg"

    invoke-virtual {v5, v7}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result v8

    if-eqz v8, :cond_6

    .line 468
    const-wide/16 v8, 0x0

    invoke-virtual {v5, v7, v8, v9}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v7

    double-to-float v5, v7

    goto :goto_3

    :cond_6
    const/high16 v5, 0x7fc00000    # Float.NaN

    :goto_3
    aput v5, v2, v6

    .line 453
    :goto_4
    add-int/lit8 v3, v3, 0x1

    goto/16 :goto_0

    .line 470
    :cond_7
    if-ne v4, v1, :cond_8

    .line 471
    return-object v2

    .line 473
    :cond_8
    new-array p0, v4, [F

    .line 474
    invoke-static {v2, v0, p0, v0, v4}, Ljava/lang/System;->arraycopy(Ljava/lang/Object;ILjava/lang/Object;II)V

    .line 475
    return-object p0

    .line 449
    :cond_9
    :goto_5
    new-array p0, v0, [F

    return-object p0
.end method

.method private scheduleDashFrame()V
    .locals 2

    .line 246
    iget-boolean v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashFrameScheduled:Z

    if-eqz v0, :cond_0

    .line 247
    return-void

    .line 249
    :cond_0
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashFrameScheduled:Z

    .line 250
    const-wide/16 v0, 0x42

    invoke-virtual {p0, p0, v0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 251
    return-void
.end method

.method private updateDashPhase()V
    .locals 7

    .line 287
    invoke-static {}, Landroid/os/SystemClock;->uptimeMillis()J

    move-result-wide v0

    .line 288
    iget-wide v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    const-wide/16 v4, 0x0

    cmp-long v6, v2, v4

    if-nez v6, :cond_0

    .line 289
    iput-wide v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    .line 290
    return-void

    .line 293
    :cond_0
    iget-wide v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    sub-long v2, v0, v2

    const-wide/16 v4, 0x96

    invoke-static {v2, v3, v4, v5}, Ljava/lang/Math;->min(JJ)J

    move-result-wide v2

    .line 294
    iput-wide v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    .line 295
    iget v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    const/high16 v1, 0x3f800000    # 1.0f

    cmpg-float v0, v0, v1

    if-gtz v0, :cond_1

    .line 296
    return-void

    .line 299
    :cond_1
    iget v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    const v1, 0x3f4ccccd    # 0.8f

    mul-float v0, v0, v1

    const/high16 v1, 0x41900000    # 18.0f

    invoke-static {v1, v0}, Ljava/lang/Math;->max(FF)F

    move-result v0

    const/high16 v1, 0x42a00000    # 80.0f

    invoke-static {v1, v0}, Ljava/lang/Math;->min(FF)F

    move-result v0

    .line 300
    iget v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashPhase:F

    long-to-float v2, v2

    mul-float v2, v2, v0

    const/high16 v0, 0x447a0000    # 1000.0f

    div-float/2addr v2, v0

    add-float/2addr v4, v2

    rem-float/2addr v4, v1

    iput v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashPhase:F

    .line 301
    return-void
.end method

.method private static validLine([F)Z
    .locals 2

    .line 479
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

    .line 346
    invoke-static {p1}, Ljava/lang/Float;->isNaN(F)Z

    move-result v0

    const/4 v1, 0x0

    const/high16 v2, 0x40800000    # 4.0f

    const/high16 v3, 0x41c00000    # 24.0f

    if-eqz v0, :cond_5

    .line 347
    const/high16 p1, 0x43200000    # 160.0f

    sub-float/2addr p3, p1

    invoke-static {p3}, Ljava/lang/Math;->abs(F)F

    move-result p1

    .line 349
    cmpg-float p3, p1, v3

    if-ltz p3, :cond_4

    if-nez p2, :cond_0

    goto :goto_0

    .line 351
    :cond_0
    const/high16 p3, 0x42400000    # 48.0f

    cmpg-float p3, p1, p3

    if-gez p3, :cond_1

    .line 352
    const/high16 p1, 0x40800000    # 4.0f

    goto :goto_1

    .line 353
    :cond_1
    const/high16 p3, 0x42900000    # 72.0f

    cmpg-float p3, p1, p3

    if-gez p3, :cond_2

    .line 354
    const/high16 p1, 0x41000000    # 8.0f

    goto :goto_1

    .line 355
    :cond_2
    const/high16 p3, 0x42d00000    # 104.0f

    cmpg-float p1, p1, p3

    if-gez p1, :cond_3

    .line 356
    const/high16 p1, 0x41400000    # 12.0f

    goto :goto_1

    .line 358
    :cond_3
    const/high16 p1, 0x41800000    # 16.0f

    goto :goto_1

    .line 350
    :cond_4
    :goto_0
    const/4 p1, 0x0

    .line 360
    :goto_1
    if-gez p2, :cond_5

    neg-float p1, p1

    .line 363
    :cond_5
    invoke-static {p1}, Ljava/lang/Math;->abs(F)F

    move-result p2

    invoke-static {v3, p2}, Ljava/lang/Math;->min(FF)F

    move-result p2

    .line 364
    const/high16 p3, 0x40000000    # 2.0f

    cmpg-float p3, p2, p3

    if-gez p3, :cond_6

    .line 365
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleMarkerBitmap:Landroid/graphics/Bitmap;

    return-object p1

    .line 367
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

    .line 368
    cmpg-float p1, p1, v1

    if-gez p1, :cond_7

    .line 369
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleLeftMarkerBitmaps:[Landroid/graphics/Bitmap;

    aget-object p1, p1, p2

    goto :goto_2

    .line 370
    :cond_7
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRightMarkerBitmaps:[Landroid/graphics/Bitmap;

    aget-object p1, p1, p2

    .line 371
    :goto_2
    if-nez p1, :cond_8

    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleMarkerBitmap:Landroid/graphics/Bitmap;

    :cond_8
    return-object p1
.end method


# virtual methods
.method protected onDraw(Landroid/graphics/Canvas;)V
    .locals 6

    .line 215
    invoke-super {p0, p1}, Landroid/view/View;->onDraw(Landroid/graphics/Canvas;)V

    .line 216
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_3

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-nez v0, :cond_0

    goto/16 :goto_1

    .line 220
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    .line 221
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    array-length v1, v1

    add-int/lit8 v1, v1, -0x2

    :goto_0
    if-ltz v1, :cond_1

    .line 222
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    aget v2, v2, v1

    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    add-int/lit8 v4, v1, 0x1

    aget v3, v3, v4

    invoke-virtual {v0, v2, v3}, Landroid/graphics/Path;->lineTo(FF)V

    .line 221
    add-int/lit8 v1, v1, -0x2

    goto :goto_0

    .line 224
    :cond_1
    invoke-virtual {v0}, Landroid/graphics/Path;->close()V

    .line 225
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 226
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 227
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 229
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeftProb:F

    invoke-direct {p0, p1, v0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawRoadEdge(Landroid/graphics/Canvas;[FF)V

    .line 230
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRightProb:F

    invoke-direct {p0, p1, v0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawRoadEdge(Landroid/graphics/Canvas;[FF)V

    .line 232
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->updateDashPhase()V

    .line 233
    new-instance v0, Landroid/graphics/DashPathEffect;

    sget-object v1, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->LANE_DASH_PATTERN:[F

    iget v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashPhase:F

    invoke-direct {v0, v1, v2}, Landroid/graphics/DashPathEffect;-><init>([FF)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneDashEffect:Landroid/graphics/DashPathEffect;

    .line 234
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeft:[F

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftProb:F

    const/4 v4, 0x0

    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftType:Ljava/lang/String;

    move-object v0, p0

    move-object v1, p1

    invoke-direct/range {v0 .. v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLane(Landroid/graphics/Canvas;[FFFLjava/lang/String;)V

    .line 235
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftProb:F

    iget v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskLeft:F

    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftType:Ljava/lang/String;

    invoke-direct/range {v0 .. v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLane(Landroid/graphics/Canvas;[FFFLjava/lang/String;)V

    .line 236
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightProb:F

    iget v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskRight:F

    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightType:Ljava/lang/String;

    invoke-direct/range {v0 .. v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLane(Landroid/graphics/Canvas;[FFFLjava/lang/String;)V

    .line 237
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRight:[F

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightProb:F

    const/4 v4, 0x0

    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightType:Ljava/lang/String;

    invoke-direct/range {v0 .. v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLane(Landroid/graphics/Canvas;[FFFLjava/lang/String;)V

    .line 238
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawVehicles(Landroid/graphics/Canvas;)V

    .line 240
    iget v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    const/high16 v1, 0x3f800000    # 1.0f

    cmpl-float v0, v0, v1

    if-lez v0, :cond_2

    .line 241
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->scheduleDashFrame()V

    .line 243
    :cond_2
    return-void

    .line 217
    :cond_3
    :goto_1
    return-void
.end method

.method protected onSizeChanged(IIII)V
    .locals 8

    .line 203
    invoke-super {p0, p1, p2, p3, p4}, Landroid/view/View;->onSizeChanged(IIII)V

    .line 204
    int-to-float p1, p2

    .line 205
    new-instance p2, Landroid/graphics/LinearGradient;

    const/4 v6, -0x1

    sget-object v7, Landroid/graphics/Shader$TileMode;->CLAMP:Landroid/graphics/Shader$TileMode;

    const/4 v1, 0x0

    const/4 v2, 0x0

    const/4 v3, 0x0

    const v5, 0x55ffffff    # 3.518437E13f

    move-object v0, p2

    move v4, p1

    invoke-direct/range {v0 .. v7}, Landroid/graphics/LinearGradient;-><init>(FFFFIILandroid/graphics/Shader$TileMode;)V

    .line 207
    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    invoke-virtual {p3, p2}, Landroid/graphics/Paint;->setShader(Landroid/graphics/Shader;)Landroid/graphics/Shader;

    .line 208
    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p3, p2}, Landroid/graphics/Paint;->setShader(Landroid/graphics/Shader;)Landroid/graphics/Shader;

    .line 209
    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    new-instance p3, Landroid/graphics/LinearGradient;

    const v6, -0x66ff19ba

    sget-object v7, Landroid/graphics/Shader$TileMode;->CLAMP:Landroid/graphics/Shader$TileMode;

    const v5, 0x1100e646

    move-object v0, p3

    invoke-direct/range {v0 .. v7}, Landroid/graphics/LinearGradient;-><init>(FFFFIILandroid/graphics/Shader$TileMode;)V

    invoke-virtual {p2, p3}, Landroid/graphics/Paint;->setShader(Landroid/graphics/Shader;)Landroid/graphics/Shader;

    .line 211
    return-void
.end method

.method public run()V
    .locals 2

    .line 255
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashFrameScheduled:Z

    .line 256
    iget v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    const/high16 v1, 0x3f800000    # 1.0f

    cmpl-float v0, v0, v1

    if-lez v0, :cond_0

    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->getVisibility()I

    move-result v0

    if-nez v0, :cond_0

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 257
    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_0

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 258
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->invalidate()V

    .line 260
    :cond_0
    return-void
.end method

.method public updatePayload(Ljava/lang/String;Z)V
    .locals 10

    .line 138
    const-string v0, "navPathLeft"

    const-string v1, "navLaneRiskRight"

    const-string v2, "navLaneRiskLeft"

    const-string v3, "navVehicles"

    if-eqz p2, :cond_8

    if-nez p1, :cond_0

    goto/16 :goto_2

    .line 144
    :cond_0
    :try_start_0
    new-instance p2, Lorg/json/JSONObject;

    invoke-direct {p2, p1}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    .line 145
    const-string p1, "vEgoKph"

    const-wide/16 v4, 0x0

    invoke-virtual {p2, p1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v6

    double-to-float p1, v6

    const/4 v6, 0x0

    invoke-static {v6, p1}, Ljava/lang/Math;->max(FF)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    .line 146
    invoke-virtual {p2, v3}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result p1

    if-eqz p1, :cond_1

    .line 147
    invoke-virtual {p2, v3}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object p1

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readVehicles(Lorg/json/JSONArray;)[F

    move-result-object p1

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    .line 149
    :cond_1
    invoke-virtual {p2, v2}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result p1

    if-eqz p1, :cond_2

    .line 150
    invoke-virtual {p2, v2, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v2

    double-to-float p1, v2

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskLeft:F

    .line 152
    :cond_2
    invoke-virtual {p2, v1}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result p1

    if-eqz p1, :cond_3

    .line 153
    invoke-virtual {p2, v1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v1

    double-to-float p1, v1

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskRight:F

    .line 155
    :cond_3
    invoke-virtual {p2, v0}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result p1

    if-nez p1, :cond_5

    .line 156
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->getVisibility()I

    move-result p1

    if-nez p1, :cond_4

    .line 157
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->invalidate()V

    .line 159
    :cond_4
    return-void

    .line 162
    :cond_5
    invoke-virtual {p2, v0}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object p1

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object p1

    .line 163
    const-string v0, "navPathRight"

    invoke-virtual {p2, v0}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v0

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v0

    .line 164
    const-string v1, "navLaneFarLeft"

    invoke-virtual {p2, v1}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v1

    invoke-static {v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v1

    .line 165
    const-string v2, "navLaneLeft"

    invoke-virtual {p2, v2}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v2

    invoke-static {v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v2

    .line 166
    const-string v3, "navLaneRight"

    invoke-virtual {p2, v3}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v3

    invoke-static {v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v3

    .line 167
    const-string v6, "navLaneFarRight"

    invoke-virtual {p2, v6}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v6

    invoke-static {v6}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v6

    .line 168
    const-string v7, "navRoadEdgeLeft"

    invoke-virtual {p2, v7}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v7

    invoke-static {v7}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v7

    .line 169
    const-string v8, "navRoadEdgeRight"

    invoke-virtual {p2, v8}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v8

    invoke-static {v8}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v8

    .line 170
    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v9

    if-eqz v9, :cond_7

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v9

    if-eqz v9, :cond_7

    .line 171
    invoke-static {v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v9

    if-eqz v9, :cond_7

    invoke-static {v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v9

    if-nez v9, :cond_6

    goto/16 :goto_0

    .line 176
    :cond_6
    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 177
    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    .line 178
    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeft:[F

    .line 179
    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    .line 180
    iput-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    .line 181
    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRight:[F

    .line 182
    iput-object v7, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    .line 183
    iput-object v8, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    .line 184
    const-string p1, "navLaneFarLeftProb"

    invoke-virtual {p2, p1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p1, v0

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftProb:F

    .line 185
    const-string p1, "navLaneLeftProb"

    invoke-virtual {p2, p1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p1, v0

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftProb:F

    .line 186
    const-string p1, "navLaneRightProb"

    invoke-virtual {p2, p1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p1, v0

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightProb:F

    .line 187
    const-string p1, "navLaneFarRightProb"

    invoke-virtual {p2, p1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p1, v0

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightProb:F

    .line 188
    const-string p1, "navLaneFarLeftType"

    invoke-static {p2, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readLaneType(Lorg/json/JSONObject;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftType:Ljava/lang/String;

    .line 189
    const-string p1, "navLaneLeftType"

    invoke-static {p2, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readLaneType(Lorg/json/JSONObject;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftType:Ljava/lang/String;

    .line 190
    const-string p1, "navLaneRightType"

    invoke-static {p2, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readLaneType(Lorg/json/JSONObject;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightType:Ljava/lang/String;

    .line 191
    const-string p1, "navLaneFarRightType"

    invoke-static {p2, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readLaneType(Lorg/json/JSONObject;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightType:Ljava/lang/String;

    .line 192
    const-string p1, "navRoadEdgeLeftProb"

    invoke-virtual {p2, p1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p1, v0

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeftProb:F

    .line 193
    const-string p1, "navRoadEdgeRightProb"

    invoke-virtual {p2, p1, v4, v5}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide p1

    double-to-float p1, p1

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRightProb:F

    .line 194
    const/4 p1, 0x0

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setVisibility(I)V

    .line 195
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->invalidate()V

    .line 198
    goto :goto_1

    .line 172
    :cond_7
    :goto_0
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 173
    return-void

    .line 196
    :catch_0
    move-exception p1

    .line 197
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V

    .line 199
    :goto_1
    return-void

    .line 139
    :cond_8
    :goto_2
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V

    .line 140
    return-void
.end method
