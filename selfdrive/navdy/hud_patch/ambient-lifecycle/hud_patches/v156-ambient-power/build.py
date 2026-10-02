"""Build only the power and ambient delta over the verified v155r2 payload."""
import hashlib
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
import apply

TOOLS = Path.home() / '.cache/navdy-build-tools'
JAVA = next(TOOLS.glob('jdk-*/Contents/Home/bin/java'))
ANDROID = TOOLS / 'android-35/android.jar'
APKTOOL = TOOLS / 'apktool_3.0.3.jar'
BASE_HASH = '9f241b73188d6d98419609aed45c5ea4b16b9cba35f0bc2cd65f566a77d29df1'


def run(*args):
  subprocess.run(list(map(str, args)), check=True)


def main(base, original, output, apk):
  assert hashlib.sha256(base.read_bytes()).hexdigest() == BASE_HASH
  assert not output.exists(), 'use a fresh output directory'
  before = {name: (original / name).read_text() for name in apply.NAMES}
  after = apply.transform(before)
  shutil.copytree(original, output, ignore=shutil.ignore_patterns('build', 'dist'))
  for name, content in after.items():
    (output / name).write_text(content)
  helpers = apply.helper_sources()
  helper_prefixes = tuple(Path(name).stem for name in helpers)
  with tempfile.TemporaryDirectory(prefix='ambient-power-') as directory:
    temp = Path(directory)
    classes, dex = temp / 'classes', temp / 'dex'
    classes.mkdir()
    dex.mkdir()
    for name, content in helpers.items():
      (temp / name).write_text(content)
    run(JAVA.with_name('javac'), '-source', '8', '-target', '8', '-cp', ANDROID,
        '-d', classes, *temp.glob('*.java'))
    run(JAVA, '-cp', TOOLS / 'android-16/lib/d8.jar', 'com.android.tools.r8.D8',
        '--min-api', '21', '--lib', ANDROID, '--output', dex, *classes.rglob('*.class'))
    wrapper = temp / 'helper.apk'
    with zipfile.ZipFile(base) as src, zipfile.ZipFile(wrapper, 'w') as dst:
      dst.writestr('AndroidManifest.xml', src.read('AndroidManifest.xml'))
      dst.writestr('classes.dex', (dex / 'classes.dex').read_bytes())
    decoded = temp / 'helper'
    run(JAVA, '-jar', APKTOOL, 'd', '-f', '-r', wrapper, '-o', decoded)
    for source in (decoded / 'smali').rglob('*.smali'):
      assert source.name.startswith(helper_prefixes), source
      shutil.copyfile(source, output / 'smali_classes2' / source.relative_to(decoded / 'smali'))
  count = 0
  for source in original.rglob('*'):
    relative = source.relative_to(original)
    if not source.is_file() or {'build', 'dist'}.intersection(relative.parts) or str(relative) in apply.NAMES or source.name.startswith(helper_prefixes):
      continue
    assert source.read_bytes() == (output / relative).read_bytes(), relative
    count += 1
  print('Unrelated files unchanged:', count, flush=True)
  run(JAVA, '-jar', APKTOOL, 'b', output, '-o', apk)
  print('Built SHA256', hashlib.sha256(apk.read_bytes()).hexdigest())


if __name__ == '__main__':
  main(*map(Path, sys.argv[1:5]))
