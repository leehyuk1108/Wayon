.class public Lcom/navdy/hud/app/openpilot/OpenpilotOutsideTempView;
.super Lcom/navdy/hud/app/view/FontTextView;
.source "OpenpilotOutsideTempView.java"


# direct methods
.method public constructor <init>(Landroid/content/Context;)V
    .locals 0

    invoke-direct {p0, p1}, Lcom/navdy/hud/app/view/FontTextView;-><init>(Landroid/content/Context;)V

    invoke-static {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->bindOutsideTempView(Landroid/widget/TextView;)V

    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;)V
    .locals 0

    invoke-direct {p0, p1, p2}, Lcom/navdy/hud/app/view/FontTextView;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;)V

    invoke-static {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->bindOutsideTempView(Landroid/widget/TextView;)V

    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V
    .locals 0

    invoke-direct {p0, p1, p2, p3}, Lcom/navdy/hud/app/view/FontTextView;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V

    invoke-static {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotStateReceiver;->bindOutsideTempView(Landroid/widget/TextView;)V

    return-void
.end method
