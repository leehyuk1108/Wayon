"""Reuse the audited APK builder with generated, narrowly patched helpers."""
import importlib.util
import sys
import tempfile
from pathlib import Path
import apply

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("delivery_build", HERE.parent / "v154-ambient-delivery/build.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
builder.BASE_HASH = "6d0a43740302555fa6398ca45dc6e623d5ce409bf7a04525e6505b964307040d"

if __name__ == "__main__":
  with tempfile.TemporaryDirectory(prefix="ambient-off-build-") as directory:
    stage = Path(directory)
    # The original builder loads apply.py from HERE; retain the source's real HERE.
    (stage / "apply.py").write_text(
        f"__file__ = {str(HERE / 'apply.py')!r}\nexec(compile(open(__file__).read(), __file__, 'exec'))\n")
    for name, source in apply.helper_sources().items(): (stage / name).write_text(source)
    builder.HERE = stage
    builder.main(*map(Path, sys.argv[1:5]))
