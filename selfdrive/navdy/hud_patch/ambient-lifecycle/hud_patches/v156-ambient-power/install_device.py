"""Run on comma after the isolated probe; preserve app data and verify readback."""
import hashlib
import json
import subprocess
import time
from pathlib import Path

ADB = ['adb', '-P', '5038', '-s', 'FPI647618N4111AT']
ROOT = Path('/data/tmp/navdy-v156')
APK = ROOT / 'Hud-v156-signed.apk'
EXPECTED = '4e819112d0ad57eb908766f47c94247d585c0040107087a5a62ec033950e9ad2'
BASE_MD5 = '57131759254e2fc68fe6c7ad8cf8e7d4'


def shell(command):
  return subprocess.check_output(ADB + ['shell', command], timeout=60).decode(errors='replace').strip()


def snapshot():
  settings = {}
  for key in ['navdy_ambient_device_address', 'navdy_ambient_profile_json']:
    value = shell('settings get system ' + key)
    settings[key] = hashlib.sha256(value.encode()).hexdigest()
  settings['device_registry'] = hashlib.sha256(shell(
      'cat /data/data/com.navdy.hud.app/shared_prefs/DeviceRegistry.xml').encode()).hexdigest()
  return settings


def main():
  assert Path('/data/params/d/IsOnroad').read_text().strip() == '0', 'installation requires Offroad'
  assert hashlib.sha256(APK.read_bytes()).hexdigest() == EXPECTED
  installed = shell('pm path com.navdy.hud.app').removeprefix('package:')
  assert shell('busybox md5sum ' + installed).split()[0] == BASE_MD5, 'installed base changed'
  command = ('CLASSPATH=/data/local/tmp/v156-probe.jar:/data/local/tmp/v156-classes.dex:'
      '/data/local/tmp/v156-classes2.dex:/system/framework/android.test.runner.jar '
      'app_process /system/bin PowerProbe')
  probe = shell(command)
  assert 'PASS v156 actual DEX checks=50;' in probe
  (ROOT / 'probe-result.txt').write_text(probe)
  before = snapshot()
  report = {'started_utc': time.time(), 'before': before,
      'boot_before': shell('cat /proc/sys/kernel/random/boot_id')}
  (ROOT / 'installation.json').write_text(json.dumps(report, indent=2))
  # Keep staging on /cache. The HUD's /data partition is only about 494 MiB.
  for name in ['v156-probe.jar', 'v156-classes.dex', 'v156-classes2.dex']:
    shell('rm -f /data/local/tmp/' + name)
  for name in ['data@local@tmp@v156-probe.jar@classes.dex',
      'data@local@tmp@v156-classes.dex', 'data@local@tmp@v156-classes2.dex']:
    shell('rm -f /data/dalvik-cache/arm/' + name)
  subprocess.run(ADB + ['push', str(APK), '/cache/navdy-v156.apk'], check=True, timeout=60)
  assert Path('/data/params/d/IsOnroad').read_text().strip() == '0', 'state changed before install'
  result = subprocess.run(ADB + ['shell', 'pm install -r /cache/navdy-v156.apk'],
      capture_output=True, text=True, timeout=150)
  print(result.stdout, flush=True)
  print(result.stderr, flush=True)
  assert result.returncode == 0 and 'Success' in result.stdout + result.stderr
  installed = shell('pm path com.navdy.hud.app').removeprefix('package:')
  payload = subprocess.check_output(ADB + ['exec-out', 'cat', installed], timeout=60)
  actual = hashlib.sha256(payload).hexdigest()
  assert actual == EXPECTED, 'installed APK readback mismatch'
  report.update(installed_sha256=actual, installed_utc=time.time(), after=snapshot())
  assert report['before'] == report['after'], 'profile, saved module, or pairing registry changed'
  print('APK readback, ambient profile, saved module and pairing registry verified', flush=True)
  launch = shell('am start -n com.navdy.hud.app/com.navdy.hud.app.ui.activity.MainActivity')
  print(launch, flush=True)
  assert 'Error' not in launch
  time.sleep(12)
  if Path('/data/params/d/IsOnroad').read_text().strip() == '0':
    shell('input keyevent 223')
  report['boot_after'] = shell('cat /proc/sys/kernel/random/boot_id')
  report['power'] = [l for l in shell('dumpsys power').splitlines()
      if any(s in l for s in ['mWakefulness=', 'Display Power:', 'NavdyAmbient:'])]
  (ROOT / 'installation.json').write_text(json.dumps(report, indent=2))
  shell('rm -f /cache/navdy-v156.apk /cache/navdy-v156-check.oat')
  print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
  main()
