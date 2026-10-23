#!/usr/bin/env python3
"""Package matching compact test APK, editable source and SHA-256 manifest."""
from pathlib import Path
import difflib
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent
V = ROOT / 'verification/video-collapse'
APK = ROOT / 'app/build/outputs/apk/compactTest/app-compactTest.apk'
DEST = OUT / 'SparkTube-1.4.1-video-collapse-test.apk'
SOURCE = OUT / 'SparkTube-1.4.1-video-collapse-source.zip'
SUMS = OUT / 'SHA256SUMS-SparkTube-1.4.1-video-collapse.txt'
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert 'BUILD SUCCESSFUL' in (V / 'build.log').read_text()
checks = (V / 'feature-checks.log').read_text()
assert '\nOK\n' in checks
check_count = int(re.search(r'Ran (\d+) tests', checks).group(1))
assert check_count == 61
badging = (V / 'apk-badging.txt').read_text().splitlines()[0]
for part in ["name='com.sparktube.app'", "versionCode='10'", "versionName='1.4.1'"]:
    assert part in badging
certs = [re.search(r'certificate SHA-256 digest: (\w+)', (V / name).read_text()).group(1)
         for name in ['signature-before.txt', 'signature-after.txt']]
assert certs[0] == certs[1]
assert 'Verification successful' in (V / 'zipalign.txt').read_text()
counts = dict(tests=0, failures=0, errors=0, skipped=0)
for path in sorted((ROOT / 'app/build/test-results/testCompactTestUnitTest').glob('TEST-*.xml')):
    elem = ET.parse(path).getroot()
    for key in counts:
        counts[key] += int(elem.get(key, '0'))
    shutil.copy2(path, V / path.name)
assert counts['tests'] == 77
assert counts['failures'] == counts['errors'] == counts['skipped'] == 0
changes = []
with zipfile.ZipFile(OUT / 'SparkTube-1.4.1-notification-audio-source.zip') as old:
    for name in old.namelist():
        rel = name.removeprefix('SparkTube-main/')
        if not rel.startswith('app/src/'):
            continue
        path = ROOT / rel
        assert path.is_file(), rel
        if path.read_bytes() != old.read(name):
            changes.append(rel)
            (V / (path.name + '.diff')).write_text(''.join(difflib.unified_diff(
                old.read(name).decode().splitlines(True), path.read_text().splitlines(True),
                fromfile='before/' + rel, tofile='after/' + rel)))
assert set(changes) == {
    'app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt',
    'app/src/main/res/layout/activity_player.xml',
    'app/src/main/res/values/strings_player_controls.xml',
}
previous = OUT / 'SparkTube-1.4.1-notification-audio-test.apk'
summary = {
    'versionName': '1.4.1', 'versionCode': 10,
    'same_signing_certificate_as_notification_audio_test': True,
    'certificate_sha256': certs[1], 'jvm_tests': counts,
    'source_xml_checks': check_count, 'modified_existing_app_files': changes,
    'android_device_or_emulator_tested': False, 'android_ui_tested': False,
    'lint_completed': False,
    'lint_limit': 'Offline lint dependencies unavailable; lintVital tasks excluded.',
    'apk_sha256': digest(APK), 'apk_bytes': APK.stat().st_size,
    'previous_apk_bytes': previous.stat().st_size,
    'apk_size_delta_bytes': APK.stat().st_size - previous.stat().st_size,
}
(V / 'verification-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
shutil.copy2(ROOT / 'app/build/outputs/apk/compactTest/output-metadata.json', V / 'output-metadata.json')
shutil.copy2(APK, DEST)
excluded = {'.git', '.gradle', '.kotlin', 'build', '__pycache__'}
with zipfile.ZipFile(SOURCE, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT)
        if not path.is_file() or any(part in excluded for part in rel.parts):
            continue
        if rel.parts[0] == 'verification' and 'video-collapse' not in rel.parts:
            continue
        if path.name in {'local.properties', 'compile.log'} or '.before.' in path.name or path.suffix in {'.jks', '.keystore', '.apk'}:
            continue
        archive.write(path, 'SparkTube-main/' + str(rel))
with zipfile.ZipFile(SOURCE) as archive:
    assert archive.testzip() is None
    for path in (ROOT / 'app/src').rglob('*'):
        if path.is_file():
            assert archive.read('SparkTube-main/' + str(path.relative_to(ROOT))) == path.read_bytes()
    assert archive.read('SparkTube-main/VIDEO_COLLAPSE_BN.md') == (ROOT / 'VIDEO_COLLAPSE_BN.md').read_bytes()
assert digest(DEST) == digest(APK)
SUMS.write_text(''.join(f'{digest(path)}  {path.name}\n' for path in [DEST, SOURCE]))
for path in [DEST, SOURCE, SUMS]:
    assert path.is_file() and path.stat().st_size > 0
    print(f'{path}: {path.stat().st_size} bytes')
print(json.dumps(summary, indent=2))
