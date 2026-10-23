#!/usr/bin/env python3
"""Verify and package the portrait seek-only-on-timebar test build."""
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
V = R / 'verification/portrait-seek'
B = O / 'android-sdk/build-tools/36.0.0'
APK = R / 'app/build/outputs/apk/compactTest/app-compactTest.apk'
PREVIOUS = O / 'SparkTube-1.4.1-video-overflow-test.apk'
DEST = O / 'SparkTube-1.4.1-portrait-seek-test.apk'
SRC = O / 'SparkTube-1.4.1-portrait-seek-source.zip'
MANIFEST = O / 'SHA256SUMS-SparkTube-1.4.1-portrait-seek.txt'


def command(args, filename):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, check=True)
    text = result.stdout + result.stderr
    (V / filename).write_text(text)
    return text


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert 'BUILD SUCCESSFUL' in (V / 'build.log').read_text()
activity = (R / 'app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt').read_text()
# All video-surface seek paths are gated. Native timebar routing stays untouched.
double_tap = activity.split('override fun onDoubleTap', 1)[1].split('override fun onScroll', 1)[0]
assert double_tap.index('if (!canSeekFromVideoSurface()) return true') < double_tap.index('PlaybackCenter.seekTo')
horizontal = activity.split('if (gestureAxis == PlayerGestureMath.Axis.HORIZONTAL)', 1)[1].split('val width =', 1)[0]
assert horizontal.index('if (!canSeekFromVideoSurface()) return true') < horizontal.index('pendingSeekTarget =')
assert 'event.actionMasked == MotionEvent.ACTION_UP && canSeekFromVideoSurface()' in activity
assert 'gestureStartedInLandscape = resources.configuration.orientation == Configuration.ORIENTATION_LANDSCAPE' in activity
assert 'gestureTracking = inside && !hitsPlayerControl(binding.root, event.rawX.toInt(), event.rawY.toInt())' in activity
assert 'view is androidx.media3.ui.DefaultTimeBar' in activity
assert 'return super.dispatchTouchEvent(event)' in activity
assert 'if (event.actionMasked == MotionEvent.ACTION_DOWN)' in activity
assert 'pendingSeekTarget = null\n                gestureTracking = false' in activity

# App production changes are restricted to two Kotlin files. All layouts,
# dependencies, signing configuration and unrelated features match the baseline.
changed = []
with zipfile.ZipFile(O / 'SparkTube-1.4.1-video-overflow-source.zip') as old:
    for name in old.namelist():
        rel = name.removeprefix('SparkTube-main/')
        if rel.startswith('app/src/') or rel in ['app/build.gradle.kts', 'build.gradle.kts', 'gradle.properties']:
            assert (R / rel).is_file(), rel
            if (R / rel).read_bytes() != old.read(name):
                changed.append(rel)
assert set(changed) == {
    'app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt',
    'app/src/main/java/com/sparktube/app/ui/player/PlayerGestureMath.kt',
}, changed
badging = command([B / 'aapt', 'dump', 'badging', APK], 'apk-badging.txt').splitlines()[0]
for value in ["name='com.sparktube.app'", "versionCode='10'", "versionName='1.4.1'"]:
    assert value in badging
certs = []
for path, filename in [(PREVIOUS, 'signature-before.txt'), (APK, 'signature-after.txt')]:
    output = command([B / 'apksigner', 'verify', '--verbose', '--print-certs', path], filename)
    certs.append(re.search(r'certificate SHA-256 digest: (\w+)', output).group(1))
assert certs[0] == certs[1]
assert 'Verification successful' in command([B / 'zipalign', '-c', '-v', '4', APK], 'zipalign.txt')
counts = dict(tests=0, failures=0, errors=0, skipped=0)
for path in (R / 'app/build/test-results/testCompactTestUnitTest').glob('TEST-*.xml'):
    result = ET.parse(path).getroot()
    for key in counts:
        counts[key] += int(result.get(key, '0'))
    shutil.copy2(path, V / path.name)
policy_tests = ET.parse(V / 'TEST-com.sparktube.app.ui.player.PortraitSeekPolicyTest.xml').getroot()
assert int(policy_tests.get('tests')) == 4
assert counts['tests'] >= 94 and not any(counts[k] for k in ['failures', 'errors', 'skipped'])
summary = {
    'versionName': '1.4.1', 'versionCode': 10,
    'certificate_matches_video_overflow_apk': True,
    'certificate_sha256': certs[0],
    'jvm_tests': counts,
    'source_touch_routing_checks': 'passed (static checks, not device input tests)',
    'changed_existing_app_files': changed,
    'added_app_test_file': 'app/src/test/java/com/sparktube/app/ui/player/PortraitSeekPolicyTest.kt',
    'native_timebar_and_layouts_unchanged': True,
    'android_device_or_emulator_tested': False,
    'lint_completed': False,
    'apk_bytes': APK.stat().st_size, 'apk_sha256': digest(APK),
}
(V / 'verification-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
shutil.copy2(APK, DEST)
excluded = {'.git', '.gradle', '.kotlin', 'build', '__pycache__'}
with zipfile.ZipFile(SRC, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for path in sorted(R.rglob('*')):
        rel = path.relative_to(R)
        if not path.is_file() or any(x in excluded for x in rel.parts):
            continue
        if rel.parts[0] == 'verification' and 'portrait-seek' not in rel.parts:
            continue
        if path.name in {'local.properties', 'compile.log', '.env'} or '.before.' in path.name or path.suffix in {'.jks', '.keystore', '.apk', '.pem', '.key'}:
            continue
        z.write(path, 'SparkTube-main/' + str(rel))
with zipfile.ZipFile(SRC) as z:
    assert z.testzip() is None
    for rel in [
        'gradlew', 'gradle/wrapper/gradle-wrapper.jar', 'app/build.gradle.kts',
        'app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt',
        'app/src/main/java/com/sparktube/app/ui/player/PlayerGestureMath.kt',
        'app/src/test/java/com/sparktube/app/ui/player/PortraitSeekPolicyTest.kt',
    ]:
        assert z.read('SparkTube-main/' + rel) == (R / rel).read_bytes()
assert digest(DEST) == digest(APK)
MANIFEST.write_text(''.join(f'{digest(p)}  {p.name}\n' for p in [DEST, SRC]))
print(json.dumps(summary, indent=2))
for path in [DEST, SRC, MANIFEST]:
    assert path.is_file() and path.stat().st_size > 0
    print(f'{path} ({path.stat().st_size} bytes)')
