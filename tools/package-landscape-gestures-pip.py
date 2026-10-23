#!/usr/bin/env python3
"""Verify and package the matching APK/source. No Android runtime test is claimed."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

R = Path(__file__).resolve().parents[1]
O = R.parent
V = R/'verification/landscape-gestures-pip'
B = O/'android-sdk/build-tools/36.0.0'
APK = R/'app/build/outputs/apk/compactTest/app-compactTest.apk'
PREVIOUS = O/'SparkTube-1.4.1-landscape-brightness-pip-test.apk'
DEST = O/'SparkTube-1.4.1-landscape-gestures-pip-test.apk'
SRC = O/'SparkTube-1.4.1-landscape-gestures-pip-source.zip'
SUM = O/'SHA256SUMS-SparkTube-1.4.1-landscape-gestures-pip.txt'

def command(args, filename):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, check=True)
    output = result.stdout + result.stderr
    (V/filename).write_text(output)
    return output

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert 'BUILD SUCCESSFUL' in (V/'build.log').read_text()
assert '\nOK\n' in (V/'source-checks.log').read_text()
badging = command([B/'aapt', 'dump', 'badging', APK], 'apk-badging.txt').splitlines()[0]
for value in ["name='com.sparktube.app'", "versionCode='10'", "versionName='1.4.1'"]:
    assert value in badging
certs = []
for path, filename in [(PREVIOUS, 'signature-before.txt'), (APK, 'signature-after.txt')]:
    result = command([B/'apksigner', 'verify', '--verbose', '--print-certs', path], filename)
    certs.append(re.search(r'certificate SHA-256 digest: (\w+)', result).group(1))
assert certs[0] == certs[1]
assert 'Verification successful' in command([B/'zipalign', '-c', '-v', '4', APK], 'zipalign.txt')
counts = dict(tests=0, failures=0, errors=0, skipped=0)
for path in sorted((R/'app/build/test-results/testCompactTestUnitTest').glob('TEST-*.xml')):
    root = ET.parse(path).getroot()
    for key in counts:
        counts[key] += int(root.get(key, '0'))
    shutil.copy2(path, V/path.name)
assert counts['tests'] >= 83 and not any(counts[k] for k in ['failures', 'errors', 'skipped'])
summary = {
    'versionName': '1.4.1', 'versionCode': 10,
    'certificate_matches_previous_apk': True, 'certificate_sha256': certs[1],
    'jvm_tests': counts, 'source_regression_checks': 8,
    'brightness_gesture_landscape_only': True,
    'volume_gesture_landscape_only': True,
    'app_source_changed_only_player_activity': True,
    'portrait_restores_system_brightness': True,
    'explicit_replacement_closes_previous_pip_activity': True,
    'stale_pip_callbacks_identity_guarded': True,
    'automatic_queue_advance_keeps_pip': True,
    'android_device_or_emulator_tested': False,
    'lint_completed': False,
    'lint_note': 'Lint vital tasks excluded: baseline offline lint dependency unavailable. No lint pass claimed.',
    'apk_bytes': APK.stat().st_size, 'apk_sha256': digest(APK)
}
(V/'verification-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
shutil.copy2(APK, DEST)
excluded = {'.git', '.gradle', '.kotlin', 'build', '__pycache__'}
with zipfile.ZipFile(SRC, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for path in sorted(R.rglob('*')):
        rel = path.relative_to(R)
        if not path.is_file() or any(x in excluded for x in rel.parts):
            continue
        if rel.parts[0] == 'verification' and 'landscape-gestures-pip' not in rel.parts:
            continue
        if path.name in {'local.properties', 'compile.log', '.env'} or '.before.' in path.name or path.suffix in {'.jks', '.keystore', '.apk', '.pem', '.key'}:
            continue
        z.write(path, 'SparkTube-main/'+str(rel))
with zipfile.ZipFile(SRC) as z:
    assert z.testzip() is None
    for path in (R/'app/src').rglob('*'):
        if path.is_file():
            assert z.read('SparkTube-main/'+str(path.relative_to(R))) == path.read_bytes()
    for rel in ['gradlew', 'gradle/wrapper/gradle-wrapper.jar', 'app/build.gradle.kts']:
        assert z.read('SparkTube-main/'+rel) == (R/rel).read_bytes()
assert digest(DEST) == digest(APK)
assert APK.stat().st_size <= PREVIOUS.stat().st_size + 32768, 'Unexpected compact APK size increase'
SUM.write_text(''.join(f'{digest(path)}  {path.name}\n' for path in [DEST, SRC]))
for path in [DEST, SRC, SUM]:
    assert path.is_file() and path.stat().st_size > 0
    print(f'{path}: {path.stat().st_size} bytes')
print(json.dumps(summary, indent=2))
