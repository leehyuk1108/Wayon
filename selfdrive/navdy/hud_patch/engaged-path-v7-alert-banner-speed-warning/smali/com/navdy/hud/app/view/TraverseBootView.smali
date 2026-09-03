.class public Lcom/navdy/hud/app/view/TraverseBootView;
.super Landroid/widget/FrameLayout;
.source "TraverseBootView.java"


# static fields
.field private static sInstance:Lcom/navdy/hud/app/view/TraverseBootView;

# instance fields
.field mHideRunnable:Ljava/lang/Runnable;


# direct methods
.method public constructor <init>(Landroid/content/Context;)V
    .locals 0
    .param p1, "context"    # Landroid/content/Context;

    invoke-direct {p0, p1}, Landroid/widget/FrameLayout;-><init>(Landroid/content/Context;)V

    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;)V
    .locals 0
    .param p1, "context"    # Landroid/content/Context;
    .param p2, "attrs"    # Landroid/util/AttributeSet;

    invoke-direct {p0, p1, p2}, Landroid/widget/FrameLayout;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;)V

    return-void
.end method

.method public constructor <init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V
    .locals 0
    .param p1, "context"    # Landroid/content/Context;
    .param p2, "attrs"    # Landroid/util/AttributeSet;
    .param p3, "defStyleAttr"    # I

    invoke-direct {p0, p1, p2, p3}, Landroid/widget/FrameLayout;-><init>(Landroid/content/Context;Landroid/util/AttributeSet;I)V

    return-void
.end method


# virtual methods
.method protected onAttachedToWindow()V
    .locals 7

    invoke-super {p0}, Landroid/widget/FrameLayout;->onAttachedToWindow()V

    sput-object p0, Lcom/navdy/hud/app/view/TraverseBootView;->sInstance:Lcom/navdy/hud/app/view/TraverseBootView;

    const/4 v0, 0x0

    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/view/TraverseBootView;->getChildAt(I)Landroid/view/View;

    move-result-object v1

    const/4 v0, 0x1

    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/view/TraverseBootView;->getChildAt(I)Landroid/view/View;

    move-result-object v2

    const/4 v6, 0x2

    const/4 v0, 0x0

    invoke-virtual {p0, v6, v0}, Lcom/navdy/hud/app/view/TraverseBootView;->setLayerType(ILandroid/graphics/Paint;)V

    invoke-virtual {v1, v6, v0}, Landroid/view/View;->setLayerType(ILandroid/graphics/Paint;)V

    invoke-virtual {v2, v6, v0}, Landroid/view/View;->setLayerType(ILandroid/graphics/Paint;)V

    invoke-virtual {p0}, Lcom/navdy/hud/app/view/TraverseBootView;->getContext()Landroid/content/Context;

    move-result-object v3

    invoke-virtual {p0}, Lcom/navdy/hud/app/view/TraverseBootView;->getResources()Landroid/content/res/Resources;

    move-result-object v4

    invoke-virtual {v3}, Landroid/content/Context;->getPackageName()Ljava/lang/String;

    move-result-object v5

    const-string/jumbo v0, "traverse_boot_logo"

    const-string v6, "anim"

    invoke-virtual {v4, v0, v6, v5}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I

    move-result v0

    if-eqz v0, :cond_0

    invoke-static {v3, v0}, Landroid/view/animation/AnimationUtils;->loadAnimation(Landroid/content/Context;I)Landroid/view/animation/Animation;

    move-result-object v0

    invoke-virtual {v1, v0}, Landroid/view/View;->startAnimation(Landroid/view/animation/Animation;)V

    :cond_0
    const-string/jumbo v0, "traverse_boot_wordmark"

    const-string v6, "anim"

    invoke-virtual {v4, v0, v6, v5}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I

    move-result v0

    if-eqz v0, :cond_1

    invoke-static {v3, v0}, Landroid/view/animation/AnimationUtils;->loadAnimation(Landroid/content/Context;I)Landroid/view/animation/Animation;

    move-result-object v0

    invoke-virtual {v2, v0}, Landroid/view/View;->startAnimation(Landroid/view/animation/Animation;)V

    :cond_1
    const-string/jumbo v0, "traverse_boot_overlay"

    const-string v6, "anim"

    invoke-virtual {v4, v0, v6, v5}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I

    move-result v0

    if-eqz v0, :cond_2

    invoke-static {v3, v0}, Landroid/view/animation/AnimationUtils;->loadAnimation(Landroid/content/Context;I)Landroid/view/animation/Animation;

    move-result-object v0

    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/view/TraverseBootView;->startAnimation(Landroid/view/animation/Animation;)V

    :cond_2
    new-instance v0, Lcom/navdy/hud/app/view/TraverseBootView$1;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/view/TraverseBootView$1;-><init>(Lcom/navdy/hud/app/view/TraverseBootView;)V

    iput-object v0, p0, Lcom/navdy/hud/app/view/TraverseBootView;->mHideRunnable:Ljava/lang/Runnable;

    const-wide/16 v5, 0x2c24

    invoke-virtual {p0, v0, v5, v6}, Lcom/navdy/hud/app/view/TraverseBootView;->postDelayed(Ljava/lang/Runnable;J)Z

    return-void
.end method

.method public static replayIfAttached()V
    .locals 4

    sget-object v0, Lcom/navdy/hud/app/view/TraverseBootView;->sInstance:Lcom/navdy/hud/app/view/TraverseBootView;

    if-eqz v0, :cond_0

    new-instance v1, Lcom/navdy/hud/app/view/TraverseBootView$2;

    invoke-direct {v1, v0}, Lcom/navdy/hud/app/view/TraverseBootView$2;-><init>(Lcom/navdy/hud/app/view/TraverseBootView;)V

    const-wide/16 v2, 0x2bc

    invoke-virtual {v0, v1, v2, v3}, Lcom/navdy/hud/app/view/TraverseBootView;->postDelayed(Ljava/lang/Runnable;J)Z

    :cond_0
    return-void
.end method

.method public replayBootAnimation()V
    .locals 7

    iget-object v0, p0, Lcom/navdy/hud/app/view/TraverseBootView;->mHideRunnable:Ljava/lang/Runnable;

    if-eqz v0, :cond_hide_cancelled

    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/view/TraverseBootView;->removeCallbacks(Ljava/lang/Runnable;)Z

    :cond_hide_cancelled
    const/4 v0, 0x0

    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/view/TraverseBootView;->setVisibility(I)V

    invoke-virtual {p0}, Lcom/navdy/hud/app/view/TraverseBootView;->clearAnimation()V

    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/view/TraverseBootView;->getChildAt(I)Landroid/view/View;

    move-result-object v1

    const/4 v0, 0x1

    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/view/TraverseBootView;->getChildAt(I)Landroid/view/View;

    move-result-object v2

    invoke-virtual {v1}, Landroid/view/View;->clearAnimation()V

    invoke-virtual {v2}, Landroid/view/View;->clearAnimation()V

    const/4 v6, 0x2

    const/4 v0, 0x0

    invoke-virtual {p0, v6, v0}, Lcom/navdy/hud/app/view/TraverseBootView;->setLayerType(ILandroid/graphics/Paint;)V

    invoke-virtual {v1, v6, v0}, Landroid/view/View;->setLayerType(ILandroid/graphics/Paint;)V

    invoke-virtual {v2, v6, v0}, Landroid/view/View;->setLayerType(ILandroid/graphics/Paint;)V

    invoke-virtual {p0}, Lcom/navdy/hud/app/view/TraverseBootView;->getContext()Landroid/content/Context;

    move-result-object v3

    invoke-virtual {p0}, Lcom/navdy/hud/app/view/TraverseBootView;->getResources()Landroid/content/res/Resources;

    move-result-object v4

    invoke-virtual {v3}, Landroid/content/Context;->getPackageName()Ljava/lang/String;

    move-result-object v5

    const-string/jumbo v0, "traverse_boot_logo"

    const-string v6, "anim"

    invoke-virtual {v4, v0, v6, v5}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I

    move-result v0

    if-eqz v0, :cond_0

    invoke-static {v3, v0}, Landroid/view/animation/AnimationUtils;->loadAnimation(Landroid/content/Context;I)Landroid/view/animation/Animation;

    move-result-object v0

    invoke-virtual {v1, v0}, Landroid/view/View;->startAnimation(Landroid/view/animation/Animation;)V

    :cond_0
    const-string/jumbo v0, "traverse_boot_wordmark"

    const-string v6, "anim"

    invoke-virtual {v4, v0, v6, v5}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I

    move-result v0

    if-eqz v0, :cond_1

    invoke-static {v3, v0}, Landroid/view/animation/AnimationUtils;->loadAnimation(Landroid/content/Context;I)Landroid/view/animation/Animation;

    move-result-object v0

    invoke-virtual {v2, v0}, Landroid/view/View;->startAnimation(Landroid/view/animation/Animation;)V

    :cond_1
    const-string/jumbo v0, "traverse_boot_overlay"

    const-string v6, "anim"

    invoke-virtual {v4, v0, v6, v5}, Landroid/content/res/Resources;->getIdentifier(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)I

    move-result v0

    if-eqz v0, :cond_2

    invoke-static {v3, v0}, Landroid/view/animation/AnimationUtils;->loadAnimation(Landroid/content/Context;I)Landroid/view/animation/Animation;

    move-result-object v0

    invoke-virtual {p0, v0}, Lcom/navdy/hud/app/view/TraverseBootView;->startAnimation(Landroid/view/animation/Animation;)V

    :cond_2
    new-instance v0, Lcom/navdy/hud/app/view/TraverseBootView$1;

    invoke-direct {v0, p0}, Lcom/navdy/hud/app/view/TraverseBootView$1;-><init>(Lcom/navdy/hud/app/view/TraverseBootView;)V

    iput-object v0, p0, Lcom/navdy/hud/app/view/TraverseBootView;->mHideRunnable:Ljava/lang/Runnable;

    const-wide/16 v5, 0x2c24

    invoke-virtual {p0, v0, v5, v6}, Lcom/navdy/hud/app/view/TraverseBootView;->postDelayed(Ljava/lang/Runnable;J)Z

    return-void
.end method
