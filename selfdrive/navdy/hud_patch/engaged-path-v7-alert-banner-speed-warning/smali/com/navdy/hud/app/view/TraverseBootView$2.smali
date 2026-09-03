.class final Lcom/navdy/hud/app/view/TraverseBootView$2;
.super Ljava/lang/Object;
.source "TraverseBootView.java"

# interfaces
.implements Ljava/lang/Runnable;

# instance fields
.field final synthetic this$0:Lcom/navdy/hud/app/view/TraverseBootView;

# direct methods
.method constructor <init>(Lcom/navdy/hud/app/view/TraverseBootView;)V
    .locals 0

    iput-object p1, p0, Lcom/navdy/hud/app/view/TraverseBootView$2;->this$0:Lcom/navdy/hud/app/view/TraverseBootView;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

# virtual methods
.method public run()V
    .locals 1

    iget-object v0, p0, Lcom/navdy/hud/app/view/TraverseBootView$2;->this$0:Lcom/navdy/hud/app/view/TraverseBootView;

    invoke-virtual {v0}, Lcom/navdy/hud/app/view/TraverseBootView;->replayBootAnimation()V

    return-void
.end method
