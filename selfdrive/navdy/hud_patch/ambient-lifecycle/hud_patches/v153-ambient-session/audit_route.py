"""Read-only timing audit; comma qlogs do not contain Android BLE callbacks."""
import glob
import json
from collections import Counter
from tools.lib.logreader import LogReader

route = "/data/media/0/realdata/000000f2--38a10e86e2"
paths = sorted(glob.glob(route + "--*/qlog.zst"), key=lambda p: int(p.split("--")[-1].split("/")[0]))
counts = Counter()
last = {}
gaps = {}
started = None
transitions = []
messages = []
base = None
for path in paths:
  for msg in LogReader(path):
    kind = msg.which()
    t = msg.logMonoTime / 1e9
    if base is None: base = t
    counts[kind] += 1
    if kind in ("deviceState", "carState", "selfdriveState", "pandaStates"):
      if kind in last and t > last[kind]: gaps[kind] = max(gaps.get(kind, 0), t - last[kind])
      last[kind] = t
    if kind == "deviceState" and bool(msg.deviceState.started) != started:
      started = bool(msg.deviceState.started)
      transitions.append({"elapsed_s": round(t - base, 2), "started": started})
    if kind in ("logMessage", "errorLogMessage"):
      try:
        data = json.loads(str(getattr(msg, kind)))
      except (ValueError, TypeError): continue
      text = str(data.get("msg", ""))
      if "navdy" in text.lower():
        messages.append({"elapsed_s": round(t - base, 2), "message": text[:240]})
print(json.dumps({"route": route.rsplit("/", 1)[-1], "segments": len(paths),
                  "samples": {k: counts[k] for k in last}, "max_gap_s": gaps,
                  "device_started_transitions": transitions, "navdy_messages": messages[-40:]}, indent=2))
