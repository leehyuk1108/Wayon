.class Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView$1;
.super Landroid/animation/AnimatorListenerAdapter;
.source "OpenpilotAlertBannerView.java"


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->hideBanner()V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;)V
    .locals 0
    .annotation system Ldalvik/annotation/MethodParameters;
        accessFlags = {
            0x8010
        }
        names = {
            null
        }
    .end annotation

    .line 136
    iput-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView$1;->this$0:Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;

    invoke-direct {p0}, Landroid/animation/AnimatorListenerAdapter;-><init>()V

    return-void
.end method


# virtual methods
.method public onAnimationEnd(Landroid/animation/Animator;)V
    .locals 1

    .line 139
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView$1;->this$0:Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;

    invoke-static {p1}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->access$000(Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;)Z

    move-result p1

    if-nez p1, :cond_0

    .line 140
    iget-object p1, p0, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView$1;->this$0:Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;

    const/16 v0, 0x8

    invoke-virtual {p1, v0}, Lcom/navdy/hud/app/openpilot/OpenpilotAlertBannerView;->setVisibility(I)V

    .line 142
    :cond_0
    return-void
.end method
