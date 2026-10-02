import importlib.util
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1] / "output/ambient-disconnect-20261001/v153r2-build"


def load(path):
  spec = importlib.util.spec_from_file_location(path.stem, path)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module


previous = load(HERE.parent / "v153-ambient-session/test_session.py")
patch = load(HERE / "apply.py")
STUBS = dict(previous.STUBS)
STUBS["android/bluetooth/BluetoothGatt.java"] = """package android.bluetooth;
import java.util.*; public class BluetoothGatt {
 public static final int GATT_SUCCESS=0; public int busy; public List<byte[]> sent=new ArrayList<>();
 public boolean writeCharacteristic(BluetoothGattCharacteristic c){if(busy-->0)return false;sent.add(c.getValue().clone());return true;}
}"""
STUBS["android/bluetooth/BluetoothGattCharacteristic.java"] = """package android.bluetooth;
public class BluetoothGattCharacteristic {
 private byte[] value; private int type=1;
 public byte[] getValue(){return value;} public boolean setValue(byte[] v){value=v;return true;}
 public int getWriteType(){return type;} public void setWriteType(int t){type=t;}
}"""

HARNESS = """package com.navdy.hud.app.ambient;
import android.bluetooth.*; import android.os.*; import android.content.Context; import java.util.*;
public class DeliveryTest {
 static int failures, calls, disconnected; static AmbientGattSession s;
 static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
 static BluetoothGattCharacteristic packet(byte... v){BluetoothGattCharacteristic c=new BluetoothGattCharacteristic();c.setValue(v);return c;}
 static byte[] off={(byte)46,(byte)141,4,0,0,0,0,110};
 public static void main(String[] args){
  Handler h=new Handler(); BluetoothGatt g=new BluetoothGatt();
  AmbientWriteLane q=new AmbientWriteLane(h,new AmbientWriteLane.Failure(){
   public void failed(String m){failures++;} public void submitted(byte[] b){}
  });
  BluetoothGattCharacteristic c=packet((byte)1);
  check(q.offer(g,c),"accept first");h.drain();
  c.setValue(new byte[]{(byte)255});q.offer(g,c);h.drain();
  check(g.sent.size()==1,"ACK cannot overlap active GATT write");
  c.setValue(off);q.offer(g,c);c.setValue(new byte[]{99});
  q.completed(g,c,0);h.drain();check(g.sent.size()==2&&g.sent.get(1)[0]==(byte)255,"ACK priority and immutable bytes");
  q.completed(g,c,0);h.drain();check(Arrays.equals(g.sent.get(2),off),"OFF preserved after ACK");
  q.completed(g,c,0);h.drain();q.close();h.advance(2000);check(failures==0,"completed timer canceled");

  h=new Handler();g=new BluetoothGatt();g.busy=3;
  q=new AmbientWriteLane(h,new AmbientWriteLane.Failure(){public void failed(String m){failures++;}public void submitted(byte[] b){}});
  c=packet((byte)42);q.offer(g,c);h.drain();h.advance(30);h.advance(30);
  check(g.sent.isEmpty()&&failures==0,"temporary busy does not disconnect");h.advance(30);
  check(g.sent.size()==1,"busy recovers on fourth try");q.completed(g,c,0);q.close();
  h.advance(2000);check(failures==0,"closed lane has no live timers");

  h=new Handler();g=new BluetoothGatt();
  q=new AmbientWriteLane(h,new AmbientWriteLane.Failure(){public void failed(String m){failures++;}public void submitted(byte[] b){}});
  c=packet((byte)12);q.offer(g,c);h.drain();h.advance(1000);check(failures==1,"lost local callback recovers");
  q.completed(g,c,0);h.drain();check(g.sent.size()==1,"retired callback cannot resume lane");

  h=new Handler();g=new BluetoothGatt();g.busy=100;
  q=new AmbientWriteLane(h,new AmbientWriteLane.Failure(){public void failed(String m){failures++;}public void submitted(byte[] b){}});
  c=packet(off);q.offer(g,c);h.drain();
  q.offer(g,packet((byte)255));h.drain();check(g.busy==99,"new ACK cannot bypass busy backoff");
  for(int i=0;i<9;i++)h.advance(30);
  check(failures==2&&g.sent.isEmpty(),"busy recovery is bounded");

  h=new Handler();g=new BluetoothGatt();
  q=new AmbientWriteLane(h,new AmbientWriteLane.Failure(){public void failed(String m){failures++;}public void submitted(byte[] b){}});
  c=packet((byte)12);q.offer(g,c);h.drain();
  byte[] on=off.clone();on[4]=40;on[7]=70;
  q.offer(g,packet(off));q.offer(g,packet(on));
  q.completed(g,c,0);h.drain();check(g.sent.size()==2&&Arrays.equals(g.sent.get(1),on),"unsent old brightness is coalesced");q.close();

  h=new Handler();g=new BluetoothGatt();final Handler handler=h;
  s=new AmbientGattSession(new BluetoothGattCallback(){
   public void onConnectionStateChange(BluetoothGatt g,int status,int state){if(state==0){disconnected++;s.detach();}}
   public void onCharacteristicChanged(BluetoothGatt g,BluetoothGattCharacteristic c){calls++;}
  },h,new Context());
  check(s.needsDelivery(),"cold start must reconcile independently powered lights even with an empty queue");
  s.attach(g);c=packet(off);s.write(g,c);h.drain();check(s.needsDelivery(),"dequeued OFF stays pending");
  s.onCharacteristicWrite(g,c,0);h.drain();check(s.needsDelivery(),"ATT success is not module confirmation");
  h.advance(1500);check(disconnected==1&&s.needsDelivery(),"lost final OFF still requires reconnect after successful ATT and empty queue");
  BluetoothGatt old=g;g=new BluetoothGatt();s.attach(g);
  BluetoothGattCharacteristic n=packet(off);s.onCharacteristicChanged(old,n);h.drain();
  check(calls==0&&s.needsDelivery(),"old response cannot confirm replacement session");
  c=packet(off);s.write(g,c);h.drain();s.onCharacteristicChanged(g,n);h.drain();
  check(calls==1&&!s.needsDelivery(),"matching response confirms OFF");
  s.onCharacteristicWrite(g,c,0);h.drain();h.advance(1500);
  check(disconnected==1,"matching response cancels OFF timeout");
  s.write(g,packet(off));h.drain();s.onCharacteristicChanged(g,packet((byte)0xfc));h.drain();
  check(disconnected==2&&s.needsDelivery(),"NACK never counts as successful OFF");
  s.detach();s.attach(new BluetoothGatt());
  byte[] bad=off.clone();bad[7]=0;check(AmbientGattSession.normalizedResponse(bad)==null,"checksum validated");
  byte[] both=new byte[9];both[0]=(byte)255;System.arraycopy(off,0,both,1,8);
  check(Arrays.equals(AmbientGattSession.normalizedResponse(both),off),"stock ACK+frame framing supported");
  check(AmbientGattSession.normalizedResponse(new byte[]{(byte)255}).length==1,"standalone ACK recognized");
  for(int i=0;i<20;i++){s.detach();s.attach(new BluetoothGatt());}
  SystemClock.now=1000;check(s.deferReconnect(0)==60000,"failed connections bounded at one per minute");
  SystemClock.now=2000;check(!s.canConnect(),"payload cannot bypass retry backoff");
  SystemClock.now=61000;check(s.canConnect(),"recovery is not permanently disabled");
  System.out.println("PASS delivery: serialized ACK/state writes, immutable payloads, busy retries, callback timeout, lost OFF, stale callback, ACK framing, bounded reconnect");
 }
}"""


class DeliveryTests(unittest.TestCase):
  def test_retains_session_guards(self):
    harness = previous.HARNESS.replace("byte[] value={46};", "byte[] value={46,(byte)141,4,0,0,0,0,110};")
    harness = harness.replace('    check(session.canConnect(),"first connection has no cooldown");',
        '    session=new AmbientGattSession(new BluetoothGattCallback(){},h,new Context());session.attach(b);\n'
        '    check(session.canConnect(),"first connection has no cooldown");')
    with tempfile.TemporaryDirectory() as tmp:
      root = Path(tmp)
      for name, content in STUBS.items():
        file = root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content)
      (root / "SessionTest.java").write_text(harness)
      subprocess.run([str(previous.JAVA.with_name("javac")), "-d", str(root),
                      *map(str, root.rglob("*.java")), *map(str, HERE.glob("*.java"))], check=True)
      subprocess.run([str(previous.JAVA), f"-Dtest.dir={root}", "-cp", str(root), "SessionTest"], check=True)

  def test_runtime_regressions(self):
    with tempfile.TemporaryDirectory() as tmp:
      root = Path(tmp)
      for name, content in STUBS.items():
        file = root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content)
      (root / "DeliveryTest.java").write_text(HARNESS)
      java = previous.JAVA
      subprocess.run([str(java.with_name("javac")), "-d", str(root), *map(str, root.rglob("*.java")),
                      *map(str, HERE.glob("*.java"))], check=True)
      subprocess.run([str(java), f"-Dtest.dir={root}", "-cp", str(root),
                      "com.navdy.hud.app.ambient.DeliveryTest"], check=True)

  def test_patch_scope_and_old_failure(self):
    before = {name: (BASE / name).read_text() for name in patch.NAMES}
    # The old timeout drops the outstanding command and simply flushes the queue.
    self.assertIn("access$2500", before[patch.TIMEOUT])
    self.assertNotIn("access$1700", before[patch.TIMEOUT])
    after = patch.transform(before)
    methods = lambda text: dict(re.findall(r"(?ms)^\.method ([^\n]+)\n(.*?)^\.end method", text))
    a, b = methods(before[patch.CONTROLLER]), methods(after[patch.CONTROLLER])
    self.assertEqual({name for name in a if a[name] != b[name]},
                     {"private flushNext()V", "private writeAck()V", "private needsConnection()Z"})
    self.assertNotIn("->writeCharacteristic(", after[patch.CONTROLLER])
    self.assertIn("access$10200", after[patch.TIMEOUT])
    self.assertIn("no_ack_for_ack", after[patch.CALLBACK])
    with self.assertRaises(AssertionError): patch.transform(after)


if __name__ == "__main__": unittest.main()
