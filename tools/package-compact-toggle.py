#!/usr/bin/env python3
"""Verify and package the compact-toggle resource-only update; no runtime test claimed."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent
VERIFY = ROOT / 'verification/compact-toggle'
BIN = OUT / 'android-sdk/build-tools/36.0.0'
APK = ROOT / 'app/build/outputs/apk/compactTest/app-compactTest.apk'
OLD = OUT / 'SparkTube-1.4.1-render-controls-test.apk'
DEST = OUT / 'SparkTube-1.4.1-compact-toggle-test.apk'
SOURCE = OUT / 'SparkTube-1.4.1-compact-toggle-source.zip'
MANIFEST = OUT / 'SHA256SUMS-SparkTube-1.4.1-compact-toggle.txt'
CHANGED = {
    'app/src/main/res/layout/activity_player.xml',
    'app/src/main/res/layout/activity_now_playing.xml',
    'app/src/main/res/drawable/bg_mode_switch_active.xml',
    'app/src/main/res/drawable/bg_mode_switch_hit_area.xml',
    'tools/verify-player-correction.py',
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(program, *args):
    return subprocess.check_output([str(program), *map(str, args)], text=True, stderr=subprocess.STDOUT)

def record(name, text):
    (VERIFY / name).write_text(text)
    return text

baseline = json.loads((VERIFY / 'baseline-source.json').read_text())
changed = {name for name, digest in baseline.items() if sha(ROOT / name) != digest}
assert changed == CHANGED, changed
# Compare actual Kotlin/Java source, dependencies and settings against the delivered previous source.
with zipfile.ZipFile(OUT / 'SparkTube-1.4.1-render-controls-source.zip') as previous:
    for name in baseline:
        if name.startswith('app/src/') or name.startswith('app/libs/') or name.endswith('.gradle.kts'):
            if name not in CHANGED:
                assert (ROOT / name).read_bytes() == previous.read('SparkTube-main/' + name), name
record('structural-tests.log', run('python3', ROOT / 'tools/verify-player-correction.py'))
badging = record('apk-badging.txt', run(BIN / 'aapt2', 'dump', 'badging', APK))
assert "versionCode='10'" in badging.splitlines()[0]
assert "versionName='1.4.1'" in badging.splitlines()[0]
new_sig = record('signature-after.txt', run(BIN / 'apksigner', 'verify', '--print-certs', APK))
old_sig = record('signature-before.txt', run(BIN / 'apksigner', 'verify', '--print-certs', OLD))
cert = re.search(r'certificate SHA-256 digest: (\w+)', new_sig).group(1)
assert cert == re.search(r'certificate SHA-256 digest: (\w+)', old_sig).group(1)
record('zipalign.txt', run(BIN / 'zipalign', '-c', '-v', '4', APK))
resources = record('resources.txt', run(BIN / 'aapt2', 'dump', 'resources', APK))
# Resource-only: every compiled dex file must remain byte-identical.
with zipfile.ZipFile(OLD) as old, zipfile.ZipFile(APK) as new:
    dex = [name for name in old.namelist() if re.fullmatch(r'classes\d*\.dex', name)]
    assert dex == [name for name in new.namelist() if re.fullmatch(r'classes\d*\.dex', name)]
    for name in dex:
        assert new.read(name) == old.read(name), name
    for layout in ['activity_player', 'activity_now_playing']:
        path = re.search(r'layout/' + re.escape(layout) + r'\n\s+\(\) \(file\) (\S+)', resources).group(1)
        compiled = record(f'compiled-{layout}.txt', run(BIN / 'aapt2', 'dump', 'xmltree', APK, '--file', path))
        assert '76.000000dp' in compiled
        assert '48.000000dp' in compiled
        assert '30.000000dp' in compiled
        assert '24.000000dp' in compiled
        assert '17.000000dp' in compiled
counts = dict(tests=0, failures=0, errors=0, skipped=0)
for path in (ROOT / 'app/build/test-results/testCompactTestUnitTest').glob('TEST-*.xml'):
    elem = ET.parse(path).getroot()
    for key in counts:
        counts[key] += int(elem.get(key, '0'))
    shutil.copy2(path, VERIFY / path.name)
assert counts['tests'] == 38 and counts['failures'] == counts['errors'] == counts['skipped'] == 0
record('adb-devices.txt', run(OUT / 'android-sdk/platform-tools/adb', 'devices'))
shutil.copy2(APK, DEST)
summary = {
    'versionName': '1.4.1', 'versionCode': 10,
    'apk_bytes': DEST.stat().st_size, 'previous_apk_bytes': OLD.stat().st_size,
    'size_delta_bytes': DEST.stat().st_size - OLD.stat().st_size,
    'same_signing_certificate': True, 'certificate_sha256': cert,
    'compiled_dex_byte_identical': True, 'jvm_tests': counts,
    'structural_tests': 10, 'changed_existing_files': sorted(changed),
    'tap_target_dp': [76, 48], 'visual_capsule_dp': [64, 28],
    'previous_visual_capsule_dp': [80, 32], 'icon_dp': 17,
    'android_runtime_or_emulator_tested': False,
    'lint_run_for_this_update': False,
}
record('verification-summary.json', json.dumps(summary, indent=2) + '\n')
excluded = {'.git', '.gradle', '.kotlin', 'build', '__pycache__'}
with zipfile.ZipFile(SOURCE, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT)
        if not path.is_file() or any(part in excluded for part in rel.parts):
            continue
        if path.name == 'local.properties' or path.suffix in {'.jks', '.keystore', '.apk'}:
            continue
        archive.write(path, 'SparkTube-main/' + str(rel))
with zipfile.ZipFile(SOURCE) as archive:
    assert archive.testzip() is None
    for name in baseline:
        if name == 'local.properties':
            continue
        assert archive.read('SparkTube-main/' + name) == (ROOT / name).read_bytes(), name
MANIFEST.write_text(''.join(f'{sha(path)}  {path.name}\n' for path in [DEST, SOURCE]))
for path in [DEST, SOURCE, MANIFEST]:
    assert path.is_file() and path.stat().st_size > 0
    print(f'{path}: {path.stat().st_size} bytes')
print(json.dumps(summary, indent=2))
