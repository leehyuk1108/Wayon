"""Run on comma: read-only, bounded Navdy ignition/BLE/power capture."""
import json
import re
import select
import subprocess
import sys
import time
from pathlib import Path

ADB = ['adb', '-P', '5038', '-s', 'FPI647618N4111AT']
ROOT = Path('/data/tmp/navdy-v156')
ROOT.mkdir(parents=True, exist_ok=True)
OUT = ROOT / ('ignition-' + time.strftime('%Y%m%d-%H%M%S') + '.jsonl')
MATCH = re.compile(r'ambient|voltage|shut.?down|BluetoothManagerService|BluetoothGatt|btif_dm|AdapterState|Wakefulness', re.I)


def shell(command):
  return subprocess.check_output(ADB + ['shell', command], timeout=6).decode(errors='replace').strip()


def main():
  with OUT.open('w') as output:
    def record(kind, value):
      item = {'utc': time.time(), 'kind': kind, 'value': value}
      output.write(json.dumps(item) + '\n')
      output.flush()
      if kind != 'logcat':
        print(json.dumps(item), flush=True)

    record('baseline', {'onroad': Path('/data/params/d/IsOnroad').read_text(),
        'boot': shell('cat /proc/sys/kernel/random/boot_id'),
        'uptime': shell('cat /proc/uptime')})
    proc = subprocess.Popen(ADB + ['logcat', '-v', 'threadtime', '-T', '1'],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
    pending = b''
    last_onroad = None
    last_event = ''
    deadline = time.monotonic() + (int(sys.argv[1]) if len(sys.argv) > 1 else 480)
    next_state = 0
    next_power = 0
    print('READY read-only capture ' + str(OUT), flush=True)
    try:
      while time.monotonic() < deadline:
        if select.select([proc.stdout], [], [], 0.2)[0]:
          chunk = proc.stdout.read(65536)
          if not chunk:
            record('logcat_ended', proc.poll())
            proc.wait(timeout=3)
            time.sleep(1)
            proc = subprocess.Popen(ADB + ['logcat', '-v', 'threadtime', '-T', '80'],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)
            pending = b''
            continue
          pending += chunk
          lines = pending.split(b'\n')
          pending = lines.pop()
          for raw in lines:
            line = raw.decode(errors='replace')
            if MATCH.search(line):
              record('logcat', line)
        now = time.monotonic()
        if now < next_state:
          continue
        next_state = now + 2
        onroad = Path('/data/params/d/IsOnroad').read_text()
        if onroad != last_onroad:
          record('onroad', onroad)
          last_onroad = onroad
        try:
          events = shell('busybox tail -n 12 /data/data/com.navdy.hud.app/files/ambient-ble-events.log')
          if events != last_event:
            record('ambient_events', events)
            last_event = events
          if now >= next_power:
            next_power = now + 30
            power = shell('dumpsys power')
            voltage = shell('busybox tail -n 20 /data/media/0/.logs/obd.log')
            record('power', {'boot': shell('cat /proc/sys/kernel/random/boot_id'),
                'uptime': shell('cat /proc/uptime'),
                'display': [l for l in power.splitlines() if any(x in l for x in
                    ['mWakefulness=', 'Display Power:', 'NavdyAmbient:'])],
                'voltage': [l for l in voltage.splitlines() if 'Battery voltage:' in l][-1:]})
        except subprocess.SubprocessError as exc:
          record('adb_error', type(exc).__name__)
    finally:
      proc.terminate()
      try:
        proc.wait(timeout=3)
      except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
      record('capture_complete', str(OUT))


if __name__ == '__main__':
  main()
