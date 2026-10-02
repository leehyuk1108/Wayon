import importlib.util
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
import apply

HERE = Path(__file__).resolve().parent
BASE = Path(os.environ.get('NAVDY_V155_DECODE',
  str(HERE.parents[1] / 'output/ambient-disconnect-20261002/v155r2-build')))
spec = importlib.util.spec_from_file_location('off_tests', HERE.parent / 'v155-ambient-off-priority/test_off_priority.py')
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
STUBS = dict(old.delivery.STUBS)
STUBS['android/bluetooth/BluetoothDevice.java'] = '''package android.bluetooth;
import android.content.Context;
public class BluetoothDevice {
 public int transport; public boolean fail;
 public BluetoothGatt connectGatt(Context c,boolean a,BluetoothGattCallback cb){transport=0;return new BluetoothGatt();}
 public BluetoothGatt connectGatt(Context c,boolean a,BluetoothGattCallback cb,int t){
  transport=t;if(fail)throw new IllegalStateException("radio unavailable");return new BluetoothGatt();
 }
}'''
HARNESS = '''package com.navdy.hud.app.ambient;
import android.bluetooth.*;import android.content.Context;import android.os.*;
public class PowerTest {
 static int continued;
 static void check(boolean value,String label){if(!value)throw new AssertionError(label);}
 static BluetoothGattCharacteristic packet(byte[] data){BluetoothGattCharacteristic c=new BluetoothGattCharacteristic();c.setValue(data);return c;}
 public static void main(String[] args){
  check(LowVoltagePolicy.suppress("LOW_VOLTAGE"),"low voltage suppressed");
  check(LowVoltagePolicy.suppress("CRITICAL_VOLTAGE"),"critical voltage suppressed");
  for(String r:new String[]{"HIGH_TEMPERATURE","POWER_LOSS","ACCELERATE_SHUTDOWN","MENU","POWER_BUTTON","OTA","ENGINE_OFF","INACTIVITY","FACTORY_RESET","FORCED_UPDATE","TIMEOUT","UNKNOWN","DIAL_OTA"})
   check(!LowVoltagePolicy.suppress(r),"other shutdown preserved: "+r);
  check(!LowVoltagePolicy.canWaitForOff("HIGH_TEMPERATURE"),"thermal shutdown never delayed");
  check(!LowVoltagePolicy.canWaitForOff("POWER_LOSS"),"power loss never delayed");
  check(LowVoltagePolicy.canWaitForOff("POWER_BUTTON"),"manual shutdown waits for OFF");
  LowVoltagePolicy.report(11.8);LowVoltagePolicy.report(11.8);
  Handler h=new Handler();AmbientGattSession s=new AmbientGattSession(new BluetoothGattCallback(){},h,new Context());
  BluetoothDevice d=new BluetoothDevice();BluetoothGatt g=s.connect(d,new Context());
  check(g!=null&&d.transport==2,"LE transport selected");
  d.fail=true;check(s.connect(d,new Context())==null,"connect exceptions are bounded");
  check(!s.requiresFreshScan(),"first connection may use saved address");
  s.attach(g);s.detach();s.attach(new BluetoothGatt());s.detach();
  check(s.requiresFreshScan(),"repeated failure requires current advertisement");
  h=new Handler();s=new AmbientGattSession(new BluetoothGattCallback(){},h,new Context());
  SystemClock.now=10000;
  AmbientShutdownGate.awaitOff(s,h,new Runnable(){public void run(){continued++;}});
  h.drain();check(continued==0,"missing module is not reported OFF");
  SystemClock.now=11499;h.advance(1499);check(continued==0,"wait is not prematurely released");
  SystemClock.now=11549;h.advance(50);check(continued==1,"shutdown bounded despite missing module");
  h.advance(10000);check(continued==1,"continuation exactly once");
  h=new Handler();s=new AmbientGattSession(new BluetoothGattCallback(){},h,new Context());g=new BluetoothGatt();s.attach(g);
  byte[] off={46,(byte)141,4,0,0,0,0,110};BluetoothGattCharacteristic c=packet(off);
  s.offRequested("device shutdown");s.write(g,c);h.drain();
  SystemClock.now=20000;AmbientShutdownGate.awaitOff(s,h,new Runnable(){public void run(){continued++;}});h.drain();
  s.onCharacteristicWrite(g,c,0);h.drain();check(continued==1,"ATT callback is not module OFF confirmation");
  s.onCharacteristicChanged(g,packet(off));h.drain();SystemClock.now+=50;h.advance(50);
  check(continued==2&&!s.needsDelivery(),"module response releases shutdown");
  check(!s.requiresFreshScan(),"module response resets failed-attempt state");
  h.advance(2000);check(continued==2,"response and timeout cannot both continue");
  System.out.println("PASS power policy, thermal/manual preservation, LE connect, fresh-scan recovery, asynchronous bounded OFF handshake");
 }
}'''


class PowerTests(unittest.TestCase):
  def execute(self, harness, name, fallback=False):
    with tempfile.TemporaryDirectory() as directory:
      root = Path(directory)
      stubs = dict(STUBS)
      if fallback:
        stubs['android/bluetooth/BluetoothDevice.java'] = '''package android.bluetooth;
import android.content.Context;public class BluetoothDevice {public int calls;
public BluetoothGatt connectGatt(Context c,boolean a,BluetoothGattCallback b){calls++;return new BluetoothGatt();}}'''
      for filename, content in {**stubs, **apply.helper_sources(), name+'.java': harness}.items():
        path = root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
      java = old.delivery.previous.JAVA
      subprocess.run([str(java.with_name('javac')), '-d', str(root), *map(str, root.rglob('*.java'))], check=True)
      subprocess.run([str(java), '-Dtest.dir='+str(root), '-cp', str(root),
                      'com.navdy.hud.app.ambient.'+name], check=True)

  def test_power_and_recovery(self):
    self.execute(HARNESS, 'PowerTest')

  def test_legacy_transport_fallback(self):
    self.execute('''package com.navdy.hud.app.ambient;import android.bluetooth.*;import android.os.*;import android.content.*;
public class FallbackTest {public static void main(String[] a){BluetoothDevice d=new BluetoothDevice();
AmbientGattSession s=new AmbientGattSession(new BluetoothGattCallback(){},new Handler(),new Context());
if(s.connect(d,new Context())==null||d.calls!=1)throw new AssertionError("legacy fallback");}}''', 'FallbackTest', True)

  def test_existing_off_priority(self):
    self.execute(old.HARNESS, 'OffPriorityTest')

  def test_existing_delivery(self):
    self.execute(old.delivery.HARNESS, 'DeliveryTest')

  def test_scope(self):
    before = {n: (BASE/n).read_text() for n in apply.NAMES}
    after = apply.transform(before)
    methods = lambda text: dict(re.findall(r'(?ms)^\.method ([^\n]+)\n(.*?)^\.end method', text))
    a, b = methods(before[apply.CONTROLLER]), methods(after[apply.CONTROLLER])
    self.assertEqual({n for n in a if a[n] != b[n]}, {
      'private ambientOutputBlocked()Z', 'private connectDevice(Landroid/bluetooth/BluetoothDevice;)V',
      'private connectIfNeeded()V'})
    self.assertNotIn('->sleep(Z)V', after[apply.OBD].split('    .line 389\n')[0])
    self.assertEqual(before[apply.OBD].split('    .line 389\n')[1],
                     after[apply.OBD].split('    .line 389\n')[1])
    self.assertNotIn('Battery Voltage is too low, shutting down', after[apply.OBD])
    self.assertIn('->report(D)V', after[apply.OBD])
    for n in (apply.POWER, apply.SHUTDOWN):
      self.assertIn('->suppress(Ljava/lang/String;)Z', after[n])
    self.assertIn('->canWaitForOff(Ljava/lang/String;)Z', after[apply.SHUTDOWN])
    self.assertIn('->prepareShutdown(Ljava/lang/Runnable;)Z', after[apply.SHUTDOWN])
    self.assertIn('mShuttingDown', b['private ambientOutputBlocked()Z'])
    self.assertIn('->execute(Ljava/lang/Runnable;I)', after[apply.RESUME])
    self.assertIn('AmbientLightController$ResumeShutdown', b['public shutdownOff(Ljava/lang/Runnable;)V'])
    self.assertIn('const-string p1, "slave"', after[apply.CONTROLLER])
    with self.assertRaises((AssertionError, ValueError)):
      apply.transform(after)


if __name__ == '__main__':
  unittest.main()
