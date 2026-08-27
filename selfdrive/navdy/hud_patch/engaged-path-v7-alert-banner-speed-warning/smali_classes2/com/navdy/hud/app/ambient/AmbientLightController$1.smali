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

    .line 105
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-direct {p0}, Landroid/bluetooth/BluetoothGattCallback;-><init>()V

    return-void
.end method


# virtual methods
.method public onCharacteristicChanged(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)V
    .locals 2

    .line 185
    invoke-virtual {p2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getValue()[B

    move-result-object p1

    .line 186
    if-eqz p1, :cond_2

    array-length p2, p1

    if-nez p2, :cond_0

    goto :goto_0

    .line 189
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

    .line 190
    const/4 p2, 0x0

    aget-byte p1, p1, p2

    const/16 p2, 0x2e

    if-ne p1, p2, :cond_1

    .line 191
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 192
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 193
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p2, 0x1

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 194
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2700(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 195
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 196
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

    .line 198
    :cond_1
    return-void

    .line 187
    :cond_2
    :goto_0
    return-void
.end method

.method public onCharacteristicWrite(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;I)V
    .locals 1

    .line 165
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

    .line 166
    if-eqz p2, :cond_0

    .line 167
    invoke-virtual {p2}, Landroid/bluetooth/BluetoothGattCharacteristic;->getWriteType()I

    move-result p1

    const/4 p2, 0x1

    if-ne p1, p2, :cond_0

    .line 168
    return-void

    .line 170
    :cond_0
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 171
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p2

    invoke-virtual {p1, p2}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 172
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p2, 0x0

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 173
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 174
    return-void
.end method

.method public onConnectionStateChange(Landroid/bluetooth/BluetoothGatt;II)V
    .locals 4

    .line 108
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGatt;

    move-result-object v0

    const-string v1, "NavdyAmbient"

    if-eq p1, v0, :cond_0

    .line 109
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

    .line 111
    :try_start_0
    invoke-virtual {p1}, Landroid/bluetooth/BluetoothGatt;->close()V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 113
    goto :goto_0

    .line 112
    :catch_0
    move-exception p1

    .line 114
    :goto_0
    return-void

    .line 116
    :cond_0
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v2, 0x0

    invoke-static {v0, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$102(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 117
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object v0

    iget-object v3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object v3

    invoke-virtual {v0, v3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 118
    const/4 v0, 0x2

    if-ne p3, v0, :cond_1

    .line 119
    const-string p2, "ambient gatt connected"

    invoke-static {v1, p2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 120
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$402(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 121
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p3, 0x1

    invoke-static {p2, p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 122
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 123
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p2

    iget-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$700(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p3

    invoke-virtual {p2, p3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 124
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2, p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$002(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGatt;

    .line 125
    invoke-virtual {p1}, Landroid/bluetooth/BluetoothGatt;->discoverServices()Z

    goto/16 :goto_2

    .line 126
    :cond_1
    if-nez p3, :cond_3

    .line 127
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

    .line 128
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 129
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$802(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 130
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$900(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p3

    invoke-virtual {p1, p3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 131
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1000(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p3

    invoke-virtual {p1, p3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 132
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1100(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p3

    invoke-virtual {p1, p3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 133
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/os/Handler;

    move-result-object p1

    iget-object p3, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1200(Lcom/navdy/hud/app/ambient/AmbientLightController;)Ljava/lang/Runnable;

    move-result-object p3

    invoke-virtual {p1, p3}, Landroid/os/Handler;->removeCallbacks(Ljava/lang/Runnable;)V

    .line 134
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p3, 0x0

    invoke-static {p1, p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1302(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 135
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1402(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 136
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 137
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 138
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1700(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 139
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/16 p3, 0x85

    if-ne p2, p3, :cond_2

    const-wide/16 p2, 0x5dc

    goto :goto_1

    :cond_2
    const-wide/16 p2, 0x1388

    :goto_1
    invoke-static {p1, p2, p3}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1800(Lcom/navdy/hud/app/ambient/AmbientLightController;J)V

    .line 141
    :cond_3
    :goto_2
    return-void
.end method

.method public onDescriptorWrite(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattDescriptor;I)V
    .locals 0

    .line 178
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

    .line 179
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 p2, 0x1

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 180
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 181
    return-void
.end method

.method public onServicesDiscovered(Landroid/bluetooth/BluetoothGatt;I)V
    .locals 3

    .line 145
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1900(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1302(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 146
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2000(Landroid/bluetooth/BluetoothGatt;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object v1

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1402(Lcom/navdy/hud/app/ambient/AmbientLightController;Landroid/bluetooth/BluetoothGattCharacteristic;)Landroid/bluetooth/BluetoothGattCharacteristic;

    .line 147
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    const/4 v1, 0x0

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 148
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {v0, v1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1602(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 149
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

    .line 150
    invoke-static {v0}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1400(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object v0

    if-eqz v0, :cond_1

    const/4 v1, 0x1

    :cond_1
    invoke-virtual {p2, v1}, Ljava/lang/StringBuilder;->append(Z)Ljava/lang/StringBuilder;

    move-result-object p2

    invoke-virtual {p2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object p2

    .line 149
    const-string v0, "NavdyAmbient"

    invoke-static {v0, p2}, Landroid/util/Log;->i(Ljava/lang/String;Ljava/lang/String;)I

    .line 151
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p2

    if-eqz p2, :cond_2

    .line 152
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1300(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p2

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2100(Landroid/bluetooth/BluetoothGattCharacteristic;)V

    .line 153
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2200(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 155
    :cond_2
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2300(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 156
    iget-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1400(Lcom/navdy/hud/app/ambient/AmbientLightController;)Landroid/bluetooth/BluetoothGattCharacteristic;

    move-result-object p2

    invoke-static {p1, p2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2400(Landroid/bluetooth/BluetoothGatt;Landroid/bluetooth/BluetoothGattCharacteristic;)Z

    move-result p1

    if-eqz p1, :cond_3

    .line 157
    return-void

    .line 159
    :cond_3
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1, v2}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$1502(Lcom/navdy/hud/app/ambient/AmbientLightController;Z)Z

    .line 160
    iget-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$1;->this$0:Lcom/navdy/hud/app/ambient/AmbientLightController;

    invoke-static {p1}, Lcom/navdy/hud/app/ambient/AmbientLightController;->access$2500(Lcom/navdy/hud/app/ambient/AmbientLightController;)V

    .line 161
    return-void
.end method
