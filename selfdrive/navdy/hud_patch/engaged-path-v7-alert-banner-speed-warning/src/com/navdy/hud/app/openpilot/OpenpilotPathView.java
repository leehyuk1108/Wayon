package com.navdy.hud.app.openpilot;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.DashPathEffect;
import android.graphics.LinearGradient;
import android.graphics.LightingColorFilter;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.graphics.Shader;
import android.os.SystemClock;
import android.view.View;

import org.json.JSONArray;
import org.json.JSONObject;

public final class OpenpilotPathView extends View {
  private static final int COLOR_GREEN = 0xff00e646;
  private static final int COLOR_LANE_CLEAR = 0xffffffff;
  private static final int COLOR_LANE_CENTER = 0xffffd43b;
  private static final int COLOR_LANE_DANGER = 0xffff2028;
  private static final int COLOR_VEHICLE_RADAR = 0xddffffff;
  private static final int COLOR_VEHICLE_VISION = 0xff00e646;
  private static final int COLOR_VEHICLE_FUSED = 0xff00e5ff;
  private static final float[] LANE_DASH_PATTERN = {56.0f, 24.0f};
  private static final float LANE_DASH_CYCLE = 80.0f;
  private static final float ROAD_EDGE_MIN_CONFIDENCE = 0.5f;
  private static final int LANE_RISK_FILTER_STEPS = 10;
  private static final long DASH_FRAME_MS = 66L;

  private final Paint lanePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
  private final Paint roadEdgePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
  private final Paint pathEdgePaint = new Paint(Paint.ANTI_ALIAS_FLAG);
  private final Paint pathFillPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
  private final Paint vehicleFillPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
  private final Paint vehicleBitmapPaint = new Paint(
      Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
  private final LightingColorFilter[] laneRiskFilters =
      new LightingColorFilter[LANE_RISK_FILTER_STEPS + 1];
  private final LightingColorFilter[] centerLaneRiskFilters =
      new LightingColorFilter[LANE_RISK_FILTER_STEPS + 1];
  private final LightingColorFilter vehicleRadarFilter = new LightingColorFilter(0xffffffff, 0);
  private final LightingColorFilter vehicleVisionFilter = new LightingColorFilter(
      COLOR_VEHICLE_VISION, 0);
  private final LightingColorFilter vehicleFusedFilter = new LightingColorFilter(
      COLOR_VEHICLE_FUSED, 0);
  private final Bitmap vehicleMarkerBitmap;
  private final Bitmap[] vehicleLeftMarkerBitmaps;
  private final Bitmap[] vehicleRightMarkerBitmaps;
  private float[] laneFarLeft = new float[0];
  private float laneFarLeftProb;
  private String laneFarLeftType = "unknown";
  private float[] laneLeft = new float[0];
  private float laneLeftProb;
  private String laneLeftType = "unknown";
  private float laneRiskLeft;
  private float[] laneRight = new float[0];
  private float laneRightProb;
  private String laneRightType = "unknown";
  private float laneRiskRight;
  private float[] laneFarRight = new float[0];
  private float laneFarRightProb;
  private String laneFarRightType = "unknown";
  private float[] pathLeft = new float[0];
  private float[] pathRight = new float[0];
  private float[] roadEdgeLeft = new float[0];
  private float roadEdgeLeftProb;
  private float[] roadEdgeRight = new float[0];
  private float roadEdgeRightProb;
  private float[] vehicles = new float[0];
  private DashPathEffect laneDashEffect;
  private float dashPhase;
  private long lastDashFrameMs;
  private float vehicleSpeedKph;

  public OpenpilotPathView(Context context) {
    super(context);

    lanePaint.setStyle(Paint.Style.STROKE);
    lanePaint.setStrokeCap(Paint.Cap.ROUND);
    lanePaint.setStrokeJoin(Paint.Join.ROUND);
    lanePaint.setStrokeWidth(3.2f);
    for (int index = 0; index <= LANE_RISK_FILTER_STEPS; index++) {
      float risk = index / (float) LANE_RISK_FILTER_STEPS;
      laneRiskFilters[index] = new LightingColorFilter(blendColor(
          COLOR_LANE_CLEAR, COLOR_LANE_DANGER, risk), 0);
      centerLaneRiskFilters[index] = new LightingColorFilter(blendColor(
          COLOR_LANE_CENTER, COLOR_LANE_DANGER, risk), 0);
    }

    roadEdgePaint.setStyle(Paint.Style.STROKE);
    roadEdgePaint.setStrokeCap(Paint.Cap.ROUND);
    roadEdgePaint.setStrokeJoin(Paint.Join.ROUND);
    roadEdgePaint.setStrokeWidth(2.8f);
    roadEdgePaint.setAlpha(115);
    roadEdgePaint.setColorFilter(new LightingColorFilter(COLOR_LANE_DANGER, 0));

    pathEdgePaint.setColor(COLOR_GREEN);
    pathEdgePaint.setStyle(Paint.Style.STROKE);
    pathEdgePaint.setStrokeJoin(Paint.Join.ROUND);
    pathEdgePaint.setStrokeWidth(1.8f);

    pathFillPaint.setStyle(Paint.Style.FILL);

    vehicleFillPaint.setStyle(Paint.Style.FILL);
    vehicleMarkerBitmap = loadVehicleMarker(context, "navdy_vehicle_marker");
    vehicleLeftMarkerBitmaps = new Bitmap[] {
        loadVehicleMarker(context, "navdy_vehicle_marker_left_4"),
        loadVehicleMarker(context, "navdy_vehicle_marker_left_8"),
        loadVehicleMarker(context, "navdy_vehicle_marker_left_12"),
        loadVehicleMarker(context, "navdy_vehicle_marker_left_16"),
        loadVehicleMarker(context, "navdy_vehicle_marker_left_20"),
        loadVehicleMarker(context, "navdy_vehicle_marker_left_24"),
    };
    vehicleRightMarkerBitmaps = new Bitmap[] {
        loadVehicleMarker(context, "navdy_vehicle_marker_right_4"),
        loadVehicleMarker(context, "navdy_vehicle_marker_right_8"),
        loadVehicleMarker(context, "navdy_vehicle_marker_right_12"),
        loadVehicleMarker(context, "navdy_vehicle_marker_right_16"),
        loadVehicleMarker(context, "navdy_vehicle_marker_right_20"),
        loadVehicleMarker(context, "navdy_vehicle_marker_right_24"),
    };
    setWillNotDraw(false);
    setVisibility(View.GONE);
  }

  private Bitmap loadVehicleMarker(Context context, String name) {
    int markerId = getResources().getIdentifier(
        name, "drawable", context.getPackageName());
    return markerId == 0 ? null : BitmapFactory.decodeResource(getResources(), markerId);
  }

  public void updatePayload(String payload, boolean active) {
    if (!active || payload == null) {
      clearGeometry();
      return;
    }

    try {
      JSONObject json = new JSONObject(payload);
      vehicleSpeedKph = Math.max(0.0f, (float) json.optDouble("vEgoKph", 0.0));
      if (json.has("navVehicles")) {
        vehicles = readVehicles(json.optJSONArray("navVehicles"));
      }
      if (json.has("navLaneRiskLeft")) {
        laneRiskLeft = clamp01((float) json.optDouble("navLaneRiskLeft", 0.0));
      }
      if (json.has("navLaneRiskRight")) {
        laneRiskRight = clamp01((float) json.optDouble("navLaneRiskRight", 0.0));
      }
      if (!json.has("navPathLeft")) {
        if (getVisibility() == View.VISIBLE) {
          invalidate();
        }
        return;
      }

      float[] nextPathLeft = readPoints(json.optJSONArray("navPathLeft"));
      float[] nextPathRight = readPoints(json.optJSONArray("navPathRight"));
      float[] nextLaneFarLeft = readPoints(json.optJSONArray("navLaneFarLeft"));
      float[] nextLaneLeft = readPoints(json.optJSONArray("navLaneLeft"));
      float[] nextLaneRight = readPoints(json.optJSONArray("navLaneRight"));
      float[] nextLaneFarRight = readPoints(json.optJSONArray("navLaneFarRight"));
      float[] nextRoadEdgeLeft = readPoints(json.optJSONArray("navRoadEdgeLeft"));
      float[] nextRoadEdgeRight = readPoints(json.optJSONArray("navRoadEdgeRight"));
      if (!validLine(nextPathLeft) || !validLine(nextPathRight)
          || !validLine(nextLaneLeft) || !validLine(nextLaneRight)) {
        clearGeometry();
        return;
      }

      pathLeft = nextPathLeft;
      pathRight = nextPathRight;
      laneFarLeft = nextLaneFarLeft;
      laneLeft = nextLaneLeft;
      laneRight = nextLaneRight;
      laneFarRight = nextLaneFarRight;
      roadEdgeLeft = nextRoadEdgeLeft;
      roadEdgeRight = nextRoadEdgeRight;
      laneFarLeftProb = clamp01((float) json.optDouble("navLaneFarLeftProb", 0.0));
      laneLeftProb = clamp01((float) json.optDouble("navLaneLeftProb", 0.0));
      laneRightProb = clamp01((float) json.optDouble("navLaneRightProb", 0.0));
      laneFarRightProb = clamp01((float) json.optDouble("navLaneFarRightProb", 0.0));
      laneFarLeftType = readLaneType(json, "navLaneFarLeftType");
      laneLeftType = readLaneType(json, "navLaneLeftType");
      laneRightType = readLaneType(json, "navLaneRightType");
      laneFarRightType = readLaneType(json, "navLaneFarRightType");
      roadEdgeLeftProb = clamp01((float) json.optDouble("navRoadEdgeLeftProb", 0.0));
      roadEdgeRightProb = clamp01((float) json.optDouble("navRoadEdgeRightProb", 0.0));
      setVisibility(View.VISIBLE);
      invalidate();
    } catch (Exception ignored) {
      clearGeometry();
    }
  }

  @Override
  protected void onSizeChanged(int width, int height, int oldWidth, int oldHeight) {
    super.onSizeChanged(width, height, oldWidth, oldHeight);
    float h = height;
    Shader lineGradient = new LinearGradient(
        0.0f, 0.0f, 0.0f, h, 0x55ffffff, 0xffffffff, Shader.TileMode.CLAMP);
    lanePaint.setShader(lineGradient);
    roadEdgePaint.setShader(lineGradient);
    pathFillPaint.setShader(new LinearGradient(
        0.0f, 0.0f, 0.0f, h, 0x1100e646, 0x9900e646, Shader.TileMode.CLAMP));
  }

  @Override
  protected void onDraw(Canvas canvas) {
    super.onDraw(canvas);
    if (!validLine(pathLeft) || !validLine(pathRight)) {
      return;
    }

    Path path = linePath(pathLeft);
    for (int index = pathRight.length - 2; index >= 0; index -= 2) {
      path.lineTo(pathRight[index], pathRight[index + 1]);
    }
    path.close();
    canvas.drawPath(path, pathFillPaint);
    canvas.drawPath(linePath(pathLeft), pathEdgePaint);
    canvas.drawPath(linePath(pathRight), pathEdgePaint);

    drawRoadEdge(canvas, roadEdgeLeft, roadEdgeLeftProb);
    drawRoadEdge(canvas, roadEdgeRight, roadEdgeRightProb);

    updateDashPhase();
    laneDashEffect = new DashPathEffect(LANE_DASH_PATTERN, dashPhase);
    drawLane(canvas, laneFarLeft, laneFarLeftProb, 0.0f, laneFarLeftType);
    drawLane(canvas, laneLeft, laneLeftProb, laneRiskLeft, laneLeftType);
    drawLane(canvas, laneRight, laneRightProb, laneRiskRight, laneRightType);
    drawLane(canvas, laneFarRight, laneFarRightProb, 0.0f, laneFarRightType);
    drawVehicles(canvas);

    if (vehicleSpeedKph > 1.0f) {
      postInvalidateDelayed(DASH_FRAME_MS);
    }
  }

  private void drawLane(
      Canvas canvas, float[] points, float probability, float risk, String type) {
    if (!validLine(points) || probability < 0.05f) {
      return;
    }
    int filterIndex = Math.min(LANE_RISK_FILTER_STEPS,
        Math.max(0, Math.round(clamp01(risk) * LANE_RISK_FILTER_STEPS)));
    boolean centerline = type != null && type.startsWith("center");
    boolean solid = "solid".equals(type) || "centerSolid".equals(type);
    lanePaint.setPathEffect(solid ? null : laneDashEffect);
    lanePaint.setColorFilter(
        centerline ? centerLaneRiskFilters[filterIndex] : laneRiskFilters[filterIndex]);
    lanePaint.setAlpha((int) (probability * 225.0f + 30.0f));
    canvas.drawPath(linePath(points), lanePaint);
  }

  private void drawRoadEdge(Canvas canvas, float[] points, float confidence) {
    if (!validLine(points) || confidence < ROAD_EDGE_MIN_CONFIDENCE) {
      return;
    }
    roadEdgePaint.setAlpha((int) (confidence * 210.0f + 25.0f));
    canvas.drawPath(linePath(points), roadEdgePaint);
  }

  private void updateDashPhase() {
    long now = SystemClock.uptimeMillis();
    if (lastDashFrameMs == 0L) {
      lastDashFrameMs = now;
      return;
    }

    long elapsedMs = Math.min(now - lastDashFrameMs, 150L);
    lastDashFrameMs = now;
    if (vehicleSpeedKph <= 1.0f) {
      return;
    }

    float pixelsPerSecond = Math.min(80.0f, Math.max(18.0f, vehicleSpeedKph * 0.8f));
    dashPhase = (dashPhase + elapsedMs * pixelsPerSecond / 1000.0f) % LANE_DASH_CYCLE;
  }

  private void drawVehicles(Canvas canvas) {
    for (int index = 0; index + 5 < vehicles.length; index += 6) {
      drawVehicle(canvas, vehicles[index], vehicles[index + 1],
          vehicles[index + 2], (int) vehicles[index + 3], (int) vehicles[index + 4],
          vehicles[index + 5]);
    }
  }

  private void drawVehicle(
      Canvas canvas, float centerX, float centerY, float distanceM, int source, int lane,
      float yawDeg) {
    float nearScale = clamp01(1.0f - distanceM / 80.0f);
    float width = 12.0f + nearScale * 46.5f;
    float height = width * 1.55f;

    if (source == 2) {
      vehicleFillPaint.setColor(COLOR_VEHICLE_FUSED);
      vehicleBitmapPaint.setColorFilter(vehicleFusedFilter);
      vehicleBitmapPaint.setAlpha(255);
    } else if (source == 1) {
      vehicleFillPaint.setColor(COLOR_VEHICLE_VISION);
      vehicleBitmapPaint.setColorFilter(vehicleVisionFilter);
      vehicleBitmapPaint.setAlpha(255);
    } else {
      vehicleFillPaint.setColor(COLOR_VEHICLE_RADAR);
      vehicleBitmapPaint.setColorFilter(vehicleRadarFilter);
      vehicleBitmapPaint.setAlpha(221);
    }

    RectF destination = new RectF(
        centerX - width * 0.82f,
        centerY - height * 0.55f,
        centerX + width * 0.82f,
        centerY + height * 0.45f);
    Bitmap marker = vehicleMarkerForYaw(yawDeg, lane, centerX);
    if (marker != null) {
      canvas.drawBitmap(marker, null, destination, vehicleBitmapPaint);
    } else {
      canvas.drawRoundRect(destination, width * 0.24f, width * 0.24f, vehicleFillPaint);
    }
  }

  private Bitmap vehicleMarkerForYaw(float yawDeg, int lane, float centerX) {
    if (Float.isNaN(yawDeg)) {
      float centerDistance = Math.abs(centerX - 160.0f);
      float fallbackYaw;
      if (centerDistance < 24.0f || lane == 0) {
        fallbackYaw = 0.0f;
      } else if (centerDistance < 48.0f) {
        fallbackYaw = 4.0f;
      } else if (centerDistance < 72.0f) {
        fallbackYaw = 8.0f;
      } else if (centerDistance < 104.0f) {
        fallbackYaw = 12.0f;
      } else {
        fallbackYaw = 16.0f;
      }
      yawDeg = lane < 0 ? -fallbackYaw : fallbackYaw;
    }

    float absoluteYaw = Math.min(24.0f, Math.abs(yawDeg));
    if (absoluteYaw < 2.0f) {
      return vehicleMarkerBitmap;
    }
    int angleIndex = Math.min(5, Math.max(0, Math.round(absoluteYaw / 4.0f) - 1));
    Bitmap marker = yawDeg < 0.0f
        ? vehicleLeftMarkerBitmaps[angleIndex]
        : vehicleRightMarkerBitmaps[angleIndex];
    return marker == null ? vehicleMarkerBitmap : marker;
  }

  private void clearGeometry() {
    pathLeft = new float[0];
    pathRight = new float[0];
    laneFarLeft = new float[0];
    laneLeft = new float[0];
    laneRight = new float[0];
    laneFarRight = new float[0];
    roadEdgeLeft = new float[0];
    roadEdgeRight = new float[0];
    vehicles = new float[0];
    laneFarLeftProb = 0.0f;
    laneFarLeftType = "unknown";
    laneLeftProb = 0.0f;
    laneLeftType = "unknown";
    laneRiskLeft = 0.0f;
    laneRightProb = 0.0f;
    laneRightType = "unknown";
    laneRiskRight = 0.0f;
    laneFarRightProb = 0.0f;
    laneFarRightType = "unknown";
    roadEdgeLeftProb = 0.0f;
    roadEdgeRightProb = 0.0f;
    vehicleSpeedKph = 0.0f;
    lastDashFrameMs = 0L;
    setVisibility(View.GONE);
    invalidate();
  }

  private static float clamp01(float value) {
    return Math.max(0.0f, Math.min(1.0f, value));
  }

  private static String readLaneType(JSONObject json, String key) {
    String type = json.optString(key, "unknown");
    if ("solid".equals(type) || "dashed".equals(type)
        || "centerSolid".equals(type) || "centerDashed".equals(type)) {
      return type;
    }
    return "unknown";
  }

  private static int blendColor(int from, int to, float amount) {
    float ratio = clamp01(amount);
    int red = Math.round(((from >> 16) & 0xff) * (1.0f - ratio)
        + ((to >> 16) & 0xff) * ratio);
    int green = Math.round(((from >> 8) & 0xff) * (1.0f - ratio)
        + ((to >> 8) & 0xff) * ratio);
    int blue = Math.round((from & 0xff) * (1.0f - ratio) + (to & 0xff) * ratio);
    return 0xff000000 | (red << 16) | (green << 8) | blue;
  }

  private static Path linePath(float[] points) {
    Path path = new Path();
    path.moveTo(points[0], points[1]);
    for (int index = 2; index < points.length; index += 2) {
      path.lineTo(points[index], points[index + 1]);
    }
    return path;
  }

  private static float[] readPoints(JSONArray json) {
    if (json == null || json.length() < 4 || (json.length() & 1) != 0) {
      return new float[0];
    }
    float[] points = new float[json.length()];
    for (int index = 0; index < json.length(); index++) {
      points[index] = (float) json.optDouble(index, 0.0);
    }
    return points;
  }

  private static float[] readVehicles(JSONArray json) {
    if (json == null || json.length() == 0) {
      return new float[0];
    }
    float[] values = new float[json.length() * 6];
    int output = 0;
    for (int index = 0; index < json.length(); index++) {
      JSONObject vehicle = json.optJSONObject(index);
      if (vehicle == null) {
        continue;
      }
      String source = vehicle.optString("source", "radar");
      int sourceCode = "fused".equals(source) ? 2 : ("vision".equals(source) ? 1 : 0);
      String lane = vehicle.optString("lane", "center");
      int laneCode = "left".equals(lane) ? -1 : ("right".equals(lane) ? 1 : 0);
      values[output++] = (float) vehicle.optDouble("screenX", 160.0);
      values[output++] = (float) vehicle.optDouble("screenY", 8.0);
      values[output++] = Math.max(0.0f, (float) vehicle.optDouble("distanceM", 80.0));
      values[output++] = sourceCode;
      values[output++] = laneCode;
      values[output++] = vehicle.has("yawDeg")
          ? (float) vehicle.optDouble("yawDeg", 0.0) : Float.NaN;
    }
    if (output == values.length) {
      return values;
    }
    float[] trimmed = new float[output];
    System.arraycopy(values, 0, trimmed, 0, output);
    return trimmed;
  }

  private static boolean validLine(float[] points) {
    return points != null && points.length >= 4 && (points.length & 1) == 0;
  }
}
