"""Scoped power lifecycle and BLE recovery patch over the exact installed v155r2."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('off_patch', HERE.parent / 'v155-ambient-off-priority/apply.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
once, edit = previous.once, previous.edit
C, S, ROOT = previous.C, previous.S, previous.ROOT
CONTROLLER = previous.CONTROLLER
OBD = 'smali/com/navdy/hud/app/obd/ObdManager$Anon5.smali'
POWER = 'smali/com/navdy/hud/app/device/PowerManager.smali'
SHUTDOWN = 'smali/com/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver$ShutdownRunnable.smali'
TASK = ROOT + 'AmbientLightController$ShutdownOff.smali'
RESUME = ROOT + 'AmbientLightController$ResumeShutdown.smali'
NAMES = [CONTROLLER, OBD, POWER, SHUTDOWN]
POLICY = 'Lcom/navdy/hud/app/ambient/LowVoltagePolicy;'


def transform(files):
  result = dict(files)
  text = files[OBD]
  start = text.index('    .line 375\n')
  end = text.index('    .line 389\n', start)
  assert '->sleep(Z)V' in text[start:end] and '->post(Ljava/lang/Object;)V' in text[start:end]
  # Do not merely suppress the final Android shutdown: the old path first sleeps
  # the OBD device, so that entire low-voltage action must become observation-only.
  text = text[:start] + f'''    invoke-static {{v3, v4}}, {POLICY}->report(D)V
    goto/16 :goto_2

''' + text[end:]
  result[OBD] = text
  result[POWER] = edit(files[POWER], 'public androidShutdown(Lcom/navdy/hud/app/event/Shutdown$Reason;Z)V',
      lambda body: once(body, '    .prologue\n', f'''    .prologue
    invoke-virtual {{p1}}, Ljava/lang/Enum;->name()Ljava/lang/String;
    move-result-object v0
    invoke-static {{v0}}, {POLICY}->suppress(Ljava/lang/String;)Z
    move-result v0
    if-eqz v0, :power_reason_allowed
    return-void
    :power_reason_allowed
'''))
  shutdown_cls = 'Lcom/navdy/hud/app/service/ShutdownMonitor$NotificationReceiver$ShutdownRunnable;'
  text = once(files[SHUTDOWN], '# instance fields\n', '# instance fields\n.field private ambientPrepared:Z\n')
  anchor = '    iget-object v5, v9, Lcom/navdy/hud/app/event/Shutdown;->reason:Lcom/navdy/hud/app/event/Shutdown$Reason;'
  text = once(text, anchor, anchor + f'''
    invoke-virtual {{v5}}, Ljava/lang/Enum;->name()Ljava/lang/String;
    move-result-object v9
    invoke-static {{v9}}, {POLICY}->suppress(Ljava/lang/String;)Z
    move-result v10
    if-eqz v10, :shutdown_reason_allowed
    return-void
    :shutdown_reason_allowed
    invoke-static {{v9}}, {POLICY}->canWaitForOff(Ljava/lang/String;)Z
    move-result v10
    if-eqz v10, :ambient_done
    iget-boolean v10, p0, {shutdown_cls}->ambientPrepared:Z
    if-nez v10, :ambient_done
    const/4 v10, 0x1
    iput-boolean v10, p0, {shutdown_cls}->ambientPrepared:Z
    invoke-static {{p0}}, {C}->prepareShutdown(Ljava/lang/Runnable;)Z
    move-result v10
    if-eqz v10, :ambient_done
    return-void
    :ambient_done
''')
  result[SHUTDOWN] = text
  text = once(files[CONTROLLER], '.field private mSkipRememberedOnce:Z',
              '.field private mSkipRememberedOnce:Z\n\n.field private mShuttingDown:Z')
  text = edit(text, 'private ambientOutputBlocked()Z', lambda body: once(body,
      '    .locals 1\n', f'''    .locals 1
    iget-boolean v0, p0, {C}->mShuttingDown:Z
    if-nez v0, :blocked
'''))
  # After repeated failures, wait for a fresh advertisement instead of alternating
  # cached and bonded addresses forever. Keep the existing master/slave filter.
  text = edit(text, 'private connectIfNeeded()V', lambda body: once(body,
      '    .line 1384\n', f'''    iget-object v0, p0, {C}->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;
    check-cast v0, {S}
    invoke-virtual {{v0}}, {S}->requiresFreshScan()Z
    move-result v0
    if-nez v0, :cond_4
    .line 1384
'''))
  text = edit(text, 'private connectDevice(Landroid/bluetooth/BluetoothDevice;)V', lambda body: once(body,
      '    invoke-virtual {p1, v1, v0, v2}, Landroid/bluetooth/BluetoothDevice;->connectGatt(Landroid/content/Context;ZLandroid/bluetooth/BluetoothGattCallback;)Landroid/bluetooth/BluetoothGatt;',
      f'''    check-cast v2, {S}
    invoke-virtual {{v2, p1, v1}}, {S}->connect(Landroid/bluetooth/BluetoothDevice;Landroid/content/Context;)Landroid/bluetooth/BluetoothGatt;'''))
  text += f'''
.method public static prepareShutdown(Ljava/lang/Runnable;)Z
    .locals 3
    sget-object v0, {C}->sInstance:{C}
    if-eqz v0, :not_running
    iget-object v1, v0, {C}->mHandler:Landroid/os/Handler;
    new-instance v2, Lcom/navdy/hud/app/ambient/AmbientLightController$ShutdownOff;
    invoke-direct {{v2, v0, p0}}, Lcom/navdy/hud/app/ambient/AmbientLightController$ShutdownOff;-><init>({C}Ljava/lang/Runnable;)V
    invoke-virtual {{v1, v2}}, Landroid/os/Handler;->post(Ljava/lang/Runnable;)Z
    move-result v0
    return v0
    :not_running
    const/4 v0, 0x0
    return v0
.end method

.method public shutdownOff(Ljava/lang/Runnable;)V
    .locals 3
    const/4 v0, 0x1
    iput-boolean v0, p0, {C}->mShuttingDown:Z
    invoke-direct {{p0}}, {C}->cancelOffroadTimers()V
    const-string v0, "device shutdown"
    invoke-direct {{p0, v0}}, {C}->hardAmbientOff(Ljava/lang/String;)V
    iget-object v0, p0, {C}->mGattCallback:Landroid/bluetooth/BluetoothGattCallback;
    check-cast v0, {S}
    iget-object v1, p0, {C}->mHandler:Landroid/os/Handler;
    new-instance v2, Lcom/navdy/hud/app/ambient/AmbientLightController$ResumeShutdown;
    invoke-direct {{v2, p1}}, Lcom/navdy/hud/app/ambient/AmbientLightController$ResumeShutdown;-><init>(Ljava/lang/Runnable;)V
    invoke-static {{v0, v1, v2}}, Lcom/navdy/hud/app/ambient/AmbientShutdownGate;->awaitOff({S}Landroid/os/Handler;Ljava/lang/Runnable;)V
    return-void
.end method
'''
  result[CONTROLLER] = text
  result[TASK] = f'''.class final Lcom/navdy/hud/app/ambient/AmbientLightController$ShutdownOff;
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;
.field private final owner:{C}
.field private final continuation:Ljava/lang/Runnable;
.method public constructor <init>({C}Ljava/lang/Runnable;)V
    .locals 0
    invoke-direct {{p0}}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$ShutdownOff;->owner:{C}
    iput-object p2, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$ShutdownOff;->continuation:Ljava/lang/Runnable;
    return-void
.end method
.method public run()V
    .locals 2
    iget-object v0, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$ShutdownOff;->owner:{C}
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$ShutdownOff;->continuation:Ljava/lang/Runnable;
    invoke-virtual {{v0, v1}}, {C}->shutdownOff(Ljava/lang/Runnable;)V
    return-void
.end method
'''
  result[RESUME] = '''.class final Lcom/navdy/hud/app/ambient/AmbientLightController$ResumeShutdown;
.super Ljava/lang/Object;
.implements Ljava/lang/Runnable;
.field private final continuation:Ljava/lang/Runnable;
.method public constructor <init>(Ljava/lang/Runnable;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$ResumeShutdown;->continuation:Ljava/lang/Runnable;
    return-void
.end method
.method public run()V
    .locals 3
    invoke-static {}, Lcom/navdy/service/library/task/TaskManager;->getInstance()Lcom/navdy/service/library/task/TaskManager;
    move-result-object v0
    iget-object v1, p0, Lcom/navdy/hud/app/ambient/AmbientLightController$ResumeShutdown;->continuation:Ljava/lang/Runnable;
    const/4 v2, 0x1
    invoke-virtual {v0, v1, v2}, Lcom/navdy/service/library/task/TaskManager;->execute(Ljava/lang/Runnable;I)Ljava/util/concurrent/Future;
    return-void
.end method
'''
  return result


def helper_sources():
  sources = previous.helper_sources()
  session = sources['AmbientGattSession.java']
  session = once(session, '  public void attach(', '''  public boolean requiresFreshScan() { return attemptsWithoutResponse >= 2; }

  public void recordPowerEvent(String event) { record(event); }

  public BluetoothGatt connect(android.bluetooth.BluetoothDevice device, Context context) {
    try {
      // Android 5 exposes the transport overload on this HUD through reflection.
      java.lang.reflect.Method method = android.bluetooth.BluetoothDevice.class.getMethod(
          "connectGatt", Context.class, boolean.class, BluetoothGattCallback.class, int.class);
      record("connect transport=LE freshScan=" + requiresFreshScan());
      return (BluetoothGatt) method.invoke(device, context, false, this, 2);
    } catch (NoSuchMethodException unavailable) {
      record("connect transport=AUTO compatibility fallback");
      try { return device.connectGatt(context, false, this); }
      catch (RuntimeException failure) { record("connect exception=" + failure.getClass().getSimpleName()); return null; }
    } catch (Exception failure) {
      record("connect exception=" + failure.getClass().getSimpleName());
      return null;
    }
  }

  public void attach(''')
  sources['AmbientGattSession.java'] = session
  for name in ('LowVoltagePolicy.java', 'AmbientShutdownGate.java'):
    sources[name] = (HERE / name).read_text()
  return sources
