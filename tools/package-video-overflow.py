#!/usr/bin/env python3
"""Check the video overflow change and package the matching test APK/source."""
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
V = R / 'verification/video-overflow'
B = O / 'android-sdk/build-tools/36.0.0'
APK = R / 'app/build/outputs/apk/compactTest/app-compactTest.apk'
PREVIOUS = O / 'SparkTube-1.4.1-landscape-gestures-pip-test.apk'
DEST = O / 'SparkTube-1.4.1-video-overflow-test.apk'
SRC = O / 'SparkTube-1.4.1-video-overflow-source.zip'


def command(args, filename):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True, check=True)
    text = result.stdout + result.stderr
    (V / filename).write_text(text)
    return text


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


assert 'BUILD SUCCESSFUL' in (V / 'build.log').read_text()
a = '{http://schemas.android.com/apk/res/android}'
c = '{http://schemas.android.com/apk/res-auto}'
root = ET.parse(R / 'app/src/main/res/layout/item_video.xml').getroot()
views = {x.get(a + 'id', '').split('/')[-1]: x for x in root}
button = views['overflowButton']
assert button.get(a + 'layout_width') == button.get(a + 'layout_height') == '48dp'
assert button.get(c + 'layout_constraintTop_toBottomOf') == '@id/thumbWrap'
assert button.get(c + 'layout_constraintEnd_toEndOf') == 'parent'
assert button.get(c + 'tint') == '@color/on_surface'
for name in ['title', 'meta']:
    assert views[name].get(c + 'layout_constraintEnd_toStartOf') == '@id/overflowButton'
adapter = (R / 'app/src/main/java/com/sparktube/app/ui/common/VideoAdapter.kt').read_text()
assert 'b.overflowButton.setOnClickListener' in adapter
assert 'PopupMenu(context, anchor)' in adapter
assert 'b.root.setOnClickListener { onClick(item) }' in adapter
assert 'b.root.setOnLongClickListener' in adapter
assert '4 -> onLongClick?.invoke(item)' in adapter
assert 'Intent.EXTRA_TEXT, item.url' in adapter
assert 'video_more_options, item.title' in adapter
# Preserve all other app source, including the prior gesture/PiP work.
changed = []
with zipfile.ZipFile(O / 'SparkTube-1.4.1-landscape-gestures-pip-source.zip') as old:
    for name in old.namelist():
        rel = name.removeprefix('SparkTube-main/')
        if rel.startswith('app/src/') or rel in ['app/build.gradle.kts', 'build.gradle.kts', 'gradle.properties']:
            if (R / rel).read_bytes() != old.read(name):
                changed.append(rel)
assert set(changed) == {
    'app/src/main/java/com/sparktube/app/ui/common/VideoAdapter.kt',
    'app/src/main/res/layout/item_video.xml',
    'app/src/main/res/values/strings.xml',
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
assert counts['tests'] >= 90 and not any(counts[k] for k in ['failures', 'errors', 'skipped'])
summary = {
    'versionName': '1.4.1', 'versionCode': 10,
    'certificate_matches_previous_apk': True,
    'jvm_tests': counts, 'source_layout_and_callback_checks': 'passed',
    'changed_app_files': changed,
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
        if rel.parts[0] == 'verification' and 'video-overflow' not in rel.parts:
            continue
        if path.name in {'local.properties', 'compile.log', '.env'} or '.before.' in path.name or path.suffix in {'.jks', '.keystore', '.apk', '.pem', '.key'}:
            continue
        z.write(path, 'SparkTube-main/' + str(rel))
with zipfile.ZipFile(SRC) as z:
    assert z.testzip() is None
assert DEST.is_file() and DEST.stat().st_size == APK.stat().st_size
print(json.dumps(summary, indent=2))
print(DEST)
print(SRC)
