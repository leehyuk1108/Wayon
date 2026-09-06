package com.navdy.hud.app.openpilot;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.os.SystemClock;
import android.view.View;

import org.json.JSONObject;

import java.util.Locale;

public final class OpenpilotAutoHoldView extends View {
  private static final int COLOR_PROGRESS = Color.rgb(58, 255, 112);
  private static final float RING_RADIUS = 21.0f;
  private static final float RING_WIDTH = 3.0f;
  private static final float TIMER_X = 60.0f;

  private final Paint ringPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
  private final Paint textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
  private final RectF ringBounds = new RectF();
  private float elapsedSeconds;
  private float progress;
  private boolean active;
  private long startedAtMs;

  public OpenpilotAutoHoldView(Context context) {
    super(context);
    ringPaint.setStyle(Paint.Style.STROKE);
    ringPaint.setStrokeCap(Paint.Cap.ROUND);
    ringPaint.setStrokeWidth(RING_WIDTH);
    textPaint.setColor(Color.WHITE);
    textPaint.setTextSize(30.0f);
    textPaint.setTypeface(Typeface.DEFAULT_BOLD);
    textPaint.setTextAlign(Paint.Align.LEFT);
    setWillNotDraw(false);
    setVisibility(GONE);
  }

  public void updatePayload(JSONObject json) {
    boolean nextActive = json != null
        && json.optBoolean("autoHoldActive", json.optBoolean("standstill", false));
    long now = SystemClock.elapsedRealtime();

    if (nextActive) {
      if (!active || startedAtMs <= 0L) {
        startedAtMs = now;
      }
      double reportedElapsed = json.optDouble("autoHoldElapsedSec", -1.0);
      elapsedSeconds = reportedElapsed >= 0.0
          ? Math.max(0.0f, (float) reportedElapsed)
          : Math.max(0.0f, (now - startedAtMs) / 1000.0f);
    } else {
      startedAtMs = 0L;
      elapsedSeconds = 0.0f;
    }

    active = nextActive;
    progress = json == null ? 0.0f
        : clamp01((float) json.optDouble("autoHoldEpbProgress", 0.0));
    setVisibility(active ? VISIBLE : GONE);
    if (active) {
      invalidate();
    }
  }

  @Override
  protected void onDraw(Canvas canvas) {
    super.onDraw(canvas);
    float centerY = getHeight() * 0.5f;
    ringBounds.set(5.0f, centerY - RING_RADIUS, 47.0f, centerY + RING_RADIUS);

    ringPaint.setColor(Color.argb(70, 255, 255, 255));
    canvas.drawArc(ringBounds, -90.0f, 360.0f, false, ringPaint);
    if (progress > 0.0f) {
      ringPaint.setColor(COLOR_PROGRESS);
      canvas.drawArc(ringBounds, -90.0f, 360.0f * progress, false, ringPaint);
    }

    int totalSeconds = Math.max(0, (int) elapsedSeconds);
    String timer = String.format(Locale.US, "%02d:%02d", totalSeconds / 60, totalSeconds % 60);
    Paint.FontMetrics metrics = textPaint.getFontMetrics();
    float baseline = centerY - (metrics.ascent + metrics.descent) * 0.5f;
    canvas.drawText(timer, TIMER_X, baseline, textPaint);
  }

  private static float clamp01(float value) {
    return Math.max(0.0f, Math.min(1.0f, value));
  }
}
