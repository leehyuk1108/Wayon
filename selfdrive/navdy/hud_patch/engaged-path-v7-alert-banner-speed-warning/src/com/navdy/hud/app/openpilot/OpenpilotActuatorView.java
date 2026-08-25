package com.navdy.hud.app.openpilot;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.PorterDuff;
import android.graphics.PorterDuffColorFilter;
import android.graphics.RectF;
import android.view.View;

import org.json.JSONObject;

public final class OpenpilotActuatorView extends View {
  private static final int ACTUATOR_NONE = 0;
  private static final int ACTUATOR_ACCELERATOR = 1;
  private static final int ACTUATOR_BRAKE = 2;
  private static final int COLOR_ACCELERATOR = 0xff2f8cff;
  private static final int COLOR_BRAKE = 0xffff3b30;
  private static final float MAX_ICON_SIZE_PX = 18.0f;
  private static final float INDICATOR_RADIUS_PX = 16.0f;

  private final Bitmap acceleratorBitmap;
  private final Bitmap brakeBitmap;
  private final Paint bitmapPaint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
  private final Paint fillPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
  private final RectF destination = new RectF();
  private final PorterDuffColorFilter iconFilter =
      new PorterDuffColorFilter(0xffffffff, PorterDuff.Mode.SRC_IN);
  private int actuator;
  private float level;

  public OpenpilotActuatorView(Context context) {
    super(context);
    acceleratorBitmap = loadBitmap(context, "navdy_accelerator_pedal");
    brakeBitmap = loadBitmap(context, "navdy_brake_pedal");
    fillPaint.setStyle(Paint.Style.FILL);
    setWillNotDraw(false);
    setVisibility(GONE);
  }

  private Bitmap loadBitmap(Context context, String name) {
    int resourceId = getResources().getIdentifier(name, "drawable", context.getPackageName());
    return resourceId == 0 ? null : BitmapFactory.decodeResource(getResources(), resourceId);
  }

  public void updatePayload(JSONObject root, boolean active) {
    actuator = ACTUATOR_NONE;
    level = 0.0f;
    if (active && root != null) {
      String value = root.optString("longitudinalActuator", "none");
      if ("accelerator".equals(value)) {
        actuator = ACTUATOR_ACCELERATOR;
      } else if ("brake".equals(value)) {
        actuator = ACTUATOR_BRAKE;
      }
      level = clamp01((float) root.optDouble("longitudinalActuatorLevel", 0.0));
    }

    setVisibility(active ? VISIBLE : GONE);
    if (active) {
      invalidate();
    }
  }

  @Override
  protected void onDraw(Canvas canvas) {
    super.onDraw(canvas);
    float centerY = getHeight() * 0.5f;
    float brakeCenterX = getWidth() * 0.25f;
    float acceleratorCenterX = getWidth() * 0.75f;
    drawIndicator(canvas, brakeCenterX, centerY,
        actuator == ACTUATOR_BRAKE, COLOR_BRAKE);
    drawIndicator(canvas, acceleratorCenterX, centerY,
        actuator == ACTUATOR_ACCELERATOR, COLOR_ACCELERATOR);
    drawIcon(canvas, brakeBitmap, brakeCenterX, centerY,
        actuator == ACTUATOR_BRAKE);
    drawIcon(canvas, acceleratorBitmap, acceleratorCenterX, centerY,
        actuator == ACTUATOR_ACCELERATOR);
  }

  private void drawIndicator(Canvas canvas, float centerX, float centerY,
      boolean selected, int color) {
    if (!selected) {
      return;
    }

    fillPaint.setColor(color);
    fillPaint.setAlpha(175 + Math.round(level * 55.0f));
    canvas.drawCircle(centerX, centerY, INDICATOR_RADIUS_PX, fillPaint);
  }

  private void drawIcon(Canvas canvas, Bitmap bitmap, float centerX, float centerY,
      boolean selected) {
    if (bitmap == null || bitmap.getWidth() <= 0 || bitmap.getHeight() <= 0) {
      return;
    }

    float scale = Math.min(MAX_ICON_SIZE_PX / bitmap.getWidth(),
        MAX_ICON_SIZE_PX / bitmap.getHeight());
    float width = bitmap.getWidth() * scale;
    float height = bitmap.getHeight() * scale;
    float left = centerX - width * 0.5f;
    float top = centerY - height * 0.5f;
    destination.set(left, top, left + width, top + height);

    bitmapPaint.setColorFilter(iconFilter);
    bitmapPaint.setAlpha(selected ? 255 : 180);
    canvas.drawBitmap(bitmap, null, destination, bitmapPaint);
  }

  private static float clamp01(float value) {
    return Math.max(0.0f, Math.min(1.0f, value));
  }
}
