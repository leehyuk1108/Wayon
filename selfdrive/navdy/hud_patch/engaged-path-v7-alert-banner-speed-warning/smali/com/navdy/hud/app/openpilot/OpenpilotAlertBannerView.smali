.class public final Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;
.super Landroid/widget/FrameLayout;
.source "OpenpilotAlertBannerView.java"


# static fields
.field private static final BANNER_HEIGHT:I = 0x64

.field private static final HIDE_DURATION_MS:J = 0xb4L

.field private static final SHOW_DURATION_MS:J = 0xf0L


# instance fields
.field private final background:Landroid/graphics/drawable/GradientDrawable;

.field private currentKey:Ljava/lang/String;

.field private showing:Z

.field private final subtitleView:Landroid/widget/TextView;

.field private final titleView:Landroid/widget/TextView;


# direct methods
.method public constructor <init>(Landroid/content/Context;)V
    .registers 9

    .line 29
    invoke-direct {p0, p1}, Landroid/widget/FrameLayout;-><init>(Landroid/content/Context;)V

    .line 25
    const-string v0, ""

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->currentKey:Ljava/lang/String;

    .line 30
    const/4 v0, 0x0

    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->setClickable(Z)V

    .line 31
    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->setFocusable(Z)V

    .line 32
    const/16 v1, 0x8

    invoke-virtual {p0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->setVisibility(I)V

    .line 33
    const/high16 v2, -0x3d380000    # -100.0f

    invoke-virtual {p0, v2}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->setTranslationY(F)V

    .line 35
    new-instance v2, Landroid/graphics/drawable/GradientDrawable;

    invoke-direct {v2}, Landroid/graphics/drawable/GradientDrawable;-><init>()V

    iput-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->background:Landroid/graphics/drawable/GradientDrawable;

    .line 36
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->background:Landroid/graphics/drawable/GradientDrawable;

    const/16 v3, 0xe6

    invoke-static {v3, v0, v0, v0}, Landroid/graphics/Color;->argb(IIII)I

    move-result v3

    invoke-virtual {v2, v3}, Landroid/graphics/drawable/GradientDrawable;->setColor(I)V

    .line 37
    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->background:Landroid/graphics/drawable/GradientDrawable;

    invoke-virtual {p0, v2}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->setBackground(Landroid/graphics/drawable/Drawable;)V

    .line 39
    new-instance v2, Landroid/widget/LinearLayout;

    invoke-direct {v2, p1}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    .line 40
    const/4 v3, 0x1

    invoke-virtual {v2, v3}, Landroid/widget/LinearLayout;->setOrientation(I)V

    .line 41
    const/16 v4, 0x11

    invoke-virtual {v2, v4}, Landroid/widget/LinearLayout;->setGravity(I)V

    .line 42
    const/16 v5, 0x16

    const/4 v6, 0x7

    invoke-virtual {v2, v5, v6, v5, v1}, Landroid/widget/LinearLayout;->setPadding(IIII)V

    .line 44
    new-instance v1, Landroid/widget/TextView;

    invoke-direct {v1, p1}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->titleView:Landroid/widget/TextView;

    .line 45
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->titleView:Landroid/widget/TextView;

    const/4 v5, -0x1

    invoke-virtual {v1, v5}, Landroid/widget/TextView;->setTextColor(I)V

    .line 46
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->titleView:Landroid/widget/TextView;

    const/high16 v6, 0x41d80000    # 27.0f

    invoke-virtual {v1, v0, v6}, Landroid/widget/TextView;->setTextSize(IF)V

    .line 47
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->titleView:Landroid/widget/TextView;

    sget-object v6, Landroid/graphics/Typeface;->DEFAULT:Landroid/graphics/Typeface;

    invoke-virtual {v1, v6, v3}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;I)V

    .line 48
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->titleView:Landroid/widget/TextView;

    invoke-virtual {v1, v4}, Landroid/widget/TextView;->setGravity(I)V

    .line 49
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->titleView:Landroid/widget/TextView;

    invoke-virtual {v1, v0}, Landroid/widget/TextView;->setIncludeFontPadding(Z)V

    .line 50
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->titleView:Landroid/widget/TextView;

    invoke-virtual {v1, v3}, Landroid/widget/TextView;->setSingleLine(Z)V

    .line 51
    iget-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->titleView:Landroid/widget/TextView;

    sget-object v6, Landroid/text/TextUtils$TruncateAt;->END:Landroid/text/TextUtils$TruncateAt;

    invoke-virtual {v1, v6}, Landroid/widget/TextView;->setEllipsize(Landroid/text/TextUtils$TruncateAt;)V

    .line 53
    new-instance v1, Landroid/widget/TextView;

    invoke-direct {v1, p1}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    iput-object v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->subtitleView:Landroid/widget/TextView;

    .line 54
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->subtitleView:Landroid/widget/TextView;

    const/16 v1, 0xeb

    const/16 v6, 0xff

    invoke-static {v1, v6, v6, v6}, Landroid/graphics/Color;->argb(IIII)I

    move-result v1

    invoke-virtual {p1, v1}, Landroid/widget/TextView;->setTextColor(I)V

    .line 55
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->subtitleView:Landroid/widget/TextView;

    const/high16 v1, 0x41900000    # 18.0f

    invoke-virtual {p1, v0, v1}, Landroid/widget/TextView;->setTextSize(IF)V

    .line 56
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->subtitleView:Landroid/widget/TextView;

    invoke-virtual {p1, v4}, Landroid/widget/TextView;->setGravity(I)V

    .line 57
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->subtitleView:Landroid/widget/TextView;

    invoke-virtual {p1, v0}, Landroid/widget/TextView;->setIncludeFontPadding(Z)V

    .line 58
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->subtitleView:Landroid/widget/TextView;

    invoke-virtual {p1, v3}, Landroid/widget/TextView;->setSingleLine(Z)V

    .line 59
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->subtitleView:Landroid/widget/TextView;

    sget-object v0, Landroid/text/TextUtils$TruncateAt;->END:Landroid/text/TextUtils$TruncateAt;

    invoke-virtual {p1, v0}, Landroid/widget/TextView;->setEllipsize(Landroid/text/TextUtils$TruncateAt;)V

    .line 61
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->titleView:Landroid/widget/TextView;

    new-instance v0, Landroid/widget/LinearLayout$LayoutParams;

    const/16 v1, 0x37

    invoke-direct {v0, v5, v1}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    invoke-virtual {v2, p1, v0}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 63
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->subtitleView:Landroid/widget/TextView;

    new-instance v0, Landroid/widget/LinearLayout$LayoutParams;

    const/16 v1, 0x1e

    invoke-direct {v0, v5, v1}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    invoke-virtual {v2, p1, v0}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 65
    new-instance p1, Landroid/widget/FrameLayout$LayoutParams;

    invoke-direct {p1, v5, v5}, Landroid/widget/FrameLayout$LayoutParams;-><init>(II)V

    invoke-virtual {p0, v2, p1}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 67
    return-void
.end method

.method static synthetic access$000(Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;)Z
    .registers 1

    .line 17
    iget-boolean p0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->showing:Z

    return p0
.end method

.method private static backgroundColor(Ljava/lang/String;)I
    .registers 5

    .line 105
    const-string v0, "critical"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    move-result v0

    const/16 v1, 0xff

    const/16 v2, 0xee

    const/4 v3, 0x0

    if-eqz v0, :cond_14

    .line 106
    const/16 p0, 0x15

    invoke-static {v2, v1, v3, p0}, Landroid/graphics/Color;->argb(IIII)I

    move-result p0

    return p0

    .line 108
    :cond_14
    const-string v0, "userPrompt"

    invoke-virtual {v0, p0}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    move-result p0

    if-eqz p0, :cond_23

    .line 109
    const/16 p0, 0x73

    invoke-static {v2, v1, p0, v3}, Landroid/graphics/Color;->argb(IIII)I

    move-result p0

    return p0

    .line 111
    :cond_23
    const/16 p0, 0xe6

    invoke-static {p0, v3, v3, v3}, Landroid/graphics/Color;->argb(IIII)I

    move-result p0

    return p0
.end method

.method private hideBanner()V
    .registers 4

    .line 129
    iget-boolean v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->showing:Z

    if-nez v0, :cond_b

    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->getVisibility()I

    move-result v0

    if-eqz v0, :cond_b

    .line 130
    return-void

    .line 132
    :cond_b
    const/4 v0, 0x0

    iput-boolean v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->showing:Z

    .line 133
    const-string v0, ""

    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->currentKey:Ljava/lang/String;

    .line 134
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->animate()Landroid/view/ViewPropertyAnimator;

    move-result-object v0

    invoke-virtual {v0}, Landroid/view/ViewPropertyAnimator;->cancel()V

    .line 135
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->animate()Landroid/view/ViewPropertyAnimator;

    move-result-object v0

    const/high16 v1, -0x3d380000    # -100.0f

    invoke-virtual {v0, v1}, Landroid/view/ViewPropertyAnimator;->translationY(F)Landroid/view/ViewPropertyAnimator;

    move-result-object v0

    const-wide/16 v1, 0xb4

    invoke-virtual {v0, v1, v2}, Landroid/view/ViewPropertyAnimator;->setDuration(J)Landroid/view/ViewPropertyAnimator;

    move-result-object v0

    new-instance v1, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView$1;

    invoke-direct {v1, p0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView$1;-><init>(Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;)V

    .line 136
    invoke-virtual {v0, v1}, Landroid/view/ViewPropertyAnimator;->setListener(Landroid/animation/Animator$AnimatorListener;)Landroid/view/ViewPropertyAnimator;

    move-result-object v0

    .line 143
    invoke-virtual {v0}, Landroid/view/ViewPropertyAnimator;->start()V

    .line 144
    return-void
.end method

.method private showBanner()V
    .registers 4

    .line 115
    iget-boolean v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->showing:Z

    const/4 v1, 0x1

    const/4 v2, 0x0

    if-eqz v0, :cond_e

    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->getVisibility()I

    move-result v0

    if-nez v0, :cond_e

    const/4 v0, 0x1

    goto :goto_f

    :cond_e
    const/4 v0, 0x0

    .line 116
    :goto_f
    iput-boolean v1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->showing:Z

    .line 117
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->animate()Landroid/view/ViewPropertyAnimator;

    move-result-object v1

    invoke-virtual {v1}, Landroid/view/ViewPropertyAnimator;->cancel()V

    .line 118
    invoke-virtual {p0, v2}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->setVisibility(I)V

    .line 119
    const/high16 v1, 0x3f800000    # 1.0f

    invoke-virtual {p0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->setAlpha(F)V

    .line 120
    const/4 v1, 0x0

    if-eqz v0, :cond_27

    .line 121
    invoke-virtual {p0, v1}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->setTranslationY(F)V

    .line 122
    return-void

    .line 124
    :cond_27
    const/high16 v0, -0x3d380000    # -100.0f

    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->setTranslationY(F)V

    .line 125
    invoke-virtual {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->animate()Landroid/view/ViewPropertyAnimator;

    move-result-object v0

    invoke-virtual {v0, v1}, Landroid/view/ViewPropertyAnimator;->translationY(F)Landroid/view/ViewPropertyAnimator;

    move-result-object v0

    const-wide/16 v1, 0xf0

    invoke-virtual {v0, v1, v2}, Landroid/view/ViewPropertyAnimator;->setDuration(J)Landroid/view/ViewPropertyAnimator;

    move-result-object v0

    const/4 v1, 0x0

    invoke-virtual {v0, v1}, Landroid/view/ViewPropertyAnimator;->setListener(Landroid/animation/Animator$AnimatorListener;)Landroid/view/ViewPropertyAnimator;

    move-result-object v0

    invoke-virtual {v0}, Landroid/view/ViewPropertyAnimator;->start()V

    .line 126
    return-void
.end method


# virtual methods
.method public updatePayload(Ljava/lang/String;)V
    .registers 9

    .line 70
    const-string v0, "none"

    const-string v1, ""

    if-nez p1, :cond_a

    .line 71
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->hideBanner()V

    .line 72
    return-void

    .line 76
    :cond_a
    :try_start_a
    new-instance v2, Lorg/json/JSONObject;

    invoke-direct {v2, p1}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    .line 77
    const-string p1, "alertText1"

    invoke-virtual {v2, p1, v1}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/String;->trim()Ljava/lang/String;

    move-result-object p1

    .line 78
    const-string v3, "alertText2"

    invoke-virtual {v2, v3, v1}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v3

    invoke-virtual {v3}, Ljava/lang/String;->trim()Ljava/lang/String;

    move-result-object v3

    .line 79
    const-string v4, "alertType"

    invoke-virtual {v2, v4, v1}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v4

    .line 80
    const-string v5, "alertStatus"

    const-string v6, "normal"

    invoke-virtual {v2, v5, v6}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v5

    .line 81
    const-string v6, "alertSize"

    invoke-virtual {v2, v6, v0}, Lorg/json/JSONObject;->optString(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v2

    const-string v6, "resumeRequired"

    invoke-virtual {v4, v6}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z

    move-result v6

    if-nez v6, :cond_navdy_hide_resume_required

    const-string v6, "Resume 버튼"

    invoke-virtual {p1, v6}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z

    move-result v6

    if-eqz v6, :cond_navdy_check_empty_alert

    :cond_navdy_hide_resume_required
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->hideBanner()V

    return-void

    :cond_navdy_check_empty_alert
    .line 83
    invoke-virtual {p1}, Ljava/lang/String;->length()I

    move-result v6

    if-nez v6, :cond_43

    invoke-virtual {v3}, Ljava/lang/String;->length()I

    move-result v6

    if-eqz v6, :cond_49

    :cond_43
    invoke-virtual {v0, v2}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_4d

    .line 84
    :cond_49
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->hideBanner()V

    .line 85
    return-void

    .line 88
    :cond_4d
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v0, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    const/16 v2, 0xa

    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(C)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    .line 89
    iget-boolean v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->showing:Z

    if-eqz v2, :cond_81

    iget-object v2, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->currentKey:Ljava/lang/String;

    invoke-virtual {v0, v2}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v2

    if-eqz v2, :cond_81

    .line 90
    return-void

    .line 93
    :cond_81
    iput-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->currentKey:Ljava/lang/String;

    .line 94
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->titleView:Landroid/widget/TextView;

    invoke-virtual {p1}, Ljava/lang/String;->length()I

    move-result v2

    if-lez v2, :cond_8d

    move-object v2, p1

    goto :goto_8e

    :cond_8d
    move-object v2, v3

    :goto_8e
    invoke-virtual {v0, v2}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 95
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->subtitleView:Landroid/widget/TextView;

    invoke-virtual {p1}, Ljava/lang/String;->length()I

    move-result v2

    if-lez v2, :cond_9a

    move-object v1, v3

    :cond_9a
    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 96
    iget-object v0, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->subtitleView:Landroid/widget/TextView;

    invoke-virtual {p1}, Ljava/lang/String;->length()I

    move-result p1

    if-lez p1, :cond_ad

    invoke-virtual {v3}, Ljava/lang/String;->length()I

    move-result p1

    if-lez p1, :cond_ad

    const/4 p1, 0x0

    goto :goto_af

    :cond_ad
    const/16 p1, 0x8

    :goto_af
    invoke-virtual {v0, p1}, Landroid/widget/TextView;->setVisibility(I)V

    .line 97
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->background:Landroid/graphics/drawable/GradientDrawable;

    invoke-static {v5}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->backgroundColor(Ljava/lang/String;)I

    move-result v0

    invoke-virtual {p1, v0}, Landroid/graphics/drawable/GradientDrawable;->setColor(I)V

    .line 98
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->showBanner()V
    :try_end_be
    .catch Ljava/lang/Exception; {:try_start_a .. :try_end_be} :catch_bf

    .line 101
    goto :goto_c3

    .line 99
    :catch_bf
    move-exception p1

    .line 100
    invoke-direct {p0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->hideBanner()V

    .line 102
    :goto_c3
    return-void
.end method
