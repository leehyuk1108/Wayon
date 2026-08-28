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

    .line 100
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Landroid/bluetooth/BluetoothGattCallback;-><init>()V

    return-void
.end method


# virtual methods
.method public onCharacteristicChanged(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V
    .locals 2

    .line 180
    invoke-virtual {p2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getValue()[B

    move-result-object p1

    .line 181
    if-eqz p1, :cond_2

    array-length p2, p1

    if-nez p2, :cond_0

    goto :goto_0

    .line 184
    :cond_0
    new-instance p2, Ljava/lang/StringBuilder;

    invoke-direct {p2}, Ljava/lang/StringBuilder;-><init>()V

    const-string v0, "ambient notify "

    invoke-virtual {p2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p2

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2600([B)Ljava/lang/String;

    move-result-object v0

    invoke-virtual {p2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p2

    invoke-virtual {p2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p2

    const-string v0, "NavdyAmbient"

    invoke-static {v0, p2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 185
    const/4 p2, 0x0

    aget-byte p1, p1, p2

    const/16 p2, 0x2e

    if-ne p1, p2, :cond_1

    .line 186
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 187
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 188
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p2, 0x1

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 189
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2700(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 190
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 191
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2800(Lcom/navdy/hud/app/ambient/AmbientLightController;)I

    move-result v0

    int-to-long v0, v0

    invoke-virtual {p1, p2, v0, v1}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 193
    :cond_1
    return-void

    .line 182
    :cond_2
    :goto_0
    return-void
.end method

.method public onCharacteristicWrite(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V
    .locals 1

    .line 160
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

    .line 161
    if-eqz p2, :cond_0

    .line 162
    invoke-virtual {p2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getWriteType()I

    move-result p1

    const/4 p2, 0x1

    if-ne p1, p2, :cond_0

    .line 163
    return-void

    .line 165
    :cond_0
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 166
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 167
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p2, 0x0

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 168
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 169
    return-void
.end method

.method public onConnectionStateChange(Landroid/bluetooth/BluetoothGatt;II)V
    .locals 4

    .line 103
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGatt;

    move-result-object v0

    const-string v1, "NavdyAmbient"

    if-eq p1, v0, :cond_0

    .line 104
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "ignoring stale ambient gatt callback status="

    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object p2

    const-string v0, " state="

    invoke-virtual {p2, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object p2

    invoke-virtual {p2, p3}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object p2

    invoke-virtual {p2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p2

    invoke-static {v1, p2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 106
    :try_start_0
    invoke-virtual {p1}, Landroid/bluetooth/BluetoothGatt;->close()V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 108
    goto :goto_0

    .line 107
    :catch_0
    move-exception p1

    .line 109
    :goto_0
    return-void

    .line 111
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v2, 0x0

    invoke-static {v0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$102(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 112
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object v3

    invoke-virtual {v0, v3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 113
    const/4 v0, 0x2

    if-ne p3, v0, :cond_1

    .line 114
    const-string p2, "ambient gatt connected"

    invoke-static {v1, p2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 115
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$402(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 116
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p3, 0x1

    invoke-static {p2, p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 117
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 118
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p2

    iget-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p3

    invoke-virtual {p2, p3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 119
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$002(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGatt;

    .line 120
    invoke-virtual {p1}, Landroid/bluetooth/BluetoothGatt;->discoverServices()Z

    goto/16 :goto_2

    .line 121
    :cond_1
    if-nez p3, :cond_3

    .line 122
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

    .line 123
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 124
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 125
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p3

    invoke-virtual {p1, p3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 126
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p3

    invoke-virtual {p1, p3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 127
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p3

    invoke-virtual {p1, p3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 128
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p3

    invoke-virtual {p1, p3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 129
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p3, 0x0

    invoke-static {p1, p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1302(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 130
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1402(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 131
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 132
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 133
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1700(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 134
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/16 p3, 0x85

    if-ne p2, p3, :cond_2

    const-wide/16 p2, 0x5dc

    goto :goto_1

    :cond_2
    const-wide/16 p2, 0x1388

    :goto_1
    invoke-static {p1, p2, p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1800(Lcom/navdy/hud/app/ambient/AmbientLightController;J)V

    .line 136
    :cond_3
    :goto_2
    return-void
.end method

.method public onDescriptorWrite(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattDescriptor;I)V
    .locals 0

    .line 173
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

    .line 174
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p2, 0x1

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 175
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 176
    return-void
.end method

.method public onServicesDiscovered(Landroid/bluetooth/BluetoothGatt;I)V
    .locals 3

    .line 140
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1900(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1302(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 141
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2000(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1402(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 142
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v1, 0x0

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 143
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 144
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

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

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

    .line 145
    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1400(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object v0

    if-eqz v0, :cond_1

    const/4 v1, 0x1

    :cond_1
    invoke-virtual {p2, v1}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object p2

    invoke-virtual {p2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p2

    .line 144
    const-string v0, "NavdyAmbient"

    invoke-static {v0, p2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 146
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p2

    if-eqz p2, :cond_2

    .line 147
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p2

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2100(Landroid/bluetooth/BluetoothGattCharacteristic;)V

    .line 148
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 150
    :cond_2
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2300(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 151
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1400(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p2

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2400(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result p1

    if-eqz p1, :cond_3

    .line 152
    return-void

    .line 154
    :cond_3
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 155
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 156
    return-void
.end method
