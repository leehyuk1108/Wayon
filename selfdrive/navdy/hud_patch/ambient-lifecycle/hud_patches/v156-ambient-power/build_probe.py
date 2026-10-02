"""Build a standalone probe and verify that only the two DEX payloads changed."""
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = Path.home() / '.cache/navdy-build-tools'
JAVA = next(TOOLS.glob('jdk-*/Contents/Home/bin/java'))
ANDROID = TOOLS / 'android-35/android.jar'


def run(*args):
  subprocess.run(list(map(str, args)), check=True)


if __name__ == '__main__':
  output, original, patched = map(Path, sys.argv[1:4])
  output.mkdir(parents=True, exist_ok=True)
  with tempfile.TemporaryDirectory() as directory:
    temp = Path(directory)
    classes = temp / 'classes'
    classes.mkdir()
    source = (HERE.parent / 'v155-ambient-off-priority/ControllerProbe.java').read_text()
    assert source.count('    System.exit(0);') == 1
    (temp / 'ControllerProbe.java').write_text(source.replace('    System.exit(0);', ''))
    run(JAVA.with_name('javac'), '-source', '8', '-target', '8', '-cp', ANDROID,
        '-d', classes, temp / 'ControllerProbe.java', HERE / 'PowerProbe.java')
    run(JAVA, '-cp', TOOLS / 'android-16/lib/d8.jar', 'com.android.tools.r8.D8',
        '--min-api', '21', '--lib', ANDROID, '--output', output / 'probe.jar', *classes.rglob('*.class'))
  with zipfile.ZipFile(original) as old, zipfile.ZipFile(patched) as new:
    old_names = {n for n in old.namelist() if not n.startswith('META-INF/') and not n.endswith('/')}
    new_names = {n for n in new.namelist() if not n.startswith('META-INF/') and not n.endswith('/')}
    assert old_names == new_names, (old_names - new_names, new_names - old_names)
    changed = {n for n in old_names if old.read(n) != new.read(n)}
    assert changed == {'classes.dex', 'classes2.dex'}, changed
    for name in sorted(changed):
      (output / name).write_bytes(new.read(name))
    print('Only changed APK payloads:', sorted(changed))
