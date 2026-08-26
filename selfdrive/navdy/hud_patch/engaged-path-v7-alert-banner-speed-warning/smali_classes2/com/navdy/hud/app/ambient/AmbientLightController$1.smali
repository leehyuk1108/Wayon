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

    .line 77
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Landroid/bluetooth/BluetoothGattCallback;-><init>()V

    return-void
.end method


# virtual methods
.method public onCharacteristicChanged(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V
    .locals 2

    .line 146
    invoke-virtual {p2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getValue()[B

    move-result-object p1

    .line 147
    if-eqz p1, :cond_2

    array-length p2, p1

    if-nez p2, :cond_0

    goto :goto_0

    .line 150
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

    .line 151
    const/4 p2, 0x0

    aget-byte p1, p1, p2

    const/16 v0, 0x2e

    if-ne p1, v0, :cond_1

    .line 152
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object v0

    invoke-virtual {p1, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 153
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object v0

    invoke-virtual {p1, v0}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 154
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 155
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2400(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 156
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 157
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    const-wide/16 v0, 0x78

    invoke-virtual {p1, p2, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 159
    :cond_1
    return-void

    .line 148
    :cond_2
    :goto_0
    return-void
.end method

.method public onCharacteristicWrite(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V
    .locals 1

    .line 126
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

    .line 127
    if-eqz p2, :cond_0

    .line 128
    invoke-virtual {p2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getWriteType()I

    move-result p1

    const/4 p2, 0x1

    if-ne p1, p2, :cond_0

    .line 129
    return-void

    .line 131
    :cond_0
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 132
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 133
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p2, 0x0

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 134
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 135
    return-void
.end method

.method public onConnectionStateChange(Landroid/bluetooth/BluetoothGatt;II)V
    .locals 3

    .line 80
    const/4 v0, 0x2

    const-string v1, "NavdyAmbient"

    const/4 v2, 0x0

    if-ne p3, v0, :cond_0

    .line 81
    const-string p2, "ambient gatt connected"

    invoke-static {v1, p2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 82
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p3, 0x1

    invoke-static {p2, p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$002(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 83
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$102(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 84
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p2

    iget-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p3

    invoke-virtual {p2, p3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 85
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$402(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGatt;

    .line 86
    invoke-virtual {p1}, Landroid/bluetooth/BluetoothGatt;->discoverServices()Z

    goto/16 :goto_0

    .line 87
    :cond_0
    if-nez p3, :cond_1

    .line 88
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

    .line 89
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$002(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 90
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 91
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$600(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 92
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 93
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$800(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 94
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 95
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p2, 0x0

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1002(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 96
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1102(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 97
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 98
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1302(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 99
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1400(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 100
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 102
    :cond_1
    :goto_0
    return-void
.end method

.method public onDescriptorWrite(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattDescriptor;I)V
    .locals 0

    .line 139
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

    .line 140
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p2, 0x1

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 141
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 142
    return-void
.end method

.method public onServicesDiscovered(Landroid/bluetooth/BluetoothGatt;I)V
    .locals 3

    .line 106
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1600(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1002(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 107
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1700(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1102(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 108
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v1, 0x0

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 109
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1302(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 110
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

    .line 111
    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object v0

    if-eqz v0, :cond_1

    const/4 v1, 0x1

    :cond_1
    invoke-virtual {p2, v1}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object p2

    invoke-virtual {p2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p2

    .line 110
    const-string v0, "NavdyAmbient"

    invoke-static {v0, p2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 112
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p2

    if-eqz p2, :cond_2

    .line 113
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p2

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1800(Landroid/bluetooth/BluetoothGattCharacteristic;)V

    .line 114
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1900(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 116
    :cond_2
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2000(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 117
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p2

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2100(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result p1

    if-eqz p1, :cond_3

    .line 118
    return-void

    .line 120
    :cond_3
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1202(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 121
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 122
    return-void
.end method
