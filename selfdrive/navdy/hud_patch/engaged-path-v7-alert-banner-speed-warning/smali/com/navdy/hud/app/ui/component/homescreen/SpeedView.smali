.class public Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;
.super Landroid/widget/LinearLayout;
.source "SpeedView.java"


# static fields
.field public static final ANIMATE_UNIT_VIEW:Z


# instance fields
.field private bus:Lcom/squareup/otto/Bus;

.field private excessiveSpeedingWarningColor:I

.field private lastSpeed:I

.field private lastSpeedUnit:Lcom/navdy/hud/app/manager/SpeedManager$SpeedUnit;

.field private logger:Lcom/navdy/service/library/log/Logger;

.field private speedLimit:I

.field private speedManager:Lcom/navdy/hud/app/manager/SpeedManager;

.field speedUnitView:Landroid/widget/TextView;
    .annotation build Lbutterknife/InjectView;
        value = 0x7f0e0198
    .end annotation
.end field

.field speedView:Landroid/widget/TextView;
    .annotation build Lbutterknife/InjectView;
        value = 0x7f0e0199
    .end annotation
.end field

.field private speedingWarningColor:I


# direct methods
.method public constructor <init>(Landroid/content/Context;)V
    .locals 1
    .param p1, "context"    # Landroid/content/Context;

    .prologue
    .line 49
    const/4 v0, 0x0

    invoke-direct {p0, p1, v0}, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;)V

    .line 50
    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;)V
    .locals 1
    .param p1, "context"    # Landroid/content/Context;
    .param p2, "attrs"    # Landroid/util/AttributeSet;

    .prologue
    .line 53
    const/4 v0, 0x0

    invoke-direct {p0, p1, p2, v0}, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V

    .line 54
    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V
    .locals 2
    .param p1, "context"    # Landroid/content/Context;
    .param p2, "attrs"    # Landroid/util/AttributeSet;
    .param p3, "defStyleAttr"    # I

    .prologue
    .line 57
    invoke-direct {p0, p1, p2, p3}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V

    .line 35
    const/4 v0, -0x1

    iput v0, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->lastSpeed:I

    .line 58
    invoke-virtual {p1}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;

    move-result-object v0

    const v1, 0x7f0d000f

    invoke-virtual {v0, v1}, Landroid/content/res/Resources;->getColor(I)I

    move-result v0

    iput v0, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedingWarningColor:I

    .line 59
    invoke-virtual {p1}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;

    move-result-object v0

    const v1, 0x7f0d00a7

    invoke-virtual {v0, v1}, Landroid/content/res/Resources;->getColor(I)I

    move-result v0

    iput v0, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->excessiveSpeedingWarningColor:I

    .line 60
    return-void
.end method

.method private setTrackingSpeed()V
    .locals 9

    .prologue
    const/4 v6, -0x1

    .line 107
    iget-object v4, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedManager:Lcom/navdy/hud/app/manager/SpeedManager;

    invoke-virtual {v4}, Lcom/navdy/hud/app/manager/SpeedManager;->getCurrentSpeed()I

    move-result v0

    .line 108
    .local v0, "speed":I
    if-gez v0, :cond_0

    .line 109
    const/4 v0, 0x0

    .line 111
    :cond_0
    iget-object v4, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedManager:Lcom/navdy/hud/app/manager/SpeedManager;

    invoke-virtual {v4}, Lcom/navdy/hud/app/manager/SpeedManager;->getSpeedUnit()Lcom/navdy/hud/app/manager/SpeedManager$SpeedUnit;

    move-result-object v2

    .line 112
    .local v2, "speedUnit":Lcom/navdy/hud/app/manager/SpeedManager$SpeedUnit;
    iget v4, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->lastSpeed:I

    if-eq v0, v4, :cond_1

    .line 113
    iput v0, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->lastSpeed:I

    .line 114
    iget-object v4, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedView:Landroid/widget/TextView;

    invoke-static {v0}, Ljava/lang/String;->valueOf(I)Ljava/lang/String;

    move-result-object v5

    invoke-virtual {v4, v5}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 116
    :cond_1
    iget-object v4, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->lastSpeedUnit:Lcom/navdy/hud/app/manager/SpeedManager$SpeedUnit;

    if-eq v2, v4, :cond_2

    .line 117
    iput-object v2, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->lastSpeedUnit:Lcom/navdy/hud/app/manager/SpeedManager$SpeedUnit;

    .line 118
    const-string v3, ""

    .line 119
    .local v3, "str":Ljava/lang/String;
    sget-object v4, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView$Anon1;->$SwitchMap$com$navdy$hud$app$manager$SpeedManager$SpeedUnit:[I

    invoke-virtual {v2}, Lcom/navdy/hud/app/manager/SpeedManager$SpeedUnit;->ordinal()I

    move-result v5

    aget v4, v4, v5

    packed-switch v4, :pswitch_data_0

    .line 132
    :goto_0
    iget-object v4, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedUnitView:Landroid/widget/TextView;

    invoke-virtual {v4, v3}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 134
    .end local v3    # "str":Ljava/lang/String;
    :cond_2
    const/4 v1, 0x0

    .line 135
    .local v1, "speedLimitThreshold":I
    sget-object v4, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView$Anon1;->$SwitchMap$com$navdy$hud$app$manager$SpeedManager$SpeedUnit:[I

    invoke-virtual {v2}, Lcom/navdy/hud/app/manager/SpeedManager$SpeedUnit;->ordinal()I

    move-result v5

    aget v4, v4, v5

    packed-switch v4, :pswitch_data_1

    .line 144
    :goto_1
    invoke-static {}, Lcom/navdy/hud/app/maps/widget/TrafficIncidentWidgetPresenter;->getLastCameraSpeedLimit()I

    move-result v8

    if-lez v8, :cond_3

    if-le v0, v8, :cond_3

    iget-object v4, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedView:Landroid/widget/TextView;

    const/high16 v5, -0x10000

    invoke-virtual {v4, v5}, Landroid/widget/TextView;->setTextColor(I)V

    add-int/lit8 v5, v8, 0x2

    if-lt v0, v5, :cond_4

    invoke-virtual {p0}, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->getContext()Landroid/content/Context;

    move-result-object v7

    const/4 v5, 0x1

    invoke-static {v7, v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onOverspeedChanged(Landroid/content/Context;Z)V

    goto :goto_2

    :cond_3
    invoke-virtual {p0}, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->getContext()Landroid/content/Context;

    move-result-object v7

    const/4 v5, 0x0

    invoke-static {v7, v5}, Lcom/navdy/hud/app/ambient/AmbientLightController;->onOverspeedChanged(Landroid/content/Context;Z)V

    iget v4, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedLimit:I

    if-lez v4, :cond_7

    .line 145
    iget v4, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedLimit:I

    add-int/2addr v4, v1

    if-lt v0, v4, :cond_5

    .line 147
    iget-object v4, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedView:Landroid/widget/TextView;

    const/high16 v5, -0x10000

    invoke-virtual {v4, v5}, Landroid/widget/TextView;->setTextColor(I)V

    .line 159
    :cond_4
    :goto_2
    return-void

    .line 121
    .end local v1    # "speedLimitThreshold":I
    .restart local v3    # "str":Ljava/lang/String;
    :pswitch_0
    sget-object v3, Lcom/navdy/hud/app/ui/component/homescreen/HomeScreenConstants;->SPEED_MPH:Ljava/lang/String;

    .line 122
    goto :goto_0

    .line 125
    :pswitch_1
    sget-object v3, Lcom/navdy/hud/app/ui/component/homescreen/HomeScreenConstants;->SPEED_KM:Ljava/lang/String;

    .line 126
    goto :goto_0

    .line 129
    :pswitch_2
    sget-object v3, Lcom/navdy/hud/app/ui/component/homescreen/HomeScreenConstants;->SPEED_METERS:Ljava/lang/String;

    goto :goto_0

    .line 137
    .end local v3    # "str":Ljava/lang/String;
    .restart local v1    # "speedLimitThreshold":I
    :pswitch_3
    const/16 v1, 0x8

    .line 138
    goto :goto_1

    .line 141
    :pswitch_4
    const/16 v1, 0xd

    goto :goto_1

    .line 148
    :cond_5
    iget v4, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedLimit:I

    if-lt v0, v4, :cond_6

    .line 150
    iget-object v4, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedView:Landroid/widget/TextView;

    const/high16 v5, -0x10000

    invoke-virtual {v4, v5}, Landroid/widget/TextView;->setTextColor(I)V

    goto :goto_2

    .line 153
    :cond_6
    iget-object v4, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedView:Landroid/widget/TextView;

    invoke-virtual {v4, v6}, Landroid/widget/TextView;->setTextColor(I)V

    goto :goto_2

    .line 157
    :cond_7
    iget-object v4, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedView:Landroid/widget/TextView;

    invoke-virtual {v4, v6}, Landroid/widget/TextView;->setTextColor(I)V

    goto :goto_2

    .line 119
    nop

    :pswitch_data_0
    .packed-switch 0x1
        :pswitch_0
        :pswitch_1
        :pswitch_2
    .end packed-switch

    .line 135
    :pswitch_data_1
    .packed-switch 0x1
        :pswitch_3
        :pswitch_4
    .end packed-switch
.end method


# virtual methods
.method public GPSSpeedChangeEvent(Lcom/navdy/hud/app/maps/MapEvents$GPSSpeedEvent;)V
    .locals 0
    .param p1, "event"    # Lcom/navdy/hud/app/maps/MapEvents$GPSSpeedEvent;
    .annotation runtime Lcom/squareup/otto/Subscribe;
    .end annotation

    .prologue
    .line 98
    invoke-direct {p0}, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->setTrackingSpeed()V

    .line 99
    return-void
.end method

.method public ObdPidChangeEvent(Lcom/navdy/hud/app/obd/ObdManager$ObdPidChangeEvent;)V
    .locals 1
    .param p1, "event"    # Lcom/navdy/hud/app/obd/ObdManager$ObdPidChangeEvent;
    .annotation runtime Lcom/squareup/otto/Subscribe;
    .end annotation

    .prologue
    .line 84
    iget-object v0, p1, Lcom/navdy/hud/app/obd/ObdManager$ObdPidChangeEvent;->pid:Lcom/navdy/obd/Pid;

    invoke-virtual {v0}, Lcom/navdy/obd/Pid;->getId()I

    move-result v0

    packed-switch v0, :pswitch_data_0

    .line 89
    :goto_0
    return-void

    .line 86
    :pswitch_0
    invoke-direct {p0}, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->setTrackingSpeed()V

    goto :goto_0

    .line 84
    :pswitch_data_0
    .packed-switch 0xd
        :pswitch_0
    .end packed-switch
.end method

.method public ObdStateChangeEvent(Lcom/navdy/hud/app/obd/ObdManager$ObdConnectionStatusEvent;)V
    .locals 1
    .param p1, "event"    # Lcom/navdy/hud/app/obd/ObdManager$ObdConnectionStatusEvent;
    .annotation runtime Lcom/squareup/otto/Subscribe;
    .end annotation

    .prologue
    .line 77
    const/4 v0, -0x1

    iput v0, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->lastSpeed:I

    .line 78
    const/4 v0, 0x0

    iput-object v0, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->lastSpeedUnit:Lcom/navdy/hud/app/manager/SpeedManager$SpeedUnit;

    .line 79
    invoke-direct {p0}, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->setTrackingSpeed()V

    .line 80
    return-void
.end method

.method public clearState()V
    .locals 1

    .prologue
    .line 167
    const/4 v0, -0x1

    iput v0, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->lastSpeed:I

    .line 168
    const/4 v0, 0x0

    iput-object v0, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->lastSpeedUnit:Lcom/navdy/hud/app/manager/SpeedManager$SpeedUnit;

    .line 169
    invoke-direct {p0}, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->setTrackingSpeed()V

    .line 170
    return-void
.end method

.method public getTopAnimator(Landroid/animation/AnimatorSet$Builder;Z)V
    .locals 0
    .param p1, "builder"    # Landroid/animation/AnimatorSet$Builder;
    .param p2, "out"    # Z

    .prologue
    .line 174
    return-void
.end method

.method protected onFinishInflate()V
    .locals 1

    .prologue
    .line 64
    sget-object v0, Lcom/navdy/hud/app/ui/component/homescreen/HomeScreenView;->sLogger:Lcom/navdy/service/library/log/Logger;

    iput-object v0, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->logger:Lcom/navdy/service/library/log/Logger;

    .line 65
    invoke-super {p0}, Landroid/widget/LinearLayout;->onFinishInflate()V

    .line 66
    invoke-static {p0}, Lbutterknife/ButterKnife;->inject(Landroid/view/View;)V

    .line 67
    invoke-virtual {p0}, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->isInEditMode()Z

    move-result v0

    if-eqz v0, :cond_0

    .line 73
    :goto_0
    return-void

    .line 70
    :cond_0
    invoke-static {}, Lcom/navdy/hud/app/manager/SpeedManager;->getInstance()Lcom/navdy/hud/app/manager/SpeedManager;

    move-result-object v0

    iput-object v0, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedManager:Lcom/navdy/hud/app/manager/SpeedManager;

    .line 71
    invoke-static {}, Lcom/navdy/hud/app/manager/RemoteDeviceManager;->getInstance()Lcom/navdy/hud/app/manager/RemoteDeviceManager;

    move-result-object v0

    invoke-virtual {v0}, Lcom/navdy/hud/app/manager/RemoteDeviceManager;->getBus()Lcom/squareup/otto/Bus;

    move-result-object v0

    iput-object v0, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->bus:Lcom/squareup/otto/Bus;

    .line 72
    iget-object v0, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->bus:Lcom/squareup/otto/Bus;

    invoke-virtual {v0, p0}, Lcom/squareup/otto/Bus;->register(Ljava/lang/Object;)V

    goto :goto_0
.end method

.method public onSpeedDataExpired(Lcom/navdy/hud/app/manager/SpeedManager$SpeedDataExpired;)V
    .locals 0
    .param p1, "speedDataExpired"    # Lcom/navdy/hud/app/manager/SpeedManager$SpeedDataExpired;
    .annotation runtime Lcom/squareup/otto/Subscribe;
    .end annotation

    .prologue
    .line 103
    invoke-direct {p0}, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->setTrackingSpeed()V

    .line 104
    return-void
.end method

.method public onSpeedUnitChanged(Lcom/navdy/hud/app/manager/SpeedManager$SpeedUnitChanged;)V
    .locals 0
    .param p1, "event"    # Lcom/navdy/hud/app/manager/SpeedManager$SpeedUnitChanged;
    .annotation runtime Lcom/squareup/otto/Subscribe;
    .end annotation

    .prologue
    .line 93
    invoke-direct {p0}, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->setTrackingSpeed()V

    .line 94
    return-void
.end method

.method public resetTopViewsAnimator()V
    .locals 2

    .prologue
    .line 195
    iget-object v0, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedUnitView:Landroid/widget/TextView;

    const/high16 v1, 0x3f800000    # 1.0f

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setAlpha(F)V

    .line 196
    iget-object v0, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedUnitView:Landroid/widget/TextView;

    const/4 v1, 0x0

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setTranslationX(F)V

    .line 197
    iget-object v0, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedView:Landroid/widget/TextView;

    const/4 v1, 0x0

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setVisibility(I)V

    .line 198
    return-void
.end method

.method public setSpeedLimit(I)V
    .locals 0
    .param p1, "speedLimit"    # I

    .prologue
    .line 162
    iput p1, p0, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->speedLimit:I

    .line 163
    invoke-direct {p0}, Lcom/navdy/hud/app/ui/component/homescreen/SpeedView;->setTrackingSpeed()V

    .line 164
    return-void
.end method
