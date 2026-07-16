package com.navdy.hud.app.openpilot;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.json.JSONObject;

public final class OpenpilotAlertBannerView extends FrameLayout {
  private static final int BANNER_HEIGHT = 100;
  private static final long SHOW_DURATION_MS = 240;
  private static final long HIDE_DURATION_MS = 180;

  private final TextView titleView;
  private final TextView subtitleView;
  private final GradientDrawable background;
  private String currentKey = "";
  private boolean showing;

  public OpenpilotAlertBannerView(Context context) {
    super(context);
    setClickable(false);
    setFocusable(false);
    setVisibility(View.GONE);
    setTranslationY(-BANNER_HEIGHT);

    background = new GradientDrawable();
    background.setColor(Color.argb(160, 0, 0, 0));
    setBackground(background);

    LinearLayout textContainer = new LinearLayout(context);
    textContainer.setOrientation(LinearLayout.VERTICAL);
    textContainer.setGravity(Gravity.CENTER);
    textContainer.setPadding(22, 7, 22, 8);

    titleView = new TextView(context);
    titleView.setTextColor(Color.WHITE);
    titleView.setTextSize(0, 27.0f);
    titleView.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
    titleView.setGravity(Gravity.CENTER);
    titleView.setIncludeFontPadding(false);
    titleView.setSingleLine(true);
    titleView.setEllipsize(android.text.TextUtils.TruncateAt.END);

    subtitleView = new TextView(context);
    subtitleView.setTextColor(Color.argb(235, 255, 255, 255));
    subtitleView.setTextSize(0, 18.0f);
    subtitleView.setGravity(Gravity.CENTER);
    subtitleView.setIncludeFontPadding(false);
    subtitleView.setSingleLine(true);
    subtitleView.setEllipsize(android.text.TextUtils.TruncateAt.END);

    textContainer.addView(titleView, new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, 55));
    textContainer.addView(subtitleView, new LinearLayout.LayoutParams(
        LinearLayout.LayoutParams.MATCH_PARENT, 30));
    addView(textContainer, new FrameLayout.LayoutParams(
        FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT));
  }

  public void updatePayload(String payload) {
    if (payload == null) {
      hideBanner();
      return;
    }

    try {
      JSONObject json = new JSONObject(payload);
      String title = json.optString("alertText1", "").trim();
      String subtitle = json.optString("alertText2", "").trim();
      String type = json.optString("alertType", "");
      String status = json.optString("alertStatus", "normal");
      String size = json.optString("alertSize", "none");

      if (type.startsWith("resumeRequired") || title.startsWith("Resume 버튼")) {
        hideBanner();
        return;
      }

      if ((title.length() == 0 && subtitle.length() == 0) || "none".equalsIgnoreCase(size)) {
        hideBanner();
        return;
      }

      String key = type + '\n' + status + '\n' + title + '\n' + subtitle;
      if (showing && key.equals(currentKey)) {
        return;
      }

      currentKey = key;
      titleView.setText(title.length() > 0 ? title : subtitle);
      subtitleView.setText(title.length() > 0 ? subtitle : "");
      subtitleView.setVisibility(title.length() > 0 && subtitle.length() > 0 ? View.VISIBLE : View.GONE);
      background.setColor(backgroundColor(status));
      showBanner();
    } catch (Exception ignored) {
      hideBanner();
    }
  }

  private static int backgroundColor(String status) {
    if ("critical".equalsIgnoreCase(status)) {
      return Color.argb(180, 255, 0, 21);
    }
    if ("userPrompt".equalsIgnoreCase(status)) {
      return Color.argb(170, 255, 115, 0);
    }
    return Color.argb(160, 0, 0, 0);
  }

  private void showBanner() {
    boolean wasShowing = showing && getVisibility() == View.VISIBLE;
    showing = true;
    animate().cancel();
    setVisibility(View.VISIBLE);
    setAlpha(1.0f);
    if (wasShowing) {
      setTranslationY(0.0f);
      return;
    }
    setTranslationY(-BANNER_HEIGHT);
    animate().translationY(0.0f).setDuration(SHOW_DURATION_MS).setListener(null).start();
  }

  private void hideBanner() {
    if (!showing && getVisibility() != View.VISIBLE) {
      return;
    }
    showing = false;
    currentKey = "";
    animate().cancel();
    animate().translationY(-BANNER_HEIGHT).setDuration(HIDE_DURATION_MS)
        .setListener(new AnimatorListenerAdapter() {
          @Override
          public void onAnimationEnd(Animator animation) {
            if (!showing) {
              setVisibility(View.GONE);
            }
          }
        }).start();
  }
}
