.class final Lcom/navdy/hud/app/view/TraverseBootView$1;
.super Ljava/lang/Object;
.source "TraverseBootView.java"

# interfaces
.implements Ljava/lang/Runnable;


# instance fields
.field final synthetic this$0:Lcom/navdy/hud/app/view/TraverseBootView;


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/view/TraverseBootView;)V
    .locals 0

    iput-object p1, p0, Lcom/navdy/hud/app/view/TraverseBootView$1;->this$0:Lcom/navdy/hud/app/view/TraverseBootView;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 3

    iget-object v0, p0, Lcom/navdy/hud/app/view/TraverseBootView$1;->this$0:Lcom/navdy/hud/app/view/TraverseBootView;

    const/4 v2, 0x0

    iput-object v2, v0, Lcom/navdy/hud/app/view/TraverseBootView;->mHideRunnable:Ljava/lang/Runnable;

    invoke-virtual {v0}, Lcom/navdy/hud/app/view/TraverseBootView;->clearAnimation()V

    const/16 v1, 0x8

    invoke-virtual {v0, v1}, Lcom/navdy/hud/app/view/TraverseBootView;->setVisibility(I)V

    const/4 v1, 0x0

    invoke-virtual {v0, v1, v1}, Lcom/navdy/hud/app/view/TraverseBootView;->setLayerType(ILandroid/graphics/Paint;)V

    const/4 v2, 0x0

    invoke-virtual {v0, v2}, Lcom/navdy/hud/app/view/TraverseBootView;->getChildAt(I)Landroid/view/View;

    move-result-object v2

    if-eqz v2, :cond_0

    invoke-virtual {v2, v1, v1}, Landroid/view/View;->setLayerType(ILandroid/graphics/Paint;)V

    :cond_0
    const/4 v2, 0x1

    invoke-virtual {v0, v2}, Lcom/navdy/hud/app/view/TraverseBootView;->getChildAt(I)Landroid/view/View;

    move-result-object v2

    if-eqz v2, :cond_1

    invoke-virtual {v2, v1, v1}, Landroid/view/View;->setLayerType(ILandroid/graphics/Paint;)V

    :cond_1
    return-void
.end method
