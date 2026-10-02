import importlib.util
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1] / "output/navdy-far-lead/20260930/production-decode"
JAVA = Path(os.environ['JAVA_HOME']) / 'bin/java' if os.environ.get('JAVA_HOME') else next(
  (Path.home() / '.cache/navdy-build-tools').glob('jdk-*/Contents/Home/bin/java'),
  Path(shutil.which('java') or 'java'))
spec = importlib.util.spec_from_file_location("patch", HERE / "apply.py")
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)

STUBS = {
  "android/bluetooth/BluetoothGatt.java": "package android.bluetooth; public class BluetoothGatt {public static final int GATT_SUCCESS=0;}",
  "android/bluetooth/BluetoothProfile.java": "package android.bluetooth; public interface BluetoothProfile {int STATE_CONNECTED=2, STATE_DISCONNECTED=0;}",
  "android/bluetooth/BluetoothGattCharacteristic.java": """package android.bluetooth; public class BluetoothGattCharacteristic {
    private byte[] value; public byte[] getValue(){return value;} public boolean setValue(byte[] v){value=v;return true;}}""",
  "android/bluetooth/BluetoothGattDescriptor.java": """package android.bluetooth; public class BluetoothGattDescriptor {
    public java.util.UUID getUuid(){return java.util.UUID.fromString("00002902-0000-1000-8000-00805f9b34fb");}}""",
  "android/bluetooth/BluetoothGattCallback.java": """package android.bluetooth; public class BluetoothGattCallback {
    public void onConnectionStateChange(BluetoothGatt g,int s,int n){} public void onServicesDiscovered(BluetoothGatt g,int s){}
    public void onDescriptorWrite(BluetoothGatt g,BluetoothGattDescriptor d,int s){}
    public void onCharacteristicWrite(BluetoothGatt g,BluetoothGattCharacteristic c,int s){}
    public void onCharacteristicChanged(BluetoothGatt g,BluetoothGattCharacteristic c){} }""",
  "android/content/Context.java": """package android.content; public class Context {
    public java.io.File getFilesDir(){return new java.io.File(System.getProperty("test.dir"));}}""",
  "android/util/Log.java": """package android.util; public class Log {public static int i(String t,String v){return 0;}
    public static int w(String t,String v){return 0;} public static int w(String t,String v,Throwable e){return 0;}}""",
  "android/os/Handler.java": """package android.os; import java.util.*; public class Handler {
    private final LinkedHashMap<Runnable,Long> jobs=new LinkedHashMap<>(); private long now;
    public boolean post(Runnable r){jobs.put(r,now);return true;}
    public boolean postDelayed(Runnable r,long delay){jobs.put(r,now+delay);return true;}
    public void removeCallbacks(Runnable r){jobs.remove(r);}
    public void advance(long delay){now+=delay;drain();}
    public void drain(){while(true){Runnable next=null;for(Map.Entry<Runnable,Long> e:jobs.entrySet()){
      if(e.getValue()<=now){next=e.getKey();break;}} if(next==null)return;jobs.remove(next);next.run();}}
  }""",
  "android/os/SystemClock.java": """package android.os; public class SystemClock {
    public static long now; public static long elapsedRealtime(){return now;}
  }""",
}

HARNESS = """import android.bluetooth.*; import android.os.Handler; import android.content.Context;
import com.navdy.hud.app.ambient.AmbientGattSession;
public class SessionTest {
  static int calls, services, notifications, writes, disconnected, lastByte;
  static AmbientGattSession session;
  static void check(boolean x,String message){if(!x)throw new AssertionError(message);}
  public static void main(String[] args){
    Handler h=new Handler(); BluetoothGatt a=new BluetoothGatt(), b=new BluetoothGatt();
    BluetoothGattCharacteristic c=new BluetoothGattCharacteristic();
    BluetoothGattDescriptor d=new BluetoothGattDescriptor();
    session=new AmbientGattSession(new BluetoothGattCallback(){
      public void onConnectionStateChange(BluetoothGatt g,int s,int n){calls++;if(n==0){disconnected++;session.detach();}}
      public void onServicesDiscovered(BluetoothGatt g,int s){services++;}
      public void onDescriptorWrite(BluetoothGatt g,BluetoothGattDescriptor d,int s){notifications++;}
      public void onCharacteristicWrite(BluetoothGatt g,BluetoothGattCharacteristic c,int s){writes++;}
      public void onCharacteristicChanged(BluetoothGatt g,BluetoothGattCharacteristic c){lastByte=c.getValue()[0];}
    },h,new Context());
    session.attach(a); session.onConnectionStateChange(a,0,2);
    check(calls==0,"callbacks must be queued, not mutate state on Binder threads");
    h.drain();check(calls==1,"connected delivered");
    session.onServicesDiscovered(a,0); session.onDescriptorWrite(a,d,0);h.drain();
    check(services==1&&notifications==1,"normal service/CCCD setup");
    h.advance(10001);check(disconnected==0,"successful setup cancels deadline");
    byte[] value={46};c.setValue(value);session.onCharacteristicChanged(a,c);value[0]=99;
    h.drain();check(lastByte==46,"notification value copied before posting");
    session.onCharacteristicWrite(a,c,0);session.onServicesDiscovered(a,0);
    session.onDescriptorWrite(a,d,0);session.onCharacteristicChanged(a,c);session.onConnectionStateChange(a,133,0);
    session.detach();session.attach(b);h.drain();
    check(writes==0&&services==1&&notifications==1&&disconnected==0,"all retired callbacks ignored after reconnect");
    session.onConnectionStateChange(b,0,2);h.drain();h.advance(10001);
    check(disconnected==1,"missing services/CCCD callback times out");
    session.attach(a);session.onServicesDiscovered(a,5);h.drain();
    check(disconnected==2&&services==1,"failed discovery is not accepted");
    session.attach(a);session.onDescriptorWrite(a,d,5);h.drain();
    check(disconnected==3&&notifications==1,"failed notification setup is not ready");
    session.attach(a);session.onCharacteristicWrite(a,c,133);h.drain();
    check(disconnected==4&&writes==0,"failed write enters disconnect recovery");
    session.attach(a);session.onConnectionStateChange(a,133,2);h.drain();
    check(disconnected==5,"connected state with error is not success");
    session.attach(a);session.onConnectionStateChange(a,0,2);h.drain();session.detach();session.attach(b);
    h.advance(10001);check(disconnected==5,"retired setup timer cannot disconnect replacement");
    check(session.canConnect(),"first connection has no cooldown");
    android.os.SystemClock.now=1000;session.deferReconnect(10000);session.detach();
    android.os.SystemClock.now=1080;check(!session.canConnect(),"offroad payload cannot bypass cooldown at 80 ms");
    check(session.deferReconnect(5000)==9920,"retry scheduling uses the remaining longer cooldown");
    android.os.SystemClock.now=10999;check(!session.canConnect(),"shorter retry cannot shorten error cooldown");
    android.os.SystemClock.now=11000;check(session.canConnect(),"retry allowed after 10 seconds");
    session.deferReconnect(-1);check(session.canConnect(),"negative delay is clamped");
    System.out.println("PASS: serialized/stale callbacks, setup/write failures, notification copy, independent reconnect cooldown");
  }
}"""


class SessionTests(unittest.TestCase):
  def test_runtime_session_guards(self):
    with tempfile.TemporaryDirectory() as tmp:
      root = Path(tmp)
      for name, content in STUBS.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
      (root / "SessionTest.java").write_text(HARNESS)
      subprocess.run([str(JAVA.with_name("javac")), "-d", str(root),
                      *map(str, root.rglob("*.java")), str(HERE / "AmbientGattSession.java")], check=True)
      subprocess.run([str(JAVA), f"-Dtest.dir={root}", "-cp", str(root), "SessionTest"], check=True)

  def test_patch_preserves_lighting_policy_and_filters(self):
    before = {name: (BASE / name).read_text() for name in patch.NAMES}
    after = patch.transform(before)
    def methods(text):
      return dict(re.findall(r"(?ms)^\.method ([^\n]+)\n(.*?)^\.end method", text))
    old, new = methods(before[patch.CONTROLLER]), methods(after[patch.CONTROLLER])
    changed = {name for name in old if old[name] != new[name]}
    self.assertEqual(changed, {"private constructor <init>(Landroid/content/Context;)V",
                              "private closeGatt()V", "private connectDevice(Landroid/bluetooth/BluetoothDevice;)V",
                              "private connectIfNeeded()V", "private scheduleReconnect(J)V"})
    self.assertLess(new["private scheduleReconnect(J)V"].index("deferReconnect"),
                    new["private scheduleReconnect(J)V"].index("needsConnection"))
    self.assertLess(new["private connectIfNeeded()V"].index("canConnect"),
                    new["private connectIfNeeded()V"].index("connectRememberedCandidate"))
    self.assertIn('const-string p1, "pocket"', after[patch.CONTROLLER])
    self.assertIn('const-string p1, "slave"', after[patch.CONTROLLER])
    self.assertIn("access$10100", after[patch.SCAN])
    self.assertNotIn(".line 159", after[patch.CALLBACK])
    with self.assertRaises(AssertionError): patch.transform(after)


if __name__ == "__main__": unittest.main()
