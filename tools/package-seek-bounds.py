#!/usr/bin/env python3
"""Verify and package the 1.4.2 portrait seek-bounds test build."""
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
V = R / 'verification/seek-bounds'
B = O / 'android-sdk/build-tools/36.0.0'
APK = R / 'app/build/outputs/apk/compactTest/app-compactTest.apk'
PREVIOUS = O / 'SparkTube-1.4.1-gestures-download-test.apk'
BASE_SOURCE = O / 'SparkTube-1.4.1-gestures-download-source.zip'
DEST = O / 'SparkTube-1.4.2-seek-bounds-test.apk'
SRC = O / 'SparkTube-1.4.2-seek-bounds-source.zip'
MANIFEST = O / 'SHA256SUMS-SparkTube-1.4.2-seek-bounds.txt'


def command(args, filename):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, check=True)
    text = result.stdout + result.stderr
    (V / filename).write_text(text)
    return text


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source(rel):
    return (R / rel).read_text()


assert 'BUILD SUCCESSFUL' in (V / 'build.log').read_text()
activity = source('app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt')
math = source('app/src/main/java/com/sparktube/app/ui/player/PlayerGestureMath.kt')
bar = source('app/src/main/java/com/sparktube/app/ui/player/DeliberateSeekTimeBar.kt')
gate = source('app/src/main/java/com/sparktube/app/ui/player/SeekBarDragGate.kt')
geometry = source('app/src/main/java/com/sparktube/app/ui/player/SeekBarTouchGeometry.kt')
menu = source('app/src/main/java/com/sparktube/app/ui/common/VideoAdapter.kt')
download = source('app/src/main/java/com/sparktube/app/ui/common/VideoDownloadAction.kt')
layout = source('app/src/main/res/layout/player_queue_controller.xml')
# Static routing checks complement JVM tests; they are not Android runtime tests.
assert 'startedInLandscape == isLandscape' in math
assert 'if (!canSeekFromVideoSurface()) return true' in activity
assert 'PlayerGestureMath.seekTarget(PlaybackCenter.positionMs' in activity
assert 'PlayerGestureMath.horizontalSeekTarget(' in activity
assert 'pendingSeekTarget?.let(PlaybackCenter::seekTo)' in activity
assert 'portraitGestureRejected' in activity and 'event.pointerCount > 1' in activity
assert 'gestureTracking = inside && !hitsPlayerControl(' in activity
assert 'view is androidx.media3.ui.DefaultTimeBar' in activity
assert 'return super.dispatchTouchEvent(event)' in activity
assert 'DeliberateSeekTimeBar android:id="@id/exo_progress"' in layout
assert 'exo_progress_placeholder' not in layout
assert 'ExoStyledControls_TimeBar' in bar
assert 'if (!portraitSequence) return super.onTouchEvent(event)' in bar
assert 'if (gate.move(event.x, event.y, dragSlop))' in bar
assert bar.index('if (gate.move(') < bar.index('nativeDragging = super.onTouchEvent(down)')
assert 'if (nativeDragging) super.onTouchEvent(event)' in bar
assert 'MotionEvent.ACTION_POINTER_DOWN, MotionEvent.ACTION_POINTER_UP' in bar
assert 'override fun onConfigurationChanged' in bar
assert 'override fun onDetachedFromWindow' in bar
assert 'State.DRAGGING else State.REJECTED' in gate
assert 'SeekBarTouchGeometry' in bar and 'SeekBarTouchGeometry' in geometry
# Preserve existing card-menu and download/library behavior.
assert 'menu.add(0, 5, 1, R.string.action_download)' in menu
for action in ['1 -> onClick(item)', '2 -> {', '3 -> context.startActivity', '4 -> onLongClick?.invoke(item)', 'VideoDownloadAction.start(context, item)']:
    assert action in menu
for route in ['DownloadCenter.isDownloaded', 'DownloadCenter.hasActiveDownload', 'MainActivity.openDownloads', 'DownloadSheet(activity, entry, catalog).show()', 'activity.lifecycleScope.launch', 'catch (cancelled: CancellationException)']:
    assert route in download
assert 'PlaybackCenter' not in download

# Ensure every pre-existing app source file/build setting still matches the
# gestures-download baseline, except the explicitly permitted seek/version files.
allowed_existing = {
    'app/build.gradle.kts',
    'app/src/main/java/com/sparktube/app/ui/player/DeliberateSeekTimeBar.kt',
    'app/src/main/java/com/sparktube/app/ui/player/SeekBarDragGate.kt',
    'app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt',
    'app/src/test/java/com/sparktube/app/ui/player/SeekBarDragGateTest.kt',
}
allowed_new = {
    'app/src/main/java/com/sparktube/app/ui/player/SeekBarTouchGeometry.kt',
    'app/src/test/java/com/sparktube/app/ui/player/SeekBarTouchGeometryTest.kt',
}
changed, newly_added = [], []
with zipfile.ZipFile(BASE_SOURCE) as old:
    previous = {name.removeprefix('SparkTube-main/'): old.read(name)
                for name in old.namelist() if name.startswith('SparkTube-main/')}
    for rel, data in previous.items():
        if rel.startswith('app/src/') or rel in ['app/build.gradle.kts', 'build.gradle.kts', 'gradle.properties']:
            assert (R / rel).is_file(), rel
            if (R / rel).read_bytes() != data:
                changed.append(rel)
    old_names = set(previous)
    for path in R.rglob('*'):
        if not path.is_file():
            continue
        rel = path.relative_to(R).as_posix()
        if rel.startswith('app/src/') and rel not in old_names:
            newly_added.append(rel)
assert set(changed) <= allowed_existing, sorted(changed)
assert set(newly_added) <= allowed_new, sorted(newly_added)
assert 'app/src/main/java/com/sparktube/app/ui/player/SeekBarTouchGeometry.kt' in newly_added
assert 'app/src/test/java/com/sparktube/app/ui/player/SeekBarTouchGeometryTest.kt' in newly_added

badging = command([B / 'aapt', 'dump', 'badging', APK], 'apk-badging.txt').splitlines()[0]
for value in ["name='com.sparktube.app'", "versionCode='11'", "versionName='1.4.2'"]:
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
assert counts['tests'] > 110 and not any(counts[k] for k in ['failures', 'errors', 'skipped'])
with zipfile.ZipFile(APK) as z:
    dex = b''.join(z.read(n) for n in z.namelist() if re.fullmatch(r'classes\d*\.dex', n))
    for name in [b'DeliberateSeekTimeBar', b'SeekBarDragGate', b'SeekBarTouchGeometry', b'VideoDownloadAction']:
        assert name in dex
summary = {
    'versionName': '1.4.2', 'versionCode': 11,
    'certificate_matches_previous_gestures_download_apk': True,
    'certificate_sha256': certs[0],
    'jvm_tests': counts,
    'source_routing_checks': 'passed (static checks, not device input tests)',
    'changed_existing_app_files': sorted(changed),
    'new_app_source_files': sorted(newly_added),
    'portrait_seekbar_bounds': 'validated by SeekBarTouchGeometry source and JVM tests',
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
        if rel.parts[0] == 'verification' and 'seek-bounds' not in rel.parts:
            continue
        if path.name in {'local.properties', 'compile.log', '.env'} or '.before.' in path.name or path.suffix in {'.jks', '.keystore', '.apk', '.pem', '.key'}:
            continue
        z.write(path, 'SparkTube-main/' + str(rel))
with zipfile.ZipFile(SRC) as z:
    assert z.testzip() is None
    for path in R.rglob('*'):
        rel = path.relative_to(R)
        if path.is_file() and (str(rel).startswith('app/src/') or str(rel) in ['gradlew', 'gradle/wrapper/gradle-wrapper.jar', 'app/build.gradle.kts']):
            assert z.read('SparkTube-main/' + str(rel)) == path.read_bytes()
assert digest(DEST) == digest(APK)
MANIFEST.write_text(''.join(f'{digest(p)}  {p.name}\n' for p in [DEST, SRC]))
print(json.dumps(summary, indent=2))
for path in [DEST, SRC, MANIFEST]:
    assert path.is_file() and path.stat().st_size > 0
    print(f'{path} ({path.stat().st_size} bytes)')
