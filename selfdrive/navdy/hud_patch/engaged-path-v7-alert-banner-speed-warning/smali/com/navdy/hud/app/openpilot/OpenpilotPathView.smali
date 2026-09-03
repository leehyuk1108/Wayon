.class public final Lcom/navdy/hud/app/openpilot/OpenpilotPathView;
.super Landroid/view/View;
.source "OpenpilotPathView.java"

# interfaces
.implements Ljava/lang/Runnable;


# static fields
.field private static final COLOR_ACCEL_FLOW:I = -0x99007a

.field private static final COLOR_BRAKE_FLOW:I = -0x1

.field private static final COLOR_GREEN:I = -0xff19ba

.field private static final COLOR_LANE_CENTER:I = -0x2bc5

.field private static final COLOR_LANE_CLEAR:I = -0x1

.field private static final COLOR_LANE_DANGER:I = -0xdfd8

.field private static final COLOR_TRAFFIC_STOP:I = -0xc4d0

.field private static final COLOR_VEHICLE_LONGITUDINAL_LEAD:I = -0xff1a01

.field private static final COLOR_VEHICLE_CUTIN:I = -0xdfd8

.field private static final COLOR_VEHICLE_RADAR:I = -0x22000001

.field private static final COLOR_VEHICLE_VISION:I = -0xff19ba

.field private static final DASH_FRAME_MS:J = 0x42L

.field private static final FLOW_BAND_SLICES:I = 0x6

.field private static final LANE_DASH_CYCLE:F = 80.0f

.field private static final LANE_DASH_PATTERN:[F

.field private static final LANE_RISK_FILTER_STEPS:I = 0xa

.field private static final ROAD_EDGE_MIN_CONFIDENCE:F = 0.5f


# instance fields
.field private final accelerationFlowPaint:Landroid/graphics/Paint;

.field private accelerationPhase:F

.field private final brakeFlowPaint:Landroid/graphics/Paint;

.field private brakePhase:F

.field private final centerLaneRiskFilters:[Landroid/graphics/LightingColorFilter;

.field private dashFrameScheduled:Z

.field private dashPhase:F

.field private final flowBackPoint:[F

.field private final flowCenterPoint:[F

.field private final flowLeftPoint:[F

.field private final flowPath:Landroid/graphics/Path;

.field private final flowRightPoint:[F

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

.field private longitudinalActuator:Ljava/lang/String;

.field private longitudinalActuatorLevel:F

.field private final pathEdgePaint:Landroid/graphics/Paint;

.field private final pathFillPaint:Landroid/graphics/Paint;

.field private pathLeft:[F

.field private pathRight:[F

.field private roadEdgeLeft:[F

.field private roadEdgeLeftProb:F

.field private final roadEdgePaint:Landroid/graphics/Paint;

.field private roadEdgeRight:[F

.field private roadEdgeRightProb:F

.field private final scratchPath:Landroid/graphics/Path;

.field private trafficStopActive:Z

.field private final trafficStopGlowPaint:Landroid/graphics/Paint;

.field private trafficStopLine:[F

.field private final trafficStopPaint:Landroid/graphics/Paint;

.field private final vehicleBitmapPaint:Landroid/graphics/Paint;

.field private final vehicleFillPaint:Landroid/graphics/Paint;

.field private final vehicleLeftMarkerBitmaps:[Landroid/graphics/Bitmap;

.field private final vehicleLongitudinalLeadFilter:Landroid/graphics/LightingColorFilter;

.field private final vehicleCutInFilter:Landroid/graphics/LightingColorFilter;

.field private final vehicleMarkerBitmap:Landroid/graphics/Bitmap;

.field private final vehicleRadarFilter:Landroid/graphics/LightingColorFilter;

.field private final vehicleRect:Landroid/graphics/RectF;

.field private final vehicleRightMarkerBitmaps:[Landroid/graphics/Bitmap;

.field private vehicleSpeedKph:F

.field private final vehicleVisionFilter:Landroid/graphics/LightingColorFilter;

.field private vehicles:[F


# direct methods
.method static constructor <clinit>()V
    .registers 1

    .line 31
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
    .registers 14

    .line 102
    invoke-direct {p0, p1}, Landroid/view/View;-><init>(Landroid/content/Context;)V

    .line 38
    new-instance v0, Landroid/graphics/Paint;

    const/4 v1, 0x1

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    .line 39
    new-instance v0, Landroid/graphics/Paint;

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    .line 40
    new-instance v0, Landroid/graphics/Paint;

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    .line 41
    new-instance v0, Landroid/graphics/Paint;

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    .line 42
    new-instance v0, Landroid/graphics/Paint;

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->accelerationFlowPaint:Landroid/graphics/Paint;

    .line 43
    new-instance v0, Landroid/graphics/Paint;

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->brakeFlowPaint:Landroid/graphics/Paint;

    .line 44
    new-instance v0, Landroid/graphics/Paint;

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    .line 45
    new-instance v0, Landroid/graphics/Paint;

    const/4 v2, 0x3

    invoke-direct {v0, v2}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    .line 47
    new-instance v0, Landroid/graphics/Paint;

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopGlowPaint:Landroid/graphics/Paint;

    .line 48
    new-instance v0, Landroid/graphics/Paint;

    invoke-direct {v0, v1}, Landroid/graphics/Paint;-><init>(I)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopPaint:Landroid/graphics/Paint;

    .line 49
    const/16 v0, 0xb

    new-array v3, v0, [Landroid/graphics/LightingColorFilter;

    iput-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskFilters:[Landroid/graphics/LightingColorFilter;

    .line 51
    new-array v0, v0, [Landroid/graphics/LightingColorFilter;

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->centerLaneRiskFilters:[Landroid/graphics/LightingColorFilter;

    .line 53
    new-instance v0, Landroid/graphics/LightingColorFilter;

    const/4 v3, -0x1

    const/4 v4, 0x0

    invoke-direct {v0, v3, v4}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRadarFilter:Landroid/graphics/LightingColorFilter;

    .line 54
    new-instance v0, Landroid/graphics/LightingColorFilter;

    const v5, -0xff19ba

    invoke-direct {v0, v5, v4}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleVisionFilter:Landroid/graphics/LightingColorFilter;

    .line 56
    new-instance v0, Landroid/graphics/LightingColorFilter;

    const v6, -0xff1a01

    invoke-direct {v0, v6, v4}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleLongitudinalLeadFilter:Landroid/graphics/LightingColorFilter;

    new-instance v0, Landroid/graphics/LightingColorFilter;

    const v7, -0xdfd8

    invoke-direct {v0, v7, v4}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleCutInFilter:Landroid/graphics/LightingColorFilter;

    .line 61
    new-instance v0, Landroid/graphics/Path;

    invoke-direct {v0}, Landroid/graphics/Path;-><init>()V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->scratchPath:Landroid/graphics/Path;

    .line 62
    new-instance v0, Landroid/graphics/Path;

    invoke-direct {v0}, Landroid/graphics/Path;-><init>()V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowPath:Landroid/graphics/Path;

    .line 63
    new-instance v0, Landroid/graphics/RectF;

    invoke-direct {v0}, Landroid/graphics/RectF;-><init>()V

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRect:Landroid/graphics/RectF;

    .line 64
    const/4 v0, 0x2

    new-array v6, v0, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowLeftPoint:[F

    .line 65
    new-array v6, v0, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowRightPoint:[F

    .line 66
    new-array v6, v0, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowCenterPoint:[F

    .line 67
    new-array v6, v0, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowBackPoint:[F

    .line 68
    new-array v6, v4, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeft:[F

    .line 70
    const-string v6, "unknown"

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftType:Ljava/lang/String;

    .line 71
    new-array v7, v4, [F

    iput-object v7, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    .line 73
    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftType:Ljava/lang/String;

    .line 75
    new-array v7, v4, [F

    iput-object v7, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    .line 77
    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightType:Ljava/lang/String;

    .line 79
    new-array v7, v4, [F

    iput-object v7, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRight:[F

    .line 81
    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightType:Ljava/lang/String;

    .line 82
    new-array v6, v4, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 83
    new-array v6, v4, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    .line 84
    new-array v6, v4, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    .line 86
    new-array v6, v4, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    .line 88
    new-array v6, v4, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    .line 89
    new-array v6, v4, [F

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopLine:[F

    .line 98
    const-string v6, "none"

    iput-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuator:Ljava/lang/String;

    .line 104
    iget-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    sget-object v7, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v6, v7}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 105
    iget-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    sget-object v7, Landroid/graphics/Paint$Cap;->ROUND:Landroid/graphics/Paint$Cap;

    invoke-virtual {v6, v7}, Landroid/graphics/Paint;->setStrokeCap(Landroid/graphics/Paint$Cap;)V

    .line 106
    iget-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    sget-object v7, Landroid/graphics/Paint$Join;->ROUND:Landroid/graphics/Paint$Join;

    invoke-virtual {v6, v7}, Landroid/graphics/Paint;->setStrokeJoin(Landroid/graphics/Paint$Join;)V

    .line 107
    iget-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    const v7, 0x404ccccd    # 3.2f

    invoke-virtual {v6, v7}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 108
    const/4 v6, 0x0

    :goto_ec
    const/16 v7, 0xa

    const v8, -0xdfd8

    if-gt v6, v7, :cond_116

    .line 109
    int-to-float v7, v6

    const/high16 v9, 0x41200000    # 10.0f

    div-float/2addr v7, v9

    .line 110
    iget-object v9, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskFilters:[Landroid/graphics/LightingColorFilter;

    new-instance v10, Landroid/graphics/LightingColorFilter;

    invoke-static {v3, v8, v7}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->blendColor(IIF)I

    move-result v11

    invoke-direct {v10, v11, v4}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    aput-object v10, v9, v6

    .line 112
    iget-object v9, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->centerLaneRiskFilters:[Landroid/graphics/LightingColorFilter;

    new-instance v10, Landroid/graphics/LightingColorFilter;

    const/16 v11, -0x2bc5

    invoke-static {v11, v8, v7}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->blendColor(IIF)I

    move-result v7

    invoke-direct {v10, v7, v4}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    aput-object v10, v9, v6

    .line 108
    add-int/lit8 v6, v6, 0x1

    goto :goto_ec

    .line 116
    :cond_116
    iget-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    sget-object v7, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v6, v7}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 117
    iget-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    sget-object v7, Landroid/graphics/Paint$Cap;->ROUND:Landroid/graphics/Paint$Cap;

    invoke-virtual {v6, v7}, Landroid/graphics/Paint;->setStrokeCap(Landroid/graphics/Paint$Cap;)V

    .line 118
    iget-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    sget-object v7, Landroid/graphics/Paint$Join;->ROUND:Landroid/graphics/Paint$Join;

    invoke-virtual {v6, v7}, Landroid/graphics/Paint;->setStrokeJoin(Landroid/graphics/Paint$Join;)V

    .line 119
    iget-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    const v7, 0x40333333    # 2.8f

    invoke-virtual {v6, v7}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 120
    iget-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    const/16 v7, 0x73

    invoke-virtual {v6, v7}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 121
    iget-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    new-instance v7, Landroid/graphics/LightingColorFilter;

    invoke-direct {v7, v8, v4}, Landroid/graphics/LightingColorFilter;-><init>(II)V

    invoke-virtual {v6, v7}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 123
    iget-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {v6, v5}, Landroid/graphics/Paint;->setColor(I)V

    .line 124
    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    sget-object v6, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v5, v6}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 125
    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    sget-object v6, Landroid/graphics/Paint$Join;->ROUND:Landroid/graphics/Paint$Join;

    invoke-virtual {v5, v6}, Landroid/graphics/Paint;->setStrokeJoin(Landroid/graphics/Paint$Join;)V

    .line 126
    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    const v6, 0x3fe66666    # 1.8f

    invoke-virtual {v5, v6}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 128
    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    sget-object v6, Landroid/graphics/Paint$Style;->FILL:Landroid/graphics/Paint$Style;

    invoke-virtual {v5, v6}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 130
    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->accelerationFlowPaint:Landroid/graphics/Paint;

    const v6, -0x99007a

    invoke-virtual {v5, v6}, Landroid/graphics/Paint;->setColor(I)V

    .line 131
    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->accelerationFlowPaint:Landroid/graphics/Paint;

    sget-object v6, Landroid/graphics/Paint$Style;->FILL:Landroid/graphics/Paint$Style;

    invoke-virtual {v5, v6}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 133
    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->brakeFlowPaint:Landroid/graphics/Paint;

    invoke-virtual {v5, v3}, Landroid/graphics/Paint;->setColor(I)V

    .line 134
    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->brakeFlowPaint:Landroid/graphics/Paint;

    sget-object v5, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v3, v5}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 135
    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->brakeFlowPaint:Landroid/graphics/Paint;

    sget-object v5, Landroid/graphics/Paint$Cap;->ROUND:Landroid/graphics/Paint$Cap;

    invoke-virtual {v3, v5}, Landroid/graphics/Paint;->setStrokeCap(Landroid/graphics/Paint$Cap;)V

    .line 136
    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->brakeFlowPaint:Landroid/graphics/Paint;

    sget-object v5, Landroid/graphics/Paint$Join;->ROUND:Landroid/graphics/Paint$Join;

    invoke-virtual {v3, v5}, Landroid/graphics/Paint;->setStrokeJoin(Landroid/graphics/Paint$Join;)V

    .line 138
    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopGlowPaint:Landroid/graphics/Paint;

    const v5, 0x66ff3b30

    invoke-virtual {v3, v5}, Landroid/graphics/Paint;->setColor(I)V

    .line 139
    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopGlowPaint:Landroid/graphics/Paint;

    sget-object v5, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v3, v5}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 140
    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopGlowPaint:Landroid/graphics/Paint;

    sget-object v5, Landroid/graphics/Paint$Cap;->ROUND:Landroid/graphics/Paint$Cap;

    invoke-virtual {v3, v5}, Landroid/graphics/Paint;->setStrokeCap(Landroid/graphics/Paint$Cap;)V

    .line 141
    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopGlowPaint:Landroid/graphics/Paint;

    const/high16 v5, 0x41000000    # 8.0f

    invoke-virtual {v3, v5}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 142
    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopPaint:Landroid/graphics/Paint;

    const v5, -0xc4d0

    invoke-virtual {v3, v5}, Landroid/graphics/Paint;->setColor(I)V

    .line 143
    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopPaint:Landroid/graphics/Paint;

    sget-object v5, Landroid/graphics/Paint$Style;->STROKE:Landroid/graphics/Paint$Style;

    invoke-virtual {v3, v5}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 144
    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopPaint:Landroid/graphics/Paint;

    sget-object v5, Landroid/graphics/Paint$Cap;->ROUND:Landroid/graphics/Paint$Cap;

    invoke-virtual {v3, v5}, Landroid/graphics/Paint;->setStrokeCap(Landroid/graphics/Paint$Cap;)V

    .line 145
    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopPaint:Landroid/graphics/Paint;

    const v5, 0x40666666    # 3.6f

    invoke-virtual {v3, v5}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 147
    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    sget-object v5, Landroid/graphics/Paint$Style;->FILL:Landroid/graphics/Paint$Style;

    invoke-virtual {v3, v5}, Landroid/graphics/Paint;->setStyle(Landroid/graphics/Paint$Style;)V

    .line 148
    const-string v3, "navdy_vehicle_marker"

    invoke-direct {p0, p1, v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v3

    iput-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleMarkerBitmap:Landroid/graphics/Bitmap;

    .line 149
    const/4 v3, 0x6

    new-array v5, v3, [Landroid/graphics/Bitmap;

    .line 150
    const-string v6, "navdy_vehicle_marker_left_4"

    invoke-direct {p0, p1, v6}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v6

    aput-object v6, v5, v4

    .line 151
    const-string v6, "navdy_vehicle_marker_left_8"

    invoke-direct {p0, p1, v6}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v6

    aput-object v6, v5, v1

    .line 152
    const-string v6, "navdy_vehicle_marker_left_12"

    invoke-direct {p0, p1, v6}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v6

    aput-object v6, v5, v0

    .line 153
    const-string v6, "navdy_vehicle_marker_left_16"

    invoke-direct {p0, p1, v6}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v6

    aput-object v6, v5, v2

    .line 154
    const-string v6, "navdy_vehicle_marker_left_20"

    invoke-direct {p0, p1, v6}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v6

    const/4 v7, 0x4

    aput-object v6, v5, v7

    .line 155
    const-string v6, "navdy_vehicle_marker_left_24"

    invoke-direct {p0, p1, v6}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v6

    const/4 v8, 0x5

    aput-object v6, v5, v8

    iput-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleLeftMarkerBitmaps:[Landroid/graphics/Bitmap;

    .line 157
    new-array v3, v3, [Landroid/graphics/Bitmap;

    .line 158
    const-string v5, "navdy_vehicle_marker_right_4"

    invoke-direct {p0, p1, v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v5

    aput-object v5, v3, v4

    .line 159
    const-string v5, "navdy_vehicle_marker_right_8"

    invoke-direct {p0, p1, v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v5

    aput-object v5, v3, v1

    .line 160
    const-string v1, "navdy_vehicle_marker_right_12"

    invoke-direct {p0, p1, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v1

    aput-object v1, v3, v0

    .line 161
    const-string v0, "navdy_vehicle_marker_right_16"

    invoke-direct {p0, p1, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v0

    aput-object v0, v3, v2

    .line 162
    const-string v0, "navdy_vehicle_marker_right_20"

    invoke-direct {p0, p1, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object v0

    aput-object v0, v3, v7

    .line 163
    const-string v0, "navdy_vehicle_marker_right_24"

    invoke-direct {p0, p1, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;

    move-result-object p1

    aput-object p1, v3, v8

    iput-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRightMarkerBitmaps:[Landroid/graphics/Bitmap;

    .line 165
    invoke-virtual {p0, v4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setWillNotDraw(Z)V

    .line 166
    const/16 p1, 0x8

    invoke-virtual {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setVisibility(I)V

    .line 167
    return-void
.end method

.method private static blendColor(IIF)I
    .registers 7

    .line 660
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p2

    .line 661
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

    .line 663
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

    .line 665
    and-int/lit16 p0, p0, 0xff

    int-to-float p0, p0

    mul-float p0, p0, v1

    and-int/lit16 p1, p1, 0xff

    int-to-float p1, p1

    mul-float p1, p1, p2

    add-float/2addr p0, p1

    invoke-static {p0}, Ljava/lang/Math;->round(F)I

    move-result p0

    .line 666
    const/high16 p1, -0x1000000

    shl-int/lit8 p2, v0, 0x10

    or-int/2addr p1, p2

    shl-int/lit8 p2, v2, 0x8

    or-int/2addr p1, p2

    or-int/2addr p0, p1

    return p0
.end method

.method private brakeFlowEndProgress()F
    .registers 6

    .line 464
    nop

    .line 465
    const/high16 v0, 0x3f800000    # 1.0f

    const/4 v1, 0x0

    :goto_4
    add-int/lit8 v2, v1, 0x5

    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    array-length v3, v3

    if-ge v2, v3, :cond_35

    .line 466
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    add-int/lit8 v3, v1, 0x3

    aget v2, v2, v3

    float-to-int v2, v2

    const/4 v3, 0x2

    if-ne v2, v3, :cond_32

    .line 467
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    aget v2, v2, v1

    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    add-int/lit8 v4, v1, 0x1

    aget v3, v3, v4

    .line 468
    invoke-direct {p0, v2, v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->progressForScreenPoint(FF)F

    move-result v2

    const v3, 0x3d4ccccd    # 0.05f

    sub-float/2addr v2, v3

    const v3, 0x3df5c28f    # 0.12f

    invoke-static {v3, v2}, Ljava/lang/Math;->max(FF)F

    move-result v2

    .line 467
    invoke-static {v0, v2}, Ljava/lang/Math;->min(FF)F

    move-result v0

    .line 465
    :cond_32
    add-int/lit8 v1, v1, 0x6

    goto :goto_4

    .line 471
    :cond_35
    return v0
.end method

.method private static clamp01(F)F
    .registers 2

    .line 647
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

    .line 611
    invoke-virtual {p0, p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->removeCallbacks(Ljava/lang/Runnable;)Z

    .line 612
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashFrameScheduled:Z

    .line 613
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 614
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    .line 615
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeft:[F

    .line 616
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    .line 617
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    .line 618
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRight:[F

    .line 619
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    .line 620
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    .line 621
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    .line 622
    new-array v1, v0, [F

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopLine:[F

    .line 623
    iput-boolean v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopActive:Z

    .line 624
    const/4 v0, 0x0

    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftProb:F

    .line 625
    const-string v1, "unknown"

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftType:Ljava/lang/String;

    .line 626
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftProb:F

    .line 627
    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftType:Ljava/lang/String;

    .line 628
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskLeft:F

    .line 629
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightProb:F

    .line 630
    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightType:Ljava/lang/String;

    .line 631
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskRight:F

    .line 632
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightProb:F

    .line 633
    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightType:Ljava/lang/String;

    .line 634
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeftProb:F

    .line 635
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRightProb:F

    .line 636
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    .line 637
    const-string v1, "none"

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuator:Ljava/lang/String;

    .line 638
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuatorLevel:F

    .line 639
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->accelerationPhase:F

    .line 640
    iput v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->brakePhase:F

    .line 641
    const-wide/16 v0, 0x0

    iput-wide v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    .line 642
    const/16 v0, 0x8

    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setVisibility(I)V

    .line 643
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->invalidate()V

    .line 644
    return-void
.end method

.method private drawAccelerationFlow(Landroid/graphics/Canvas;)V
    .registers 10

    .line 398
    iget v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuatorLevel:F

    const v1, 0x3f0ccccd    # 0.55f

    cmpl-float v0, v0, v1

    if-ltz v0, :cond_b

    const/4 v0, 0x2

    goto :goto_c

    :cond_b
    const/4 v0, 0x1

    .line 399
    :goto_c
    const v2, 0x3db851ec    # 0.09f

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuatorLevel:F

    mul-float v3, v3, v2

    const v2, 0x3e051eb8    # 0.13f

    add-float/2addr v3, v2

    .line 400
    const/high16 v2, 0x42ec0000    # 118.0f

    iget v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuatorLevel:F

    mul-float v4, v4, v2

    const/high16 v2, 0x42900000    # 72.0f

    add-float/2addr v4, v2

    invoke-static {v4}, Ljava/lang/Math;->round(F)I

    move-result v2

    .line 401
    const/4 v4, 0x0

    :goto_25
    if-ge v4, v0, :cond_47

    .line 402
    iget v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->accelerationPhase:F

    int-to-float v6, v4

    int-to-float v7, v0

    div-float/2addr v6, v7

    add-float/2addr v5, v6

    const/high16 v6, 0x3f800000    # 1.0f

    rem-float/2addr v5, v6

    .line 403
    const v6, 0x3fb9999a    # 1.45f

    mul-float v6, v6, v3

    div-int/lit8 v7, v2, 0x4

    invoke-direct {p0, p1, v5, v6, v7}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawWrappedFlowBand(Landroid/graphics/Canvas;FFI)V

    .line 404
    div-int/lit8 v6, v2, 0x2

    invoke-direct {p0, p1, v5, v3, v6}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawWrappedFlowBand(Landroid/graphics/Canvas;FFI)V

    .line 405
    mul-float v6, v3, v1

    invoke-direct {p0, p1, v5, v6, v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawWrappedFlowBand(Landroid/graphics/Canvas;FFI)V

    .line 401
    add-int/lit8 v4, v4, 0x1

    goto :goto_25

    .line 407
    :cond_47
    return-void
.end method

.method private drawBrakeChevron(Landroid/graphics/Canvas;FF)V
    .registers 11

    .line 503
    const v0, 0x3df5c28f    # 0.12f

    mul-float v0, v0, p3

    const v1, 0x3d8f5c29    # 0.07f

    invoke-static {v1, v0}, Ljava/lang/Math;->min(FF)F

    move-result v0

    add-float/2addr v0, p2

    invoke-static {p3, v0}, Ljava/lang/Math;->min(FF)F

    move-result p3

    .line 504
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowCenterPoint:[F

    invoke-direct {p0, p2, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pointOnCenter(F[F)V

    .line 505
    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowBackPoint:[F

    invoke-direct {p0, p3, p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pointOnCenter(F[F)V

    .line 506
    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowLeftPoint:[F

    invoke-static {p2, p3, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pointOnLine([FF[F)V

    .line 507
    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowRightPoint:[F

    invoke-static {p2, p3, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pointOnLine([FF[F)V

    .line 509
    nop

    .line 510
    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowBackPoint:[F

    const/4 p3, 0x0

    aget p2, p2, p3

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowLeftPoint:[F

    aget v0, v0, p3

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowBackPoint:[F

    aget v1, v1, p3

    sub-float/2addr v0, v1

    const v1, 0x3eae147b    # 0.34f

    mul-float v0, v0, v1

    add-float/2addr p2, v0

    .line 511
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowBackPoint:[F

    const/4 v2, 0x1

    aget v0, v0, v2

    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowLeftPoint:[F

    aget v3, v3, v2

    iget-object v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowBackPoint:[F

    aget v4, v4, v2

    sub-float/2addr v3, v4

    mul-float v3, v3, v1

    add-float/2addr v0, v3

    .line 512
    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowBackPoint:[F

    aget v3, v3, p3

    iget-object v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowRightPoint:[F

    aget v4, v4, p3

    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowBackPoint:[F

    aget v5, v5, p3

    sub-float/2addr v4, v5

    mul-float v4, v4, v1

    add-float/2addr v3, v4

    .line 513
    iget-object v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowBackPoint:[F

    aget v4, v4, v2

    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowRightPoint:[F

    aget v5, v5, v2

    iget-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowBackPoint:[F

    aget v6, v6, v2

    sub-float/2addr v5, v6

    mul-float v5, v5, v1

    add-float/2addr v4, v5

    .line 515
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowPath:Landroid/graphics/Path;

    invoke-virtual {v1}, Landroid/graphics/Path;->rewind()V

    .line 516
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowPath:Landroid/graphics/Path;

    invoke-virtual {v1, p2, v0}, Landroid/graphics/Path;->moveTo(FF)V

    .line 517
    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowPath:Landroid/graphics/Path;

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowCenterPoint:[F

    aget p3, v0, p3

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowCenterPoint:[F

    aget v0, v0, v2

    invoke-virtual {p2, p3, v0}, Landroid/graphics/Path;->lineTo(FF)V

    .line 518
    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowPath:Landroid/graphics/Path;

    invoke-virtual {p2, v3, v4}, Landroid/graphics/Path;->lineTo(FF)V

    .line 519
    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowPath:Landroid/graphics/Path;

    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->brakeFlowPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p2, p3}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 520
    return-void
.end method

.method private drawBrakeFlow(Landroid/graphics/Canvas;)V
    .registers 11

    .line 447
    iget v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuatorLevel:F

    const/high16 v1, 0x40000000    # 2.0f

    mul-float v0, v0, v1

    invoke-static {v0}, Ljava/lang/Math;->round(F)I

    move-result v0

    const/4 v1, 0x2

    invoke-static {v1, v0}, Ljava/lang/Math;->min(II)I

    move-result v0

    add-int/lit8 v0, v0, 0x1

    .line 448
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->brakeFlowEndProgress()F

    move-result v1

    .line 449
    const/high16 v2, 0x3e800000    # 0.25f

    mul-float v2, v2, v1

    const v3, 0x3da3d70a    # 0.08f

    invoke-static {v3, v2}, Ljava/lang/Math;->min(FF)F

    move-result v2

    .line 450
    sub-float v3, v1, v2

    .line 451
    const v4, 0x3d75c28f    # 0.06f

    cmpg-float v5, v3, v4

    if-gez v5, :cond_2a

    .line 452
    return-void

    .line 454
    :cond_2a
    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->brakeFlowPaint:Landroid/graphics/Paint;

    const/high16 v6, 0x42dc0000    # 110.0f

    iget v7, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuatorLevel:F

    mul-float v7, v7, v6

    const/high16 v6, 0x42fa0000    # 125.0f

    add-float/2addr v7, v6

    invoke-static {v7}, Ljava/lang/Math;->round(F)I

    move-result v6

    invoke-virtual {v5, v6}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 455
    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->brakeFlowPaint:Landroid/graphics/Paint;

    const v6, 0x3fe66666    # 1.8f

    iget v7, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuatorLevel:F

    mul-float v7, v7, v6

    const v6, 0x400ccccd    # 2.2f

    add-float/2addr v7, v6

    invoke-virtual {v5, v7}, Landroid/graphics/Paint;->setStrokeWidth(F)V

    .line 456
    const/4 v5, 0x0

    :goto_4d
    if-ge v5, v0, :cond_68

    .line 457
    iget v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->brakePhase:F

    int-to-float v7, v5

    int-to-float v8, v0

    div-float/2addr v7, v8

    add-float/2addr v6, v7

    const/high16 v7, 0x3f800000    # 1.0f

    rem-float/2addr v6, v7

    sub-float/2addr v7, v6

    .line 458
    const v6, 0x3f6147ae    # 0.88f

    mul-float v7, v7, v6

    add-float/2addr v7, v4

    mul-float v7, v7, v3

    add-float/2addr v7, v2

    .line 459
    invoke-direct {p0, p1, v7, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawBrakeChevron(Landroid/graphics/Canvas;FF)V

    .line 456
    add-int/lit8 v5, v5, 0x1

    goto :goto_4d

    .line 461
    :cond_68
    return-void
.end method

.method private drawFlowBand(Landroid/graphics/Canvas;FFI)V
    .registers 12

    .line 420
    const/high16 v0, 0x3f000000    # 0.5f

    mul-float p3, p3, v0

    sub-float v0, p2, p3

    const/4 v1, 0x0

    invoke-static {v1, v0}, Ljava/lang/Math;->max(FF)F

    move-result v0

    .line 421
    const/high16 v1, 0x3f800000    # 1.0f

    add-float/2addr p2, p3

    invoke-static {v1, p2}, Ljava/lang/Math;->min(FF)F

    move-result p2

    .line 422
    sub-float/2addr p2, v0

    const p3, 0x3c23d70a    # 0.01f

    cmpg-float p3, p2, p3

    if-gez p3, :cond_1b

    .line 423
    return-void

    .line 426
    :cond_1b
    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowPath:Landroid/graphics/Path;

    invoke-virtual {p3}, Landroid/graphics/Path;->rewind()V

    .line 427
    const/4 p3, 0x0

    const/4 v1, 0x0

    :goto_22
    const/high16 v2, 0x40c00000    # 6.0f

    const/4 v3, 0x6

    const/4 v4, 0x1

    if-gt v1, v3, :cond_54

    .line 428
    int-to-float v3, v1

    mul-float v3, v3, p2

    div-float/2addr v3, v2

    add-float/2addr v3, v0

    .line 429
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowLeftPoint:[F

    invoke-static {v2, v3, v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pointOnLine([FF[F)V

    .line 430
    if-nez v1, :cond_44

    .line 431
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowPath:Landroid/graphics/Path;

    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowLeftPoint:[F

    aget v3, v3, p3

    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowLeftPoint:[F

    aget v4, v5, v4

    invoke-virtual {v2, v3, v4}, Landroid/graphics/Path;->moveTo(FF)V

    goto :goto_51

    .line 433
    :cond_44
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowPath:Landroid/graphics/Path;

    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowLeftPoint:[F

    aget v3, v3, p3

    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowLeftPoint:[F

    aget v4, v5, v4

    invoke-virtual {v2, v3, v4}, Landroid/graphics/Path;->lineTo(FF)V

    .line 427
    :goto_51
    add-int/lit8 v1, v1, 0x1

    goto :goto_22

    .line 436
    :cond_54
    nop

    :goto_55
    if-ltz v3, :cond_73

    .line 437
    int-to-float v1, v3

    mul-float v1, v1, p2

    div-float/2addr v1, v2

    add-float/2addr v1, v0

    .line 438
    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    iget-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowRightPoint:[F

    invoke-static {v5, v1, v6}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pointOnLine([FF[F)V

    .line 439
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowPath:Landroid/graphics/Path;

    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowRightPoint:[F

    aget v5, v5, p3

    iget-object v6, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowRightPoint:[F

    aget v6, v6, v4

    invoke-virtual {v1, v5, v6}, Landroid/graphics/Path;->lineTo(FF)V

    .line 436
    add-int/lit8 v3, v3, -0x1

    goto :goto_55

    .line 441
    :cond_73
    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowPath:Landroid/graphics/Path;

    invoke-virtual {p2}, Landroid/graphics/Path;->close()V

    .line 442
    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->accelerationFlowPaint:Landroid/graphics/Paint;

    const/16 v0, 0xff

    invoke-static {p3, p4}, Ljava/lang/Math;->max(II)I

    move-result p3

    invoke-static {v0, p3}, Ljava/lang/Math;->min(II)I

    move-result p3

    invoke-virtual {p2, p3}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 443
    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowPath:Landroid/graphics/Path;

    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->accelerationFlowPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p2, p3}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 444
    return-void
.end method

.method private drawLane(Landroid/graphics/Canvas;[FFFLjava/lang/String;)V
    .registers 10

    .line 325
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_77

    const v0, 0x3d4ccccd    # 0.05f

    cmpg-float v0, p3, v0

    if-gez v0, :cond_e

    goto :goto_77

    .line 328
    :cond_e
    nop

    .line 329
    invoke-static {p4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p4

    const/high16 v0, 0x41200000    # 10.0f

    mul-float p4, p4, v0

    invoke-static {p4}, Ljava/lang/Math;->round(F)I

    move-result p4

    const/4 v0, 0x0

    invoke-static {v0, p4}, Ljava/lang/Math;->max(II)I

    move-result p4

    .line 328
    const/16 v1, 0xa

    invoke-static {v1, p4}, Ljava/lang/Math;->min(II)I

    move-result p4

    .line 330
    const/4 v1, 0x1

    if-eqz p5, :cond_33

    const-string v2, "center"

    invoke-virtual {p5, v2}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z

    move-result v2

    if-eqz v2, :cond_33

    const/4 v2, 0x1

    goto :goto_34

    :cond_33
    const/4 v2, 0x0

    .line 331
    :goto_34
    const-string v3, "solid"

    invoke-virtual {v3, p5}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v3

    if-nez v3, :cond_44

    const-string v3, "centerSolid"

    invoke-virtual {v3, p5}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p5

    if-eqz p5, :cond_45

    :cond_44
    const/4 v0, 0x1

    .line 332
    :cond_45
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    if-eqz v0, :cond_4b

    const/4 v0, 0x0

    goto :goto_4d

    :cond_4b
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneDashEffect:Landroid/graphics/DashPathEffect;

    :goto_4d
    invoke-virtual {p5, v0}, Landroid/graphics/Paint;->setPathEffect(Landroid/graphics/PathEffect;)Landroid/graphics/PathEffect;

    .line 333
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    .line 334
    if-eqz v2, :cond_59

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->centerLaneRiskFilters:[Landroid/graphics/LightingColorFilter;

    aget-object p4, v0, p4

    goto :goto_5d

    :cond_59
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskFilters:[Landroid/graphics/LightingColorFilter;

    aget-object p4, v0, p4

    .line 333
    :goto_5d
    invoke-virtual {p5, p4}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 335
    iget-object p4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    const/high16 p5, 0x43610000    # 225.0f

    mul-float p3, p3, p5

    const/high16 p5, 0x41f00000    # 30.0f

    add-float/2addr p3, p5

    float-to-int p3, p3

    invoke-virtual {p4, p3}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 336
    invoke-direct {p0, p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object p2

    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p2, p3}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 337
    return-void

    .line 326
    :cond_77
    :goto_77
    return-void
.end method

.method private drawLongitudinalFlow(Landroid/graphics/Canvas;)V
    .registers 4

    .line 387
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathAnimationActive()Z

    move-result v0

    if-nez v0, :cond_7

    .line 388
    return-void

    .line 390
    :cond_7
    const-string v0, "accelerator"

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuator:Ljava/lang/String;

    invoke-virtual {v0, v1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_15

    .line 391
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawAccelerationFlow(Landroid/graphics/Canvas;)V

    goto :goto_18

    .line 393
    :cond_15
    invoke-direct {p0, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawBrakeFlow(Landroid/graphics/Canvas;)V

    .line 395
    :goto_18
    return-void
.end method

.method private drawRoadEdge(Landroid/graphics/Canvas;[FF)V
    .registers 6

    .line 340
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_24

    const/high16 v0, 0x3f000000    # 0.5f

    cmpg-float v0, p3, v0

    if-gez v0, :cond_d

    goto :goto_24

    .line 343
    :cond_d
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    const/high16 v1, 0x43520000    # 210.0f

    mul-float p3, p3, v1

    const/high16 v1, 0x41c80000    # 25.0f

    add-float/2addr p3, v1

    float-to-int p3, p3

    invoke-virtual {v0, p3}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 344
    invoke-direct {p0, p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object p2

    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p2, p3}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 345
    return-void

    .line 341
    :cond_24
    :goto_24
    return-void
.end method

.method private drawTrafficStopLine(Landroid/graphics/Canvas;)V
    .registers 4

    .line 348
    iget-boolean v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopActive:Z

    if-eqz v0, :cond_1c

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopLine:[F

    array-length v0, v0

    const/4 v1, 0x4

    if-eq v0, v1, :cond_b

    goto :goto_1c

    .line 351
    :cond_b
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopLine:[F

    invoke-direct {p0, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v0

    .line 352
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopGlowPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 353
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0, v1}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 354
    return-void

    .line 349
    :cond_1c
    :goto_1c
    return-void
.end method

.method private drawVehicle(Landroid/graphics/Canvas;FFFIIF)V
    .registers 13

    .line 550
    const/high16 v0, 0x42a00000    # 80.0f

    div-float/2addr p4, v0

    const/high16 v0, 0x3f800000    # 1.0f

    sub-float/2addr v0, p4

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p4

    .line 551
    const/high16 v0, 0x423a0000    # 46.5f

    mul-float p4, p4, v0

    const/high16 v0, 0x41400000    # 12.0f

    add-float/2addr p4, v0

    .line 552
    const v0, 0x3fc66666    # 1.55f

    mul-float v0, v0, p4

    .line 554
    const/4 v1, 0x3

    const/16 v2, 0xff

    if-ne p5, v1, :cond_navdy_not_cutin

    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    const v1, -0xdfd8

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColor(I)V

    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleCutInFilter:Landroid/graphics/LightingColorFilter;

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    invoke-virtual {p5, v2}, Landroid/graphics/Paint;->setAlpha(I)V

    goto :goto_5e

    :cond_navdy_not_cutin
    const/4 v1, 0x2

    if-ne p5, v1, :cond_30

    .line 555
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    const v1, -0xff1a01

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColor(I)V

    .line 556
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleLongitudinalLeadFilter:Landroid/graphics/LightingColorFilter;

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 557
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    invoke-virtual {p5, v2}, Landroid/graphics/Paint;->setAlpha(I)V

    goto :goto_5e

    .line 558
    :cond_30
    const/4 v1, 0x1

    if-ne p5, v1, :cond_48

    .line 559
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    const v1, -0xff19ba

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColor(I)V

    .line 560
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleVisionFilter:Landroid/graphics/LightingColorFilter;

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 561
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    invoke-virtual {p5, v2}, Landroid/graphics/Paint;->setAlpha(I)V

    goto :goto_5e

    .line 563
    :cond_48
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    const v1, -0x22000001

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColor(I)V

    .line 564
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRadarFilter:Landroid/graphics/LightingColorFilter;

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setColorFilter(Landroid/graphics/ColorFilter;)Landroid/graphics/ColorFilter;

    .line 565
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    const/16 v1, 0xdd

    invoke-virtual {p5, v1}, Landroid/graphics/Paint;->setAlpha(I)V

    .line 568
    :goto_5e
    iget-object p5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRect:Landroid/graphics/RectF;

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

    invoke-virtual {p5, v2, v3, v1, p3}, Landroid/graphics/RectF;->set(FFFF)V

    .line 573
    invoke-direct {p0, p7, p6, p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleMarkerForYaw(FIF)Landroid/graphics/Bitmap;

    move-result-object p2

    .line 574
    if-eqz p2, :cond_87

    .line 575
    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRect:Landroid/graphics/RectF;

    iget-object p4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleBitmapPaint:Landroid/graphics/Paint;

    const/4 p5, 0x0

    invoke-virtual {p1, p2, p5, p3, p4}, Landroid/graphics/Canvas;->drawBitmap(Landroid/graphics/Bitmap;Landroid/graphics/Rect;Landroid/graphics/RectF;Landroid/graphics/Paint;)V

    goto :goto_93

    .line 577
    :cond_87
    iget-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRect:Landroid/graphics/RectF;

    const p3, 0x3e75c28f    # 0.24f

    mul-float p4, p4, p3

    iget-object p3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleFillPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, p2, p4, p4, p3}, Landroid/graphics/Canvas;->drawRoundRect(Landroid/graphics/RectF;FFLandroid/graphics/Paint;)V

    .line 579
    :goto_93
    return-void
.end method

.method private drawVehicles(Landroid/graphics/Canvas;)V
    .registers 13

    .line 540
    const/4 v0, 0x0

    :goto_1
    add-int/lit8 v1, v0, 0x5

    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    array-length v2, v2

    if-ge v1, v2, :cond_32

    .line 541
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

    .line 540
    add-int/lit8 v0, v0, 0x6

    goto :goto_1

    .line 545
    :cond_32
    return-void
.end method

.method private drawWrappedFlowBand(Landroid/graphics/Canvas;FFI)V
    .registers 8

    .line 411
    invoke-direct {p0, p1, p2, p3, p4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawFlowBand(Landroid/graphics/Canvas;FFI)V

    .line 412
    const/high16 v0, 0x3f000000    # 0.5f

    mul-float v0, v0, p3

    const/high16 v1, 0x3f800000    # 1.0f

    cmpg-float v2, p2, v0

    if-gez v2, :cond_12

    .line 413
    add-float/2addr p2, v1

    invoke-direct {p0, p1, p2, p3, p4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawFlowBand(Landroid/graphics/Canvas;FFI)V

    goto :goto_1c

    .line 414
    :cond_12
    sub-float v0, v1, v0

    cmpl-float v0, p2, v0

    if-lez v0, :cond_1c

    .line 415
    sub-float/2addr p2, v1

    invoke-direct {p0, p1, p2, p3, p4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawFlowBand(Landroid/graphics/Canvas;FFI)V

    .line 417
    :cond_1c
    :goto_1c
    return-void
.end method

.method private linePath([F)Landroid/graphics/Path;
    .registers 6

    .line 670
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->scratchPath:Landroid/graphics/Path;

    invoke-virtual {v0}, Landroid/graphics/Path;->rewind()V

    .line 671
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->scratchPath:Landroid/graphics/Path;

    const/4 v1, 0x0

    aget v1, p1, v1

    const/4 v2, 0x1

    aget v2, p1, v2

    invoke-virtual {v0, v1, v2}, Landroid/graphics/Path;->moveTo(FF)V

    .line 672
    const/4 v0, 0x2

    :goto_11
    array-length v1, p1

    if-ge v0, v1, :cond_22

    .line 673
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->scratchPath:Landroid/graphics/Path;

    aget v2, p1, v0

    add-int/lit8 v3, v0, 0x1

    aget v3, p1, v3

    invoke-virtual {v1, v2, v3}, Landroid/graphics/Path;->lineTo(FF)V

    .line 672
    add-int/lit8 v0, v0, 0x2

    goto :goto_11

    .line 675
    :cond_22
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->scratchPath:Landroid/graphics/Path;

    return-object p1
.end method

.method private loadVehicleMarker(Landroid/content/Context;Ljava/lang/String;)Landroid/graphics/Bitmap;
    .registers 5

    .line 170
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->getResources()Landroid/content/res/Resources;

    move-result-object v0

    .line 171
    invoke-virtual {p1}, Landroid/content/Context;->getPackageName()Ljava/lang/String;

    move-result-object p1

    .line 170
    const-string v1, "drawable"

    invoke-virtual {v0, p2, v1, p1}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I

    move-result p1

    .line 172
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

.method private pathAnimationActive()Z
    .registers 3

    .line 381
    iget v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuatorLevel:F

    const v1, 0x3d4ccccd    # 0.05f

    cmpl-float v0, v0, v1

    if-ltz v0, :cond_1f

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuator:Ljava/lang/String;

    .line 382
    const-string v1, "accelerator"

    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-nez v0, :cond_1d

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuator:Ljava/lang/String;

    .line 383
    const-string v1, "brake"

    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v0

    if-eqz v0, :cond_1f

    :cond_1d
    const/4 v0, 0x1

    goto :goto_20

    :cond_1f
    const/4 v0, 0x0

    .line 381
    :goto_20
    return v0
.end method

.method private pointOnCenter(F[F)V
    .registers 6

    .line 523
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowLeftPoint:[F

    invoke-static {v0, p1, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pointOnLine([FF[F)V

    .line 524
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowRightPoint:[F

    invoke-static {v0, p1, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pointOnLine([FF[F)V

    .line 525
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowLeftPoint:[F

    const/4 v0, 0x0

    aget p1, p1, v0

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowRightPoint:[F

    aget v1, v1, v0

    add-float/2addr p1, v1

    const/high16 v1, 0x3f000000    # 0.5f

    mul-float p1, p1, v1

    aput p1, p2, v0

    .line 526
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowLeftPoint:[F

    const/4 v0, 0x1

    aget p1, p1, v0

    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->flowRightPoint:[F

    aget v2, v2, v0

    add-float/2addr p1, v2

    mul-float p1, p1, v1

    aput p1, p2, v0

    .line 527
    return-void
.end method

.method private static pointOnLine([FF[F)V
    .registers 8

    .line 530
    array-length v0, p0

    div-int/lit8 v0, v0, 0x2

    .line 531
    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    add-int/lit8 v1, v0, -0x1

    int-to-float v1, v1

    mul-float p1, p1, v1

    .line 532
    add-int/lit8 v0, v0, -0x2

    float-to-int v1, p1

    const/4 v2, 0x0

    invoke-static {v2, v1}, Ljava/lang/Math;->max(II)I

    move-result v1

    invoke-static {v0, v1}, Ljava/lang/Math;->min(II)I

    move-result v0

    .line 533
    int-to-float v1, v0

    sub-float/2addr p1, v1

    .line 534
    mul-int/lit8 v0, v0, 0x2

    .line 535
    aget v1, p0, v0

    add-int/lit8 v3, v0, 0x2

    aget v3, p0, v3

    aget v4, p0, v0

    sub-float/2addr v3, v4

    mul-float v3, v3, p1

    add-float/2addr v1, v3

    aput v1, p2, v2

    .line 536
    add-int/lit8 v1, v0, 0x1

    aget v2, p0, v1

    add-int/lit8 v0, v0, 0x3

    aget v0, p0, v0

    aget p0, p0, v1

    sub-float/2addr v0, p0

    mul-float v0, v0, p1

    add-float/2addr v2, v0

    const/4 p0, 0x1

    aput v2, p2, p0

    .line 537
    return-void
.end method

.method private progressForScreenPoint(FF)F
    .registers 16

    .line 475
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    array-length v0, v0

    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    array-length v1, v1

    invoke-static {v0, v1}, Ljava/lang/Math;->min(II)I

    move-result v0

    div-int/lit8 v0, v0, 0x2

    .line 476
    nop

    .line 477
    nop

    .line 478
    const/high16 v1, 0x3f800000    # 1.0f

    const v2, 0x7f7fffff    # Float.MAX_VALUE

    const/4 v3, 0x0

    const/high16 v4, 0x3f800000    # 1.0f

    :goto_16
    add-int/lit8 v5, v3, 0x1

    if-ge v5, v0, :cond_8b

    .line 479
    mul-int/lit8 v6, v3, 0x2

    .line 480
    iget-object v7, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    aget v7, v7, v6

    iget-object v8, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    aget v8, v8, v6

    add-float/2addr v7, v8

    const/high16 v8, 0x3f000000    # 0.5f

    mul-float v7, v7, v8

    .line 481
    iget-object v9, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    add-int/lit8 v10, v6, 0x1

    aget v9, v9, v10

    iget-object v11, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    aget v10, v11, v10

    add-float/2addr v9, v10

    mul-float v9, v9, v8

    .line 482
    iget-object v10, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    add-int/lit8 v11, v6, 0x2

    aget v10, v10, v11

    iget-object v12, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    aget v11, v12, v11

    add-float/2addr v10, v11

    mul-float v10, v10, v8

    .line 483
    iget-object v11, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    add-int/lit8 v6, v6, 0x3

    aget v11, v11, v6

    iget-object v12, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    aget v6, v12, v6

    add-float/2addr v11, v6

    mul-float v11, v11, v8

    .line 484
    sub-float/2addr v10, v7

    .line 485
    sub-float/2addr v11, v9

    .line 486
    mul-float v6, v10, v10

    mul-float v8, v11, v11

    add-float/2addr v6, v8

    .line 487
    const v8, 0x3a83126f    # 0.001f

    cmpg-float v8, v6, v8

    if-gtz v8, :cond_60

    const/4 v6, 0x0

    goto :goto_6e

    :cond_60
    sub-float v8, p1, v7

    mul-float v8, v8, v10

    sub-float v12, p2, v9

    mul-float v12, v12, v11

    add-float/2addr v8, v12

    div-float/2addr v8, v6

    invoke-static {v8}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result v6

    .line 489
    :goto_6e
    mul-float v10, v10, v6

    add-float/2addr v7, v10

    .line 490
    mul-float v11, v11, v6

    add-float/2addr v9, v11

    .line 491
    sub-float v7, p1, v7

    .line 492
    sub-float v8, p2, v9

    .line 493
    mul-float v7, v7, v7

    mul-float v8, v8, v8

    add-float/2addr v7, v8

    .line 494
    cmpg-float v8, v7, v2

    if-gez v8, :cond_89

    .line 495
    nop

    .line 496
    int-to-float v2, v3

    add-float/2addr v2, v6

    int-to-float v3, v0

    sub-float/2addr v3, v1

    div-float v4, v2, v3

    move v2, v7

    .line 478
    :cond_89
    move v3, v5

    goto :goto_16

    .line 499
    :cond_8b
    return v4
.end method

.method private static readLaneType(Lorg/json/JSONObject;Ljava/lang/String;)Ljava/lang/String;
    .registers 3

    .line 651
    const-string v0, "unknown"

    invoke-virtual {p0, p1, v0}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p0

    .line 652
    const-string p1, "solid"

    invoke-virtual {p1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p1

    if-nez p1, :cond_28

    const-string p1, "dashed"

    invoke-virtual {p1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p1

    if-nez p1, :cond_28

    .line 653
    const-string p1, "centerSolid"

    invoke-virtual {p1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p1

    if-nez p1, :cond_28

    const-string p1, "centerDashed"

    invoke-virtual {p1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result p1

    if-eqz p1, :cond_27

    goto :goto_28

    .line 656
    :cond_27
    return-object v0

    .line 654
    :cond_28
    :goto_28
    return-object p0
.end method

.method private static readPoints(Lorg/json/JSONArray;)[F
    .registers 5

    .line 679
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

    .line 682
    :cond_13
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    new-array v1, v1, [F

    .line 683
    nop

    :goto_1a
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v2

    if-ge v0, v2, :cond_2c

    .line 684
    const-wide/16 v2, 0x0

    invoke-virtual {p0, v0, v2, v3}, Lorg/json/JSONArray;->optDouble(ID)D

    move-result-wide v2

    double-to-float v2, v2

    aput v2, v1, v0

    .line 683
    add-int/lit8 v0, v0, 0x1

    goto :goto_1a

    .line 686
    :cond_2c
    return-object v1

    .line 680
    :cond_2d
    :goto_2d
    new-array p0, v0, [F

    return-object p0
.end method

.method private static readVehicles(Lorg/json/JSONArray;)[F
    .registers 13

    .line 690
    const/4 v0, 0x0

    if-eqz p0, :cond_b7

    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    if-nez v1, :cond_b

    goto/16 :goto_b7

    .line 693
    :cond_b
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v1

    mul-int/lit8 v1, v1, 0x6

    new-array v2, v1, [F

    .line 694
    nop

    .line 695
    const/4 v3, 0x0

    const/4 v4, 0x0

    :goto_16
    invoke-virtual {p0}, Lorg/json/JSONArray;->length()I

    move-result v5

    if-ge v3, v5, :cond_ae

    .line 696
    invoke-virtual {p0, v3}, Lorg/json/JSONArray;->optJSONObject(I)Lorg/json/JSONObject;

    move-result-object v5

    .line 697
    if-nez v5, :cond_24

    .line 698
    goto/16 :goto_aa

    .line 700
    :cond_24
    const-string v6, "source"

    const-string v7, "radar"

    invoke-virtual {v5, v6, v7}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v6

    const-string v7, "cutInRisk"

    invoke-virtual {v5, v7, v0}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v7

    if-eqz v7, :cond_navdy_not_cutin_source

    const/4 v6, 0x3

    goto :goto_42

    :cond_navdy_not_cutin_source
    .line 701
    const-string v7, "longitudinalLead"

    invoke-virtual {v5, v7, v0}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result v7

    const/4 v8, 0x1

    if-eqz v7, :cond_37

    .line 702
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

    .line 703
    :goto_42
    const-string v7, "lane"

    const-string v9, "center"

    invoke-virtual {v5, v7, v9}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v7

    .line 704
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

    .line 705
    :goto_5e
    add-int/lit8 v7, v4, 0x1

    const-string v9, "screenX"

    const-wide/high16 v10, 0x4064000000000000L    # 160.0

    invoke-virtual {v5, v9, v10, v11}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v9

    double-to-float v9, v9

    aput v9, v2, v4

    .line 706
    add-int/lit8 v4, v7, 0x1

    const-string v9, "screenY"

    const-wide/high16 v10, 0x4020000000000000L    # 8.0

    invoke-virtual {v5, v9, v10, v11}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v9

    double-to-float v9, v9

    aput v9, v2, v7

    .line 707
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

    .line 708
    add-int/lit8 v4, v7, 0x1

    int-to-float v6, v6

    aput v6, v2, v7

    .line 709
    add-int/lit8 v6, v4, 0x1

    int-to-float v7, v8

    aput v7, v2, v4

    .line 710
    add-int/lit8 v4, v6, 0x1

    const-string v7, "yawDeg"

    invoke-virtual {v5, v7}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result v8

    if-eqz v8, :cond_a6

    .line 711
    const-wide/16 v8, 0x0

    invoke-virtual {v5, v7, v8, v9}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v7

    double-to-float v5, v7

    goto :goto_a8

    :cond_a6
    const/high16 v5, 0x7fc00000    # Float.NaN

    :goto_a8
    aput v5, v2, v6

    .line 695
    :goto_aa
    add-int/lit8 v3, v3, 0x1

    goto/16 :goto_16

    .line 713
    :cond_ae
    if-ne v4, v1, :cond_b1

    .line 714
    return-object v2

    .line 716
    :cond_b1
    new-array p0, v4, [F

    .line 717
    invoke-static {v2, v0, p0, v0, v4}, Ljava/lang/System;->arraycopy(Ljava/lang/Object;ILjava/lang/Object;II)V

    .line 718
    return-object p0

    .line 691
    :cond_b7
    :goto_b7
    new-array p0, v0, [F

    return-object p0
.end method

.method private scheduleDashFrame()V
    .registers 3

    .line 307
    iget-boolean v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashFrameScheduled:Z

    if-eqz v0, :cond_5

    .line 308
    return-void

    .line 310
    :cond_5
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashFrameScheduled:Z

    .line 311
    const-wide/16 v0, 0x42

    invoke-virtual {p0, p0, v0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 312
    return-void
.end method

.method private updateDashPhase()V
    .registers 8

    .line 357
    invoke-static {}, Landroid/os/SystemClock;->uptimeMillis()J

    move-result-wide v0

    .line 358
    iget-wide v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    const-wide/16 v4, 0x0

    cmp-long v6, v2, v4

    if-nez v6, :cond_f

    .line 359
    iput-wide v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    .line 360
    return-void

    .line 363
    :cond_f
    iget-wide v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    sub-long v2, v0, v2

    const-wide/16 v4, 0x96

    invoke-static {v2, v3, v4, v5}, Ljava/lang/Math;->min(JJ)J

    move-result-wide v2

    .line 364
    iput-wide v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lastDashFrameMs:J

    .line 365
    long-to-float v0, v2

    const/high16 v1, 0x447a0000    # 1000.0f

    div-float/2addr v0, v1

    .line 366
    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    const/high16 v2, 0x3f800000    # 1.0f

    cmpl-float v1, v1, v2

    if-lez v1, :cond_42

    .line 367
    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    const v3, 0x3f4ccccd    # 0.8f

    mul-float v1, v1, v3

    const/high16 v3, 0x41900000    # 18.0f

    invoke-static {v3, v1}, Ljava/lang/Math;->max(FF)F

    move-result v1

    const/high16 v3, 0x42a00000    # 80.0f

    invoke-static {v3, v1}, Ljava/lang/Math;->min(FF)F

    move-result v1

    .line 368
    iget v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashPhase:F

    mul-float v1, v1, v0

    add-float/2addr v4, v1

    rem-float/2addr v4, v3

    iput v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashPhase:F

    .line 371
    :cond_42
    const-string v1, "accelerator"

    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuator:Ljava/lang/String;

    invoke-virtual {v1, v3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_60

    .line 372
    const v1, 0x3f147ae1    # 0.58f

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuatorLevel:F

    mul-float v3, v3, v1

    const v1, 0x3e99999a    # 0.3f

    add-float/2addr v3, v1

    .line 373
    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->accelerationPhase:F

    mul-float v0, v0, v3

    add-float/2addr v1, v0

    rem-float/2addr v1, v2

    iput v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->accelerationPhase:F

    goto :goto_7e

    .line 374
    :cond_60
    const-string v1, "brake"

    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuator:Ljava/lang/String;

    invoke-virtual {v1, v3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_7e

    .line 375
    const v1, 0x3f1eb852    # 0.62f

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuatorLevel:F

    mul-float v3, v3, v1

    const v1, 0x3eae147b    # 0.34f

    add-float/2addr v3, v1

    .line 376
    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->brakePhase:F

    mul-float v0, v0, v3

    add-float/2addr v1, v0

    rem-float/2addr v1, v2

    iput v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->brakePhase:F

    goto :goto_7f

    .line 374
    :cond_7e
    :goto_7e
    nop

    .line 378
    :goto_7f
    return-void
.end method

.method private static validLine([F)Z
    .registers 3

    .line 722
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

    .line 582
    invoke-static {p1}, Ljava/lang/Float;->isNaN(F)Z

    move-result v0

    const/4 v1, 0x0

    const/high16 v2, 0x40800000    # 4.0f

    const/high16 v3, 0x41c00000    # 24.0f

    if-eqz v0, :cond_3b

    .line 583
    const/high16 p1, 0x43200000    # 160.0f

    sub-float/2addr p3, p1

    invoke-static {p3}, Ljava/lang/Math;->abs(F)F

    move-result p1

    .line 585
    cmpg-float p3, p1, v3

    if-ltz p3, :cond_37

    if-nez p2, :cond_19

    goto :goto_37

    .line 587
    :cond_19
    const/high16 p3, 0x42400000    # 48.0f

    cmpg-float p3, p1, p3

    if-gez p3, :cond_22

    .line 588
    const/high16 p1, 0x40800000    # 4.0f

    goto :goto_38

    .line 589
    :cond_22
    const/high16 p3, 0x42900000    # 72.0f

    cmpg-float p3, p1, p3

    if-gez p3, :cond_2b

    .line 590
    const/high16 p1, 0x41000000    # 8.0f

    goto :goto_38

    .line 591
    :cond_2b
    const/high16 p3, 0x42d00000    # 104.0f

    cmpg-float p1, p1, p3

    if-gez p1, :cond_34

    .line 592
    const/high16 p1, 0x41400000    # 12.0f

    goto :goto_38

    .line 594
    :cond_34
    const/high16 p1, 0x41800000    # 16.0f

    goto :goto_38

    .line 586
    :cond_37
    :goto_37
    const/4 p1, 0x0

    .line 596
    :goto_38
    if-gez p2, :cond_3b

    neg-float p1, p1

    .line 599
    :cond_3b
    invoke-static {p1}, Ljava/lang/Math;->abs(F)F

    move-result p2

    invoke-static {v3, p2}, Ljava/lang/Math;->min(FF)F

    move-result p2

    .line 600
    const/high16 p3, 0x40000000    # 2.0f

    cmpg-float p3, p2, p3

    if-gez p3, :cond_4c

    .line 601
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleMarkerBitmap:Landroid/graphics/Bitmap;

    return-object p1

    .line 603
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

    .line 604
    cmpg-float p1, p1, v1

    if-gez p1, :cond_66

    .line 605
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleLeftMarkerBitmaps:[Landroid/graphics/Bitmap;

    aget-object p1, p1, p2

    goto :goto_6a

    .line 606
    :cond_66
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleRightMarkerBitmaps:[Landroid/graphics/Bitmap;

    aget-object p1, p1, p2

    .line 607
    :goto_6a
    if-nez p1, :cond_6e

    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleMarkerBitmap:Landroid/graphics/Bitmap;

    :cond_6e
    return-object p1
.end method


# virtual methods
.method protected onDraw(Landroid/graphics/Canvas;)V
    .registers 9

    .line 274
    invoke-super/range {p0 .. p1}, Landroid/view/View;->onDraw(Landroid/graphics/Canvas;)V

    .line 275
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    invoke-static {v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v2

    if-eqz v2, :cond_b3

    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    invoke-static {v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v2

    if-nez v2, :cond_15

    goto/16 :goto_b3

    .line 279
    :cond_15
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    invoke-direct {p0, v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v2

    .line 280
    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    array-length v3, v3

    add-int/lit8 v3, v3, -0x2

    :goto_20
    if-ltz v3, :cond_32

    .line 281
    iget-object v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    aget v4, v4, v3

    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    add-int/lit8 v6, v3, 0x1

    aget v5, v5, v6

    invoke-virtual {v2, v4, v5}, Landroid/graphics/Path;->lineTo(FF)V

    .line 280
    add-int/lit8 v3, v3, -0x2

    goto :goto_20

    .line 283
    :cond_32
    invoke-virtual {v2}, Landroid/graphics/Path;->close()V

    .line 284
    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v2, v3}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 285
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->updateDashPhase()V

    .line 286
    invoke-direct/range {p0 .. p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLongitudinalFlow(Landroid/graphics/Canvas;)V

    .line 287
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    invoke-direct {p0, v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v2

    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v2, v3}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 288
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    invoke-direct {p0, v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->linePath([F)Landroid/graphics/Path;

    move-result-object v2

    iget-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v2, v3}, Landroid/graphics/Canvas;->drawPath(Landroid/graphics/Path;Landroid/graphics/Paint;)V

    .line 290
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeftProb:F

    invoke-direct {p0, p1, v2, v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawRoadEdge(Landroid/graphics/Canvas;[FF)V

    .line 291
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRightProb:F

    invoke-direct {p0, p1, v2, v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawRoadEdge(Landroid/graphics/Canvas;[FF)V

    .line 293
    new-instance v2, Landroid/graphics/DashPathEffect;

    sget-object v3, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->LANE_DASH_PATTERN:[F

    iget v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashPhase:F

    invoke-direct {v2, v3, v4}, Landroid/graphics/DashPathEffect;-><init>([FF)V

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneDashEffect:Landroid/graphics/DashPathEffect;

    .line 294
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeft:[F

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftProb:F

    const/4 v4, 0x0

    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftType:Ljava/lang/String;

    move-object v0, p0

    move-object v1, p1

    invoke-direct/range {v0 .. v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLane(Landroid/graphics/Canvas;[FFFLjava/lang/String;)V

    .line 295
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftProb:F

    iget v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskLeft:F

    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftType:Ljava/lang/String;

    invoke-direct/range {v0 .. v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLane(Landroid/graphics/Canvas;[FFFLjava/lang/String;)V

    .line 296
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightProb:F

    iget v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskRight:F

    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightType:Ljava/lang/String;

    invoke-direct/range {v0 .. v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLane(Landroid/graphics/Canvas;[FFFLjava/lang/String;)V

    .line 297
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRight:[F

    iget v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightProb:F

    const/4 v4, 0x0

    iget-object v5, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightType:Ljava/lang/String;

    invoke-direct/range {v0 .. v5}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawLane(Landroid/graphics/Canvas;[FFFLjava/lang/String;)V

    .line 298
    invoke-direct/range {p0 .. p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawTrafficStopLine(Landroid/graphics/Canvas;)V

    .line 299
    invoke-direct/range {p0 .. p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->drawVehicles(Landroid/graphics/Canvas;)V

    .line 301
    iget v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    const/high16 v2, 0x3f800000    # 1.0f

    cmpl-float v1, v1, v2

    if-gtz v1, :cond_af

    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathAnimationActive()Z

    move-result v1

    if-eqz v1, :cond_b2

    .line 302
    :cond_af
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->scheduleDashFrame()V

    .line 304
    :cond_b2
    return-void

    .line 276
    :cond_b3
    :goto_b3
    return-void
.end method

.method protected onSizeChanged(IIII)V
    .registers 13

    .line 262
    invoke-super {p0, p1, p2, p3, p4}, Landroid/view/View;->onSizeChanged(IIII)V

    .line 263
    int-to-float v4, p2

    .line 264
    new-instance v0, Landroid/graphics/LinearGradient;

    const/4 v6, -0x1

    sget-object v7, Landroid/graphics/Shader$TileMode;->CLAMP:Landroid/graphics/Shader$TileMode;

    const/4 v1, 0x0

    const/4 v2, 0x0

    const/4 v3, 0x0

    const v5, 0x55ffffff    # 3.518437E13f

    invoke-direct/range {v0 .. v7}, Landroid/graphics/LinearGradient;-><init>(FFFFIILandroid/graphics/Shader$TileMode;)V

    .line 266
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->lanePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setShader(Landroid/graphics/Shader;)Landroid/graphics/Shader;

    .line 267
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgePaint:Landroid/graphics/Paint;

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setShader(Landroid/graphics/Shader;)Landroid/graphics/Shader;

    .line 268
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathFillPaint:Landroid/graphics/Paint;

    new-instance v0, Landroid/graphics/LinearGradient;

    const v6, -0x66ff19ba

    sget-object v7, Landroid/graphics/Shader$TileMode;->CLAMP:Landroid/graphics/Shader$TileMode;

    const v5, 0x1100e646

    invoke-direct/range {v0 .. v7}, Landroid/graphics/LinearGradient;-><init>(FFFFIILandroid/graphics/Shader$TileMode;)V

    invoke-virtual {p1, v0}, Landroid/graphics/Paint;->setShader(Landroid/graphics/Shader;)Landroid/graphics/Shader;

    .line 270
    return-void
.end method

.method public run()V
    .registers 3

    .line 316
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->dashFrameScheduled:Z

    .line 317
    iget v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    const/high16 v1, 0x3f800000    # 1.0f

    cmpl-float v0, v0, v1

    if-gtz v0, :cond_11

    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathAnimationActive()Z

    move-result v0

    if-eqz v0, :cond_2a

    :cond_11
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->getVisibility()I

    move-result v0

    if-nez v0, :cond_2a

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 318
    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_2a

    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v0

    if-eqz v0, :cond_2a

    .line 319
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->invalidate()V

    .line 321
    :cond_2a
    return-void
.end method

.method public updatePayload(Ljava/lang/String;Z)V
    .registers 4

    .line 176
    if-nez p1, :cond_6

    .line 177
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V

    .line 178
    return-void

    .line 182
    :cond_6
    :try_start_6
    new-instance v0, Lorg/json/JSONObject;

    invoke-direct {v0, p1}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    invoke-virtual {p0, v0, p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->updatePayload(Lorg/json/JSONObject;Z)V
    :try_end_e
    .catch Ljava/lang/Exception; {:try_start_6 .. :try_end_e} :catch_f

    .line 185
    goto :goto_13

    .line 183
    :catch_f
    move-exception p1

    .line 184
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V

    .line 186
    :goto_13
    return-void
.end method

.method public updatePayload(Lorg/json/JSONObject;Z)V
    .registers 14

    .line 189
    const-string v0, "navPathLeft"

    const-string v1, "navLaneRiskRight"

    const-string v2, "navLaneRiskLeft"

    const-string v3, "navVehicles"

    const-string v4, "navTrafficStopLine"

    if-eqz p2, :cond_191

    if-nez p1, :cond_10

    goto/16 :goto_191

    .line 195
    :cond_10
    :try_start_10
    const-string p2, "vEgoKph"

    const-wide/16 v5, 0x0

    invoke-virtual {p1, p2, v5, v6}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v7

    double-to-float p2, v7

    const/4 v7, 0x0

    invoke-static {v7, p2}, Ljava/lang/Math;->max(FF)F

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicleSpeedKph:F

    .line 196
    const-string p2, "longitudinalActuator"

    const-string v7, "none"

    invoke-virtual {p1, p2, v7}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    iput-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuator:Ljava/lang/String;

    .line 197
    const-string p2, "longitudinalActuatorLevel"

    .line 198
    invoke-virtual {p1, p2, v5, v6}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v7

    double-to-float p2, v7

    .line 197
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->longitudinalActuatorLevel:F

    .line 199
    const-string p2, "trafficStopActive"

    const/4 v7, 0x0

    invoke-virtual {p1, p2, v7}, Lorg/json/JSONObject;->optBoolean(Ljava/lang/String;Z)Z

    move-result p2

    iput-boolean p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopActive:Z

    .line 200
    iget-boolean p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopActive:Z

    if-nez p2, :cond_49

    .line 201
    new-array p2, v7, [F

    iput-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopLine:[F

    goto :goto_59

    .line 202
    :cond_49
    invoke-virtual {p1, v4}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result p2

    if-eqz p2, :cond_59

    .line 203
    invoke-virtual {p1, v4}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object p2

    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object p2

    iput-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->trafficStopLine:[F

    .line 205
    :cond_59
    :goto_59
    invoke-virtual {p1, v3}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result p2

    if-eqz p2, :cond_69

    .line 206
    invoke-virtual {p1, v3}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object p2

    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readVehicles(Lorg/json/JSONArray;)[F

    move-result-object p2

    iput-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->vehicles:[F

    .line 208
    :cond_69
    invoke-virtual {p1, v2}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result p2

    if-eqz p2, :cond_7a

    .line 209
    invoke-virtual {p1, v2, v5, v6}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v2

    double-to-float p2, v2

    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskLeft:F

    .line 211
    :cond_7a
    invoke-virtual {p1, v1}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result p2

    if-eqz p2, :cond_8b

    .line 212
    invoke-virtual {p1, v1, v5, v6}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v1

    double-to-float p2, v1

    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRiskRight:F

    .line 214
    :cond_8b
    invoke-virtual {p1, v0}, Lorg/json/JSONObject;->has(Ljava/lang/String;)Z

    move-result p2

    if-nez p2, :cond_9b

    .line 215
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->getVisibility()I

    move-result p1

    if-nez p1, :cond_9a

    .line 216
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->invalidate()V

    .line 218
    :cond_9a
    return-void

    .line 221
    :cond_9b
    invoke-virtual {p1, v0}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object p2

    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object p2

    .line 222
    const-string v0, "navPathRight"

    invoke-virtual {p1, v0}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v0

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v0

    .line 223
    const-string v1, "navLaneFarLeft"

    invoke-virtual {p1, v1}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v1

    invoke-static {v1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v1

    .line 224
    const-string v2, "navLaneLeft"

    invoke-virtual {p1, v2}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v2

    invoke-static {v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v2

    .line 225
    const-string v3, "navLaneRight"

    invoke-virtual {p1, v3}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v3

    invoke-static {v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v3

    .line 226
    const-string v4, "navLaneFarRight"

    invoke-virtual {p1, v4}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v4

    invoke-static {v4}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v4

    .line 227
    const-string v8, "navRoadEdgeLeft"

    invoke-virtual {p1, v8}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v8

    invoke-static {v8}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v8

    .line 228
    const-string v9, "navRoadEdgeRight"

    invoke-virtual {p1, v9}, Lorg/json/JSONObject;->optJSONArray(Ljava/lang/String;)Lorg/json/JSONArray;

    move-result-object v9

    invoke-static {v9}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readPoints(Lorg/json/JSONArray;)[F

    move-result-object v9

    .line 229
    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v10

    if-eqz v10, :cond_188

    invoke-static {v0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v10

    if-eqz v10, :cond_188

    .line 230
    invoke-static {v2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v10

    if-eqz v10, :cond_188

    invoke-static {v3}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->validLine([F)Z

    move-result v10

    if-nez v10, :cond_103

    goto/16 :goto_188

    .line 235
    :cond_103
    iput-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathLeft:[F

    .line 236
    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->pathRight:[F

    .line 237
    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeft:[F

    .line 238
    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeft:[F

    .line 239
    iput-object v3, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRight:[F

    .line 240
    iput-object v4, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRight:[F

    .line 241
    iput-object v8, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeft:[F

    .line 242
    iput-object v9, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRight:[F

    .line 243
    const-string p2, "navLaneFarLeftProb"

    invoke-virtual {p1, p2, v5, v6}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p2, v0

    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftProb:F

    .line 244
    const-string p2, "navLaneLeftProb"

    invoke-virtual {p1, p2, v5, v6}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p2, v0

    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftProb:F

    .line 245
    const-string p2, "navLaneRightProb"

    invoke-virtual {p1, p2, v5, v6}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p2, v0

    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightProb:F

    .line 246
    const-string p2, "navLaneFarRightProb"

    invoke-virtual {p1, p2, v5, v6}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p2, v0

    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightProb:F

    .line 247
    const-string p2, "navLaneFarLeftType"

    invoke-static {p1, p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readLaneType(Lorg/json/JSONObject;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    iput-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarLeftType:Ljava/lang/String;

    .line 248
    const-string p2, "navLaneLeftType"

    invoke-static {p1, p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readLaneType(Lorg/json/JSONObject;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    iput-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneLeftType:Ljava/lang/String;

    .line 249
    const-string p2, "navLaneRightType"

    invoke-static {p1, p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readLaneType(Lorg/json/JSONObject;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    iput-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneRightType:Ljava/lang/String;

    .line 250
    const-string p2, "navLaneFarRightType"

    invoke-static {p1, p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->readLaneType(Lorg/json/JSONObject;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p2

    iput-object p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->laneFarRightType:Ljava/lang/String;

    .line 251
    const-string p2, "navRoadEdgeLeftProb"

    invoke-virtual {p1, p2, v5, v6}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide v0

    double-to-float p2, v0

    invoke-static {p2}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p2

    iput p2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeLeftProb:F

    .line 252
    const-string p2, "navRoadEdgeRightProb"

    invoke-virtual {p1, p2, v5, v6}, Lorg/json/JSONObject;->optDouble(Ljava/lang/String;D)D

    move-result-wide p1

    double-to-float p1, p1

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clamp01(F)F

    move-result p1

    iput p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->roadEdgeRightProb:F

    .line 253
    invoke-virtual {p0, v7}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->setVisibility(I)V

    .line 254
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->invalidate()V

    .line 257
    goto :goto_190

    .line 231
    :cond_188
    :goto_188
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V
    :try_end_18b
    .catch Ljava/lang/Exception; {:try_start_10 .. :try_end_18b} :catch_18c

    .line 232
    return-void

    .line 255
    :catch_18c
    move-exception p1

    .line 256
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V

    .line 258
    :goto_190
    return-void

    .line 190
    :cond_191
    :goto_191
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotPathView;->clearGeometry()V

    .line 191
    return-void
.end method
