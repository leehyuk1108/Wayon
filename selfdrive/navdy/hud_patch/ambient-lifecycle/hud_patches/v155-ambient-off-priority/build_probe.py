"""Build the isolated ART probe; it is not included in the production APK."""
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = Path.home() / ".cache/navdy-build-tools"
JAVA = next(TOOLS.glob("jdk-*/Contents/Home/bin/java"))
ANDROID = TOOLS / "android-35/android.jar"

def run(*args): subprocess.run(list(map(str, args)), check=True)

if __name__ == "__main__":
  output, original, patched = map(Path, sys.argv[1:4])
  output.mkdir(parents=True, exist_ok=True)
  with tempfile.TemporaryDirectory() as directory:
    temp = Path(directory)
    classes = temp / "classes"
    classes.mkdir()
    run(JAVA.with_name("javac"), "-source", "8", "-target", "8", "-cp", ANDROID,
        "-d", classes, HERE / "ControllerProbe.java")
    run(JAVA, "-cp", TOOLS / "android-16/lib/d8.jar", "com.android.tools.r8.D8",
        "--min-api", "21", "--lib", ANDROID, "--output", output / "probe.jar", *classes.rglob("*.class"))
  with zipfile.ZipFile(original) as old, zipfile.ZipFile(patched) as new:
    changed = [name for name in old.namelist() if not name.startswith("META-INF/") and
               old.read(name) != new.read(name)]
    assert changed == ["classes2.dex"], changed
    for name, source in (("original.dex", old), ("patched.dex", new)):
      (output / name).write_bytes(source.read("classes2.dex"))
    print("Only APK payload difference:", changed)
