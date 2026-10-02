import importlib.util
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
import apply

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("delivery_tests", HERE.parent / "v154-ambient-delivery/test_delivery.py")
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)
BASE = HERE.parents[1] / "output/ambient-disconnect-20261002/v154r2-build"

HARNESS = """package com.navdy.hud.app.ambient;
import android.bluetooth.*; import android.os.*; import java.util.*;
public class OffPriorityTest {
 static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
 static BluetoothGattCharacteristic packet(byte[] v){BluetoothGattCharacteristic c=new BluetoothGattCharacteristic();c.setValue(v);return c;}
 public static void main(String[] args){
  byte[] off={46,(byte)141,4,0,0,0,0,110};
  byte[] on={46,(byte)141,4,0,72,50,80,(byte)164};
  byte[] color={46,(byte)141,8,1,8,1,2,3,4,5,6,7};
  byte[] start={46,(byte)129,1,1,124};
  for(int scenario=0;scenario<4;scenario++){
   Handler h=new Handler();BluetoothGatt g=new BluetoothGatt();
   AmbientWriteLane lane=new AmbientWriteLane(h,new AmbientWriteLane.Failure(){
    public void failed(String r){throw new AssertionError(r);}public void submitted(byte[] b){}
   });
   BluetoothGattCharacteristic active=packet(scenario==0?on:new byte[]{(byte)255});
   lane.offer(g,active);h.drain();
   lane.offer(g,packet(color));lane.offer(g,packet(on));
   lane.offer(g,packet(new byte[]{(byte)255}));
   if(scenario>=2)lane.discardQueuedState();
   if(scenario==3)lane.offer(g,packet(start));
   lane.offer(g,packet(off));
   check(g.sent.size()==1,"OFF must not overlap the accepted ATT write");
   lane.completed(g,active,0);h.drain();
   check(g.sent.get(1).length==1,"protocol ACK retained");
   // Separate characteristics in this harness make callback identity explicit.
   java.lang.reflect.Field f;
   try {
    f=AmbientWriteLane.class.getDeclaredField("active");f.setAccessible(true);
    while(f.get(lane)!=null){
     Object item=f.get(lane);java.lang.reflect.Field cf=item.getClass().getDeclaredField("characteristic");cf.setAccessible(true);
     lane.completed(g,(BluetoothGattCharacteristic)cf.get(item),0);h.drain();
    }
   }catch(Exception e){throw new RuntimeException(e);}
   check(Arrays.equals(g.sent.get(g.sent.size()-1),off),"last state is OFF");
   for(int i=1;i<g.sent.size();i++)check(!Arrays.equals(g.sent.get(i),on)&&!Arrays.equals(g.sent.get(i),color),"obsolete color/ON discarded");
   check(g.sent.size()==(scenario==3?4:3),"ACK and handshake retained, no stale states");
   lane.close();h.advance(2000);
  }
  check(!AmbientWriteLane.isOff(on),"ON cannot be mistaken for OFF");
  check(AmbientWriteLane.isOff(off),"OFF recognized");
  System.out.println("PASS OFF priority: active write, queued ACK/color/brightness, handshake, both queues, timeout cleanup");
 }
}"""


class OffTests(unittest.TestCase):
  def execute(self, harness, class_name):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      for name, content in {**delivery.STUBS, **apply.helper_sources(), class_name + ".java": harness}.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
      java = delivery.previous.JAVA
      subprocess.run([str(java.with_name("javac")), "-d", str(root), *map(str, root.rglob("*.java"))], check=True)
      subprocess.run([str(java), f"-Dtest.dir={root}", "-cp", str(root),
                      "com.navdy.hud.app.ambient." + class_name], check=True)

  def test_off_preempts_all_old_state(self):
    self.execute(HARNESS, "OffPriorityTest")

  def test_existing_delivery_regressions(self):
    self.execute(delivery.HARNESS, "DeliveryTest")

  def test_controller_scope(self):
    before = {apply.CONTROLLER: (BASE / apply.CONTROLLER).read_text()}
    after = apply.transform(before)
    parse = lambda text: dict(re.findall(r"(?ms)^\.method ([^\n]+)\n(.*?)^\.end method", text))
    old, new = parse(before[apply.CONTROLLER]), parse(after[apply.CONTROLLER])
    self.assertEqual(set(new) - set(old), {"private ambientOutputBlocked()Z"})
    self.assertEqual({name for name in old if old[name] != new[name]}, {
        "private sendPacket([B)V", "private startAmbientFade(IIJ[B)V",
        "private restoreActiveStateAfterConnect()V", "private hardAmbientOff(Ljava/lang/String;)V",
        "private setGearText(Ljava/lang/String;)V", "private setAmbientProfile(Lorg/json/JSONObject;)V"})
    for signature in ("private sendPacket([B)V", "private startAmbientFade(IIJ[B)V",
                      "private restoreActiveStateAfterConnect()V"):
      self.assertIn("->ambientOutputBlocked()Z", new[signature])
    for token in ("offRequested", "stopBlink", "stopBrightnessSync", "mOverspeedStateRunnable", "mWriting"):
      self.assertIn(token, new["private hardAmbientOff(Ljava/lang/String;)V"])
    with self.assertRaises(AssertionError): apply.transform(after)


if __name__ == "__main__": unittest.main()
