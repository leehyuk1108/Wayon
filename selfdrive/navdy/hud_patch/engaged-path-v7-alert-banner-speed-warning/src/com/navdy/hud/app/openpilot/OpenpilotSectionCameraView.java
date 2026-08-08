package com.navdy.hud.app.openpilot;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.os.SystemClock;
import android.view.View;
import org.json.JSONObject;

public final class OpenpilotSectionCameraView extends View {
  private static final int WHITE = Color.WHITE;
  private static final int BLACK = Color.rgb(17, 17, 17);
  private static final int RED = Color.rgb(229, 61, 54);
  private static final int YELLOW = Color.rgb(255, 191, 47);
  private static final int GREEN = Color.rgb(53, 208, 111);
  private static final int TRACK = Color.argb(72, 255, 255, 255);

  private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
  private int limitKph;
  private double averageKph;
  private double progress;
  private double remainingM;
  private boolean adjusting;

  public OpenpilotSectionCameraView(Context context) {
    super(context);
    paint.setTypeface(android.graphics.Typeface.create("sans", android.graphics.Typeface.BOLD));
    setVisibility(GONE);
  }

  public void updatePayload(String payload, int cameraSpeedKph, boolean sectionCamera) {
    try {
      updatePayload(new JSONObject(payload), cameraSpeedKph, sectionCamera);
    } catch (Exception ignored) {
      updatePayload((JSONObject) null, cameraSpeedKph, sectionCamera);
    }
  }

  public void updatePayload(JSONObject root, int cameraSpeedKph, boolean sectionCamera) {
    boolean visible = sectionCamera && cameraSpeedKph > 0;
    if (!visible) {
      setVisibility(GONE);
      adjusting = false;
      return;
    }

    limitKph = cameraSpeedKph;
    try {
      if (root == null) {
        throw new IllegalArgumentException("missing section payload");
      }
      double payloadLimit = root.optDouble("sectionLimitKph", cameraSpeedKph);
      if (payloadLimit >= 20.0 && payloadLimit <= 140.0) {
        limitKph = (int) Math.round(payloadLimit);
      }
      averageKph = Math.max(0.0, root.optDouble("sectionAverageKph", 0.0));
      progress = clamp(root.optDouble("sectionProgress", 0.0));
      remainingM = Math.max(0.0, root.optDouble("sectionRemainingM", 0.0));
      adjusting = root.optBoolean("automaticAccActive", false)
          && !root.optBoolean("automaticAccAtTarget", false);
    } catch (Exception ignored) {
      averageKph = 0.0;
      progress = 0.0;
      remainingM = 0.0;
      adjusting = false;
    }

    setVisibility(VISIBLE);
    invalidate();
  }

  private static double clamp(double value) {
    return Math.max(0.0, Math.min(1.0, value));
  }

  private static String formatDistance(double meters) {
    if (meters >= 1000.0) {
      return String.format(java.util.Locale.US, "%.1fkm", meters / 1000.0);
    }
    return meters > 0.0 ? String.format(java.util.Locale.US, "%.0fm", meters) : "--";
  }

  private void drawCentered(Canvas canvas, String text, float x, float baseline) {
    paint.setTextAlign(Paint.Align.CENTER);
    canvas.drawText(text, x, baseline, paint);
  }

  @Override
  protected void onDraw(Canvas canvas) {
    super.onDraw(canvas);
    final float cx = getWidth() * 0.5f;

    paint.setStyle(Paint.Style.FILL);
    paint.setColor(YELLOW);
    paint.setTextSize(11.0f);
    paint.setFakeBoldText(true);
    drawCentered(canvas, "구간단속", cx, 12.0f);

    paint.setColor(WHITE);
    canvas.drawCircle(cx, 47.0f, 29.0f, paint);
    paint.setStyle(Paint.Style.STROKE);
    paint.setStrokeWidth(5.0f);
    paint.setColor(RED);
    canvas.drawCircle(cx, 47.0f, 27.0f, paint);

    paint.setStyle(Paint.Style.FILL);
    paint.setColor(BLACK);
    paint.setTextSize(limitKph >= 100 ? 26.0f : 30.0f);
    paint.setFakeBoldText(true);
    Paint.FontMetrics speedMetrics = paint.getFontMetrics();
    float speedBaseline = 47.0f - (speedMetrics.ascent + speedMetrics.descent) * 0.5f;
    drawCentered(canvas, Integer.toString(limitKph), cx, speedBaseline);

    paint.setTextSize(10.0f);
    paint.setFakeBoldText(true);
    paint.setColor(averageKph > limitKph ? Color.rgb(255, 82, 77)
        : averageKph >= limitKph - 3.0 ? YELLOW : WHITE);
    String average = averageKph > 0.0 ? "평균 " + Math.round(averageKph) : "평균 --";
    paint.setTextAlign(Paint.Align.RIGHT);
    canvas.drawText(average, cx - 3.0f, 86.0f, paint);

    paint.setColor(Color.argb(220, 255, 255, 255));
    paint.setTextAlign(Paint.Align.LEFT);
    canvas.drawText(formatDistance(remainingM), cx + 3.0f, 86.0f, paint);

    RectF track = new RectF(12.0f, 96.0f, getWidth() - 12.0f, 100.0f);
    paint.setColor(TRACK);
    canvas.drawRoundRect(track, 2.0f, 2.0f, paint);
    int fillColor = averageKph > limitKph ? Color.rgb(255, 82, 77)
        : averageKph >= limitKph - 3.0 ? YELLOW : GREEN;
    int alpha = 255;
    if (adjusting) {
      double wave = (Math.sin(SystemClock.uptimeMillis() / 180.0) + 1.0) * 0.5;
      alpha = 105 + (int) (150.0 * wave);
      postInvalidateDelayed(80L);
    }
    paint.setColor(fillColor);
    paint.setAlpha(alpha);
    RectF fill = new RectF(12.0f, 96.0f,
        12.0f + (getWidth() - 24.0f) * (float) progress, 100.0f);
    canvas.drawRoundRect(fill, 2.0f, 2.0f, paint);
    paint.setAlpha(255);
  }
}
