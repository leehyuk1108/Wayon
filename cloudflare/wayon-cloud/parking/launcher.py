"""Capture bootstrap failures even when Task Scheduler uses pythonw."""
from pathlib import Path
import sys
from datetime import datetime, timezone

try:
    import service
    service.main()
except BaseException as exc:
    if not isinstance(exc, KeyboardInterrupt):
        path = Path(__file__).resolve().parent.parent / "bootstrap.log"
        if path.exists() and path.stat().st_size > 100_000:
            path.replace(path.with_suffix(".previous.log"))
        with path.open("a", encoding="utf-8") as stream:
            stream.write(f"{datetime.now(timezone.utc).isoformat()} {type(exc).__name__}\n")
    sys.exit(1)
