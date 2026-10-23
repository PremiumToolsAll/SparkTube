#!/usr/bin/env python3
"""Package and verify the clean player overlay test build."""
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
V = R/'verification/clean-player-overlay'
B = O/'android-sdk/build-tools/36.0.0'
APK = R/'app/build/outputs/apk/compactTest/app-compactTest.apk'
PREVIOUS = O/'SparkTube-1.4.1-audio-timer-position-test.apk'
DEST = O/'SparkTube-1.4.1-clean-player-overlay-test.apk'
SRC = O/'SparkTube-1.4.1-clean-player-overlay-source.zip'
SUM = O/'SHA256SUMS-SparkTube-1.4.1-clean-player-overlay.txt'

def command(args, filename):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, check=True)
    output = result.stdout + result.stderr
    (V/filename).write_text(output)
    return output

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

assert 'BUILD SUCCESSFUL' in (V/'build.log').read_text()
for name in ['source-checks.log', 'timer-checks.log']:
    assert '\nOK\n' in (V/name).read_text()
badging = command([B/'aapt', 'dump', 'badging', APK], 'apk-badging.txt').splitlines()[0]
for value in ["name='com.sparktube.app'", "versionCode='10'", "versionName='1.4.1'"]:
    assert value in badging
certificates = []
for path, name in [(PREVIOUS, 'signature-before.txt'), (APK, 'signature-after.txt')]:
    output = command([B/'apksigner', 'verify', '--verbose', '--print-certs', path], name)
    certificates.append(re.search(r'certificate SHA-256 digest: (\w+)', output).group(1))
assert certificates[0] == certificates[1]
assert 'Verification successful' in command([B/'zipalign', '-c', '-v', '4', APK], 'zipalign.txt')
counts = dict(tests=0, failures=0, errors=0, skipped=0)
for p in sorted((R/'app/build/test-results/testCompactTestUnitTest').glob('TEST-*.xml')):
    root = ET.parse(p).getroot()
    for key in counts:
        counts[key] += int(root.get(key, '0'))
    shutil.copy2(p, V/p.name)
assert counts['tests'] >= 77 and not any(counts[k] for k in ['failures', 'errors', 'skipped'])
assert APK.stat().st_size < 11_000_000
summary = {
    'versionName': '1.4.1', 'versionCode': 10,
    'certificate_matches_previous_audio_timer_position_apk': True,
    'certificate_sha256': certificates[1],
    'jvm_tests': counts, 'source_regression_checks': 7,
    'modified_existing_app_files': [
        'app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt',
        'app/src/main/res/layout/activity_player.xml'],
    'collapse_visibility_matches_playback_controls': True,
    'collapse_icon_background_transparent': True,
    'portrait_bottom_bar_background_transparent': True,
    'landscape_original_media3_background_restored_on_rotation': True,
    'controller_layout_and_seek_behavior_unchanged': True,
    'timer_and_playback_code_unchanged': True,
    'android_device_or_emulator_tested': False,
    'lint_completed': False,
    'lint_limit': 'Offline lint-gradle:31.6.1 dependency unavailable; lint vital tasks excluded. No lint pass claimed.',
    'apk_bytes': APK.stat().st_size,
    'previous_apk_bytes': PREVIOUS.stat().st_size,
    'apk_size_delta_bytes': APK.stat().st_size - PREVIOUS.stat().st_size,
    'apk_sha256': digest(APK),
}
(V/'verification-summary.json').write_text(json.dumps(summary, indent=2)+'\n')
shutil.copy2(APK, DEST)
excluded = {'.git', '.gradle', '.kotlin', 'build', '__pycache__'}
with zipfile.ZipFile(SRC, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p in sorted(R.rglob('*')):
        rel = p.relative_to(R)
        if not p.is_file() or any(x in excluded for x in rel.parts):
            continue
        if rel.parts[0] == 'verification' and 'clean-player-overlay' not in rel.parts:
            continue
        if p.name in {'local.properties', 'compile.log', '.env'} or '.before.' in p.name or p.suffix in {'.jks', '.keystore', '.apk', '.pem', '.key'}:
            continue
        z.write(p, 'SparkTube-main/'+str(rel))
with zipfile.ZipFile(SRC) as z:
    assert z.testzip() is None
    for p in (R/'app/src').rglob('*'):
        if p.is_file():
            assert z.read('SparkTube-main/'+str(p.relative_to(R))) == p.read_bytes()
    for rel in ['gradlew', 'gradle/wrapper/gradle-wrapper.jar', 'app/build.gradle.kts']:
        assert z.read('SparkTube-main/'+rel) == (R/rel).read_bytes()
assert digest(DEST) == digest(APK)
SUM.write_text(''.join(f'{digest(p)}  {p.name}\n' for p in [DEST, SRC]))
for p in [DEST, SRC, SUM]:
    assert p.is_file() and p.stat().st_size > 0
    print(f'{p}: {p.stat().st_size} bytes')
print(json.dumps(summary, indent=2))
