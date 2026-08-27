.class Lcom/navdy/hud/app/ambient/AmbientLightController$2;
.super Ljava/lang/Object;
.source "AmbientLightController.java"

# interfaces
.implements Landroid/bluetooth/BluetoothAdapter$LeScanCallback;


# annotations
.annotation system Ldalvik/annotation/EnclosingClass;
    value = Lcom/navdy/hud/app/ambient/AmbientLightController;
.end annotation

.annotation system Ldalvik/annotation/InnerClass;
    accessFlags = 0x0
    name = null
.end annotation


# instance fields
.field final synthetic this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;


# direct methods
.method constructor <init>(Lcom/navdy/hud/app/ambient/AmbientLightController;)V
    .locals 0

    .line 168
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$2;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method


# virtual methods
.method public onLeScan(Landroid/bluetooth/BluetoothDevice;I[B)V
    .locals 0

    .line 171
    if-nez p1, :cond_0

    .line 172
    return-void

    .line 174
    :cond_0
    invoke-static {p1, p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2500(Landroid/bluetooth/BluetoothDevice;[B)Z

    move-result p3

    if-nez p3, :cond_1

    .line 175
    iget-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$2;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p3, p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2600(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothDevice;I)V

    .line 176
    return-void

    .line 178
    :cond_1
    new-instance p2, Ljava/lang/StringBuilder;

    invoke-direct {p2}, Ljava/lang/StringBuilder;-><init>()V

    const-string p3, "ambient candidate "

    invoke-virtual {p2, p3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p2

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2700(Landroid/bluetooth/BluetoothDevice;)Ljava/lang/String;

    move-result-object p3

    invoke-virtual {p2, p3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p2

    const-string p3, " "

    invoke-virtual {p2, p3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p2

    invoke-virtual {p1}, Landroid/bluetooth/BluetoothDevice;->getAddress()Ljava/lang/String;

    move-result-object p3

    invoke-virtual {p2, p3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p2

    invoke-virtual {p2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p2

    const-string p3, "NavdyAmbient"

    invoke-static {p3, p2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 179
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$2;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2800(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 180
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$2;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2900(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothDevice;)V

    .line 181
    return-void
.end method
