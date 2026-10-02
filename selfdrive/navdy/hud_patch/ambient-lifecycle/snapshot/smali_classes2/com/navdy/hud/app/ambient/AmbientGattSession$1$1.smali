.class Lcom/navdy/hud/app/ambient/AmbientGattSession$1$1;
.super Ljava/lang/Object;
.source "AmbientGattSession.java"

# interfaces
.implements Ljava/lang/Runnable;


# annotations
.annotation system Ldalvik/annotation/EnclosingMethod;
    value = Lcom/navdy/hud/app/ambient/AmbientGattSession$1;->run()V
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$1:Lcom/navdy/hud/app/ambient/AmbientGattSession$1;


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/ambient/AmbientGattSession$1;)V
    .locals 0
    .annotation system Ldalvik/annotation/MethodParameters;
        accessFlags = {
            0x8010
        }
        names = {
            null
        }
    .end annotation

    .line 99
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$1$1;->this$1:Lcom/navdy/hud/app/ambient/AmbientGattSession$1;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public run()V
    .locals 4

    .line 100
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$1$1;->this$1:Lcom/navdy/hud/app/ambient/AmbientGattSession$1;

    iget-object v0, v0, Lcom/navdy/hud/app/ambient/AmbientGattSession$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientGattSession;

    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientGattSession$1$1;->this$1:Lcom/navdy/hud/app/ambient/AmbientGattSession$1;

    iget-object v1, v1, Lcom/navdy/hud/app/ambient/AmbientGattSession$1;->val$gatt:Landroid/bluetooth/BluetoothGatt;

    const/16 v2, 0x85

    const-string v3, "service/notification setup timeout"

    invoke-static {v0, v1, v2, v3}, Lcom/navdy/hud/app/ambient/AmbientGattSession;->access$200(Lcom/navdy/hud/app/ambient/AmbientGattSession;Landroid/bluetooth/BluetoothGatt;ILjava/lang/String;)V

    .line 101
    return-void
.end method
