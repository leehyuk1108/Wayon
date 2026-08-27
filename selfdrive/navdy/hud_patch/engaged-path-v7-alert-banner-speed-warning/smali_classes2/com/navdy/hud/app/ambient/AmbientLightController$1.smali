.class Lcom/navdy/hud/app/ambient/AmbientLightController$1;
.super Landroid/bluetooth/BluetoothGattCallback;
.source "AmbientLightController.java"


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

    .line 83
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Landroid/bluetooth/BluetoothGattCallback;-><init>()V

    return-void
.end method


# virtual methods
.method public onCharacteristicChanged(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V
    .locals 2

    .line 152
    invoke-virtual {p2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getValue()[B

    move-result-object p1

    .line 153
    if-eqz p1, :cond_2

    array-length p2, p1

    if-nez p2, :cond_0

    goto :goto_0

    .line 156
    :cond_0
    new-instance p2, Ljava/lang/StringBuilder;

    invoke-direct {p2}, Ljava/lang/StringBuilder;-><init>()V

    const-string v0, "ambient notify "

    invoke-virtual {p2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p2

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2300([B)Ljava/lang/String;

    move-result-object v0

    invoke-virtual {p2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p2

    invoke-virtual {p2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p2

    const-string v0, "NavdyAmbient"

    invoke-static {v0, p2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 157
    const/4 p2, 0x0

    aget-byte p1, p1, p2

    const/16 v0, 0x2e

    if-ne p1, v0, :cond_1

    .line 158
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object v0

    invoke-virtual {p1, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 159
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object v0

    invoke-virtual {p1, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 160
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 161
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2400(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 162
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 163
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    const-wide/16 v0, 0x78

    invoke-virtual {p1, p2, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 165
    :cond_1
    return-void

    .line 154
    :cond_2
    :goto_0
    return-void
.end method

.method public onCharacteristicWrite(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V
    .locals 1

    .line 132
    new-instance p1, Ljava/lang/StringBuilder;

    invoke-direct {p1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v0, "ambient write status="

    invoke-virtual {p1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, p3}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    const-string p3, "NavdyAmbient"

    invoke-static {p3, p1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 133
    if-eqz p2, :cond_0

    .line 134
    invoke-virtual {p2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getWriteType()I

    move-result p1

    const/4 p2, 0x1

    if-ne p1, p2, :cond_0

    .line 135
    return-void

    .line 137
    :cond_0
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 138
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 139
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p2, 0x0

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 140
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 141
    return-void
.end method

.method public onConnectionStateChange(Landroid/bluetooth/BluetoothGatt;II)V
    .locals 3

    .line 86
    const/4 v0, 0x2

    const-string v1, "NavdyAmbient"

    const/4 v2, 0x0

    if-ne p3, v0, :cond_0

    .line 87
    const-string p2, "ambient gatt connected"

    invoke-static {v1, p2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 88
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p3, 0x1

    invoke-static {p2, p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$002(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 89
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$102(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 90
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p2

    iget-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p3

    invoke-virtual {p2, p3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 91
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$402(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGatt;

    .line 92
    invoke-virtual {p1}, Landroid/bluetooth/BluetoothGatt;->discoverServices()Z

    goto/16 :goto_0

    .line 93
    :cond_0
    if-nez p3, :cond_1

    .line 94
    new-instance p1, Ljava/lang/StringBuilder;

    invoke-direct {p1}, Ljava/lang/StringBuilder;-><init>()V

    const-string p3, "ambient gatt disconnected status="

    invoke-virtual {p1, p3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, p2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-static {v1, p1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 95
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$002(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 96
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 97
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 98
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 99
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 100
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 101
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p2, 0x0

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1002(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 102
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1102(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 103
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 104
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1302(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 105
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1400(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 106
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 108
    :cond_1
    :goto_0
    return-void
.end method

.method public onDescriptorWrite(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattDescriptor;I)V
    .locals 0

    .line 145
    new-instance p1, Ljava/lang/StringBuilder;

    invoke-direct {p1}, Ljava/lang/StringBuilder;-><init>()V

    const-string p2, "ambient notify descriptor status="

    invoke-virtual {p1, p2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1, p3}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object p1

    invoke-virtual {p1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p1

    const-string p2, "NavdyAmbient"

    invoke-static {p2, p1}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 146
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p2, 0x1

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 147
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 148
    return-void
.end method

.method public onServicesDiscovered(Landroid/bluetooth/BluetoothGatt;I)V
    .locals 3

    .line 112
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1600(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1002(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 113
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1700(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1102(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 114
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v1, 0x0

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 115
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1302(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 116
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "ambient services status="

    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object p2

    const-string v0, " write="

    invoke-virtual {p2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p2

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object v0

    const/4 v2, 0x1

    if-eqz v0, :cond_0

    const/4 v0, 0x1

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    :goto_0
    invoke-virtual {p2, v0}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object p2

    const-string v0, " notify="

    invoke-virtual {p2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p2

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    .line 117
    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object v0

    if-eqz v0, :cond_1

    const/4 v1, 0x1

    :cond_1
    invoke-virtual {p2, v1}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object p2

    invoke-virtual {p2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p2

    .line 116
    const-string v0, "NavdyAmbient"

    invoke-static {v0, p2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 118
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p2

    if-eqz p2, :cond_2

    .line 119
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p2

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1800(Landroid/bluetooth/BluetoothGattCharacteristic;)V

    .line 120
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1900(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 122
    :cond_2
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2000(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 123
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p2

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2100(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result p1

    if-eqz p1, :cond_3

    .line 124
    return-void

    .line 126
    :cond_3
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 127
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 128
    return-void
.end method
