"""Build only the BLE transport delta over the verified live v152 APK."""
import hashlib
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = Path.home() / ".cache/navdy-build-tools"
JAVA = next(TOOLS.glob("jdk-*/Contents/Home/bin/java"))
ANDROID = TOOLS / "android-35/android.jar"
APKTOOL = TOOLS / "apktool_3.0.3.jar"
BASE_HASH = "986ada31a9c855f4ba38abb9e3bdc7e2e0d46dee571de75cc50112f2f3388627"


def run(*args): subprocess.run(list(map(str, args)), check=True)


def main(base, original, output, apk):
  assert hashlib.sha256(base.read_bytes()).hexdigest() == BASE_HASH
  assert not output.exists(), "use a fresh output directory"
  shutil.copytree(original, output, ignore=shutil.ignore_patterns("build", "dist"))
  spec = importlib.util.spec_from_file_location("patch", HERE / "apply.py")
  patch = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(patch)
  before = {name: (output / name).read_text() for name in patch.NAMES}
  for name, content in patch.transform(before).items(): (output / name).write_text(content)
  with tempfile.TemporaryDirectory(prefix="ambient-session-") as temp:
    temp = Path(temp)
    classes, dex = temp / "classes", temp / "dex"
    classes.mkdir()
    dex.mkdir()
    run(JAVA.with_name("javac"), "-source", "8", "-target", "8", "-cp", ANDROID,
        "-d", classes, HERE / "AmbientGattSession.java")
    run(JAVA, "-cp", TOOLS / "android-16/lib/d8.jar", "com.android.tools.r8.D8",
        "--min-api", "21", "--lib", ANDROID, "--output", dex, *classes.rglob("*.class"))
    wrapper = temp / "helper.apk"
    with zipfile.ZipFile(base) as src, zipfile.ZipFile(wrapper, "w") as dst:
      dst.writestr("AndroidManifest.xml", src.read("AndroidManifest.xml"))
      dst.writestr("classes.dex", (dex / "classes.dex").read_bytes())
    decoded = temp / "helper"
    run(JAVA, "-jar", APKTOOL, "d", "-f", "-r", wrapper, "-o", decoded)
    for source in (decoded / "smali").rglob("*.smali"):
      assert source.name.startswith("AmbientGattSession"), source
      target = output / "smali_classes2" / source.relative_to(decoded / "smali")
      assert not target.exists()
      shutil.copyfile(source, target)
  count = 0
  for source in original.rglob("*"):
    relative = source.relative_to(original)
    if not source.is_file() or {"build", "dist"}.intersection(relative.parts) or str(relative) in patch.NAMES: continue
    assert source.read_bytes() == (output / relative).read_bytes(), relative
    count += 1
  print("Unrelated files unchanged:", count)
  run(JAVA, "-jar", APKTOOL, "b", output, "-o", apk)
  print("Built", apk, hashlib.sha256(apk.read_bytes()).hexdigest())


if __name__ == "__main__": main(*map(Path, sys.argv[1:5]))
