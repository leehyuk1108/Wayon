package com.navdy.hud.app.openpilot;

import android.content.Context;
import android.util.AttributeSet;

import com.navdy.hud.app.view.FontTextView;

public class OpenpilotOutsideTempView extends FontTextView {
  public OpenpilotOutsideTempView(Context context) {
    super(context);
    OpenpilotStateReceiver.bindOutsideTempView(this);
  }

  public OpenpilotOutsideTempView(Context context, AttributeSet attrs) {
    super(context, attrs);
    OpenpilotStateReceiver.bindOutsideTempView(this);
  }

  public OpenpilotOutsideTempView(Context context, AttributeSet attrs, int defStyleAttr) {
    super(context, attrs, defStyleAttr);
    OpenpilotStateReceiver.bindOutsideTempView(this);
  }
}
