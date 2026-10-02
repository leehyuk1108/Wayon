import android.content.Context;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGattCallback;
import android.os.Handler;
import java.lang.reflect.*;

/** Isolated ART regression; no live adapter, main loop, or shutdown invocation. */
public class PowerProbe extends ControllerProbe {
  public static void main(String[] args) {
    try {
      ControllerProbe.run();
      Class<?> policy = Class.forName("com.navdy.hud.app.ambient.LowVoltagePolicy");
      Method suppress = policy.getMethod("suppress", String.class);
      check((Boolean)suppress.invoke(null, "LOW_VOLTAGE"), "low voltage suppressed on ART");
      check((Boolean)suppress.invoke(null, "CRITICAL_VOLTAGE"), "critical voltage suppressed on ART");
      for (String reason : new String[]{"HIGH_TEMPERATURE", "POWER_LOSS", "POWER_BUTTON", "OTA"})
        check(!(Boolean)suppress.invoke(null, reason), "preserved shutdown: " + reason);
      Class<?> unsafe = Class.forName("sun.misc.Unsafe");
      Object allocator = null;
      for (Field f : unsafe.getDeclaredFields()) if (f.getType() == unsafe) {
        f.setAccessible(true); allocator = f.get(null); break;
      }
      Class<?> power = Class.forName("com.navdy.hud.app.device.PowerManager");
      Object isolatedPower = unsafe.getMethod("allocateInstance", Class.class).invoke(allocator, power);
      Class<?> reasonClass = Class.forName("com.navdy.hud.app.event.Shutdown$Reason");
      Class<?> eventClass = Class.forName("com.navdy.hud.app.event.Shutdown");
      Class<?> receiverClass = Class.forName("com.navdy.hud.app.service.ShutdownMonitor$NotificationReceiver");
      Class<?> runnableClass = Class.forName(receiverClass.getName() + "$ShutdownRunnable");
      Constructor<?> shutdown = runnableClass.getDeclaredConstructor(receiverClass, eventClass);
      shutdown.setAccessible(true);
      // All device handles and the parent receiver are null. A missing guard
      // fails with NPE before any real device operation; no event is posted.
      for (String name : new String[]{"LOW_VOLTAGE", "CRITICAL_VOLTAGE"}) {
        Object reason = reasonClass.getField(name).get(null);
        power.getMethod("androidShutdown", reasonClass, boolean.class).invoke(isolatedPower, reason, true);
        check(true, "power API returns before side effects: " + name);
        Object event = eventClass.getConstructor(reasonClass).newInstance(reason);
        ((Runnable)shutdown.newInstance(null, event)).run();
        check(true, "shutdown worker returns before side effects: " + name);
      }
      BluetoothDevice.class.getMethod("connectGatt", Context.class, boolean.class,
          BluetoothGattCallback.class, int.class);
      check(true, "device Android supports explicit LE transport");
      // Resolve both changed DEX files. Never call actual platform shutdown APIs.
      for (String name : new String[]{"com.navdy.hud.app.device.PowerManager",
          "com.navdy.hud.app.obd.ObdManager$Anon5",
          "com.navdy.hud.app.service.ShutdownMonitor$NotificationReceiver$ShutdownRunnable"}) {
        Class.forName(name, false, PowerProbe.class.getClassLoader()).getDeclaredMethods();
        check(true, "ART resolves " + name);
      }
      Object o = fresh();
      vehicle(o, true, false); gear(o, "d");
      call(o, "shutdownOff", new Class<?>[]{Runnable.class}, new Runnable() {
        public void run() { throw new AssertionError("probe must not pump shutdown continuation"); }
      });
      check((Boolean)get(o, "mShuttingDown"), "shutdown barrier latched");
      onlyOff(o, "shutdown preempts ON queue");
      vehicle(o, true, true); fade(o, 20, 100);
      call(o, "setOverspeed", new Class<?>[]{boolean.class}, true);
      ((Runnable)get(o, "mBlinkRunnable")).run();
      simple(o, "restoreActiveStateAfterConnect");
      onlyOff(o, "door/overspeed/reconnect cannot override shutdown OFF");
      check(get(o, "mGatt") == null && get(o, "mAdapter") == null,
          "power regression made no Bluetooth connections");
      ((Handler)get(o, "mHandler")).removeCallbacksAndMessages(null);
      System.out.println("PASS v156 actual DEX checks=" + checks + "; no live light or power commands");
      System.exit(0);
    } catch (Throwable failure) {
      failure.printStackTrace(System.out);
      System.exit(1);
    }
  }
}
