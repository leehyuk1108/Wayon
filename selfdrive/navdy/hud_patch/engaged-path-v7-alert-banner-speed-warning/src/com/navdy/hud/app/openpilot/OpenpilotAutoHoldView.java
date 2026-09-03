package com.navdy.hud.app.openpilot;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.view.View;

import org.json.JSONObject;

public final class OpenpilotAutoHoldView extends View {
  private static final int COLOR_PROGRESS = 0xff39ff70;
  private static final float RING_CENTER_X = 26.0f;
  private static final float RING_RADIUS = 21.0f;
  private static final float RING_WIDTH = 3.0f;

  private final Paint ringPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
  private final RectF ringBounds = new RectF();
  private float progress;

  public OpenpilotAutoHoldView(Context context) {
    super(context);
    ringPaint.setStyle(Paint.Style.STROKE);
    ringPaint.setStrokeCap(Paint.Cap.ROUND);
    ringPaint.setStrokeWidth(RING_WIDTH);
    setWillNotDraw(false);
    setVisibility(GONE);
  }

  public void updatePayload(JSONObject root) {
    boolean active = root != null && root.optBoolean("autoHoldActive", false);
    progress = root == null ? 0.0f : clamp01(
        (float) root.optDouble("autoHoldEpbProgress", 0.0));
    setVisibility(active ? VISIBLE : GONE);
    if (active) {
      invalidate();
    }
  }

  @Override
  protected void onDraw(Canvas canvas) {
    super.onDraw(canvas);
    float centerY = getHeight() * 0.5f;
    ringBounds.set(RING_CENTER_X - RING_RADIUS, centerY - RING_RADIUS,
        RING_CENTER_X + RING_RADIUS, centerY + RING_RADIUS);

    ringPaint.setColor(Color.argb(70, 255, 255, 255));
    canvas.drawArc(ringBounds, -90.0f, 360.0f, false, ringPaint);
    if (progress > 0.0f) {
      ringPaint.setColor(COLOR_PROGRESS);
      canvas.drawArc(ringBounds, -90.0f, 360.0f * progress, false, ringPaint);
    }
  }

  private static float clamp01(float value) {
    return Math.max(0.0f, Math.min(1.0f, value));
  }
}
