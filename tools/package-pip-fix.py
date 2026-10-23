#!/usr/bin/env python3
"""Package the PiP fix after build/tests; never claims Android runtime testing."""
from pathlib import Path
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent
VERIFY = ROOT / 'verification/pip-fix'
BIN = OUT / 'android-sdk/build-tools/36.0.0'
APK = ROOT / 'app/build/outputs/apk/compactTest/app-compactTest.apk'
PREVIOUS = OUT / 'SparkTube-1.4.1-audio-downloads-test.apk'
DEST = OUT / 'SparkTube-1.4.1-pip-fixed-test.apk'
SOURCE = OUT / 'SparkTube-1.4.1-pip-fixed-source.zip'
MANIFEST = OUT / 'SHA256SUMS-SparkTube-1.4.1-pip-fixed.txt'
def run(*args):
    return subprocess.check_output(list(map(str, args)), text=True, stderr=subprocess.STDOUT)
def record(name, text):
    (VERIFY / name).write_text(text)
    return text
for script, log in [('verify-pip-fix.py', 'pip-structure-tests.log'), ('verify-player-correction.py', 'player-structure-tests.log')]:
    record(log, run('python3', ROOT / 'tools' / script))
# Historical audio verifier's old byte-diff deliberately excludes later fixes.
# Run its four feature checks; the PiP verifier compares ALL app files to the latest ZIP.
import importlib.util
import unittest
spec = importlib.util.spec_from_file_location('audio_checks', ROOT / 'tools/verify-audio-downloads.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
suite = unittest.TestSuite(module.AudioDownloadStructureTest(name) for name in unittest.defaultTestLoader.getTestCaseNames(module.AudioDownloadStructureTest) if name != 'test_existing_app_changes_are_limited_to_two_classes')
with (VERIFY / 'audio-feature-tests.log').open('w') as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
assert result.wasSuccessful() and result.testsRun == 4
assert 'BUILD SUCCESSFUL' in (VERIFY / 'build.log').read_text()
badging = record('apk-badging.txt', run(BIN / 'aapt2', 'dump', 'badging', APK))
assert "versionCode='10'" in badging.splitlines()[0]
assert "versionName='1.4.1'" in badging.splitlines()[0]
assert "package: name='com.sparktube.app'" in badging.splitlines()[0]
new_sig = record('signature-after.txt', run(BIN / 'apksigner', 'verify', '--print-certs', APK))
old_sig = record('signature-before.txt', run(BIN / 'apksigner', 'verify', '--print-certs', PREVIOUS))
cert = re.search(r'certificate SHA-256 digest: (\w+)', new_sig).group(1)
assert cert == re.search(r'certificate SHA-256 digest: (\w+)', old_sig).group(1)
record('zipalign.txt', run(BIN / 'zipalign', '-c', '-v', '4', APK))
counts = dict(tests=0, failures=0, errors=0, skipped=0)
for path in sorted((ROOT / 'app/build/test-results/testCompactTestUnitTest').glob('TEST-*.xml')):
    elem = ET.parse(path).getroot()
    for key in counts:
        counts[key] += int(elem.get(key, '0'))
    shutil.copy2(path, VERIFY / path.name)
assert counts == dict(tests=46, failures=0, errors=0, skipped=0), counts
record('adb-devices.txt', run(OUT / 'android-sdk/platform-tools/adb', 'devices'))
with zipfile.ZipFile(OUT / 'SparkTube-1.4.1-audio-downloads-source.zip') as previous:
    relative = 'app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt'
    old = previous.read('SparkTube-main/' + relative).decode()
    new = (ROOT / relative).read_text()
    record('player-activity.diff', ''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile='before/'+relative, tofile='after/'+relative)))
shutil.copy2(APK, DEST)
summary = {
    'versionName': '1.4.1', 'versionCode': 10,
    'apk_bytes': DEST.stat().st_size, 'previous_apk_bytes': PREVIOUS.stat().st_size,
    'size_delta_bytes': DEST.stat().st_size - PREVIOUS.stat().st_size,
    'same_signing_certificate': True, 'certificate_sha256': cert,
    'jvm_tests': counts, 'source_structure_checks': 22,
    'only_modified_existing_app_file': 'ui/player/PlayerActivity.kt',
    'new_app_dependencies_or_assets': False,
    'android_device_or_emulator_tested': False,
    'lint_completed': False,
    'lint_limit': 'lint-gradle:31.6.1 unavailable in offline cache; lintVital tasks excluded',
}
record('verification-summary.json', json.dumps(summary, indent=2) + '\n')
notes = f'''# SparkTube — পপআপ/PiP ভিডিও সংশোধন

## কী ঠিক করা হয়েছে
আগের কোডে `onPause()`-এর সময় PiP flag এখনো false থাকলে ভিডিওর TextureView থেকে player বিচ্ছিন্ন হতো। PiP callback শুধু layout বদলাত; player ফের জোড়া দিত না। ফলে সিস্টেমের পপআপ controls থাকলেও ভিডিওর আউটপুট হারানোর পথ ছিল। এটি কোডভিত্তিক diagnosis; ফোনে সমস্যাটি reproduce করা হয়নি। অ্যাপে আলাদা floating-overlay service নেই: Android PiP একই PlayerActivity/TextureView ব্যবহার করে।

এখন pause-এর সময় আউটপুট রাখা হয়; activity সত্যিই অদৃশ্য হলে `onStop()`-এ detach হয়। `onStart()`, `onResume()` ও PiP-entry callback আউটপুট নিশ্চিত করে। PiP চলাকালে orientation/configuration callback আর সাধারণ watch-page layout বসাতে পারে না; ভিডিও পুরো ছোট উইন্ডোতে Fit হিসেবে থাকে। পপআপে app-এর controller বন্ধ, সিস্টেমের PiP/media-session controls অক্ষত; বের হলে স্বাভাবিক controller ও portrait/landscape layout ফেরে। Stop-এ PiP flag পরিষ্কার হয়; destroy-এ অতিরিক্ত detach নিরাপত্তা আছে। আগের surface-owner identity guard mini-player-এর নতুন surface ভুল করে বিচ্ছিন্ন হওয়া আটকায়।

## যা অপরিবর্তিত
versionName **1.4.1**, versionCode **10**, package `com.sparktube.app` এবং আগের test APK-এর signing certificate একই। আগের audio-downloads source ZIP-এর সঙ্গে সব app source, resource, library ও Gradle file তুলনায় কেবল `PlayerActivity.kt` বদলেছে। Player engine, TextureView configuration, gestures ও controls-এর bindings, notification service, compact Audio/Video switch, Library এবং audio/video download UI অপরিবর্তিত। কোনো dependency বা বড় asset যোগ হয়নি।

APK **{DEST.stat().st_size:,} bytes**, প্রায় **{DEST.stat().st_size / 1_000_000:.2f} MB**; আগের APK থেকে **{summary['size_delta_bytes']:+,} bytes**। এটি আগের মতো debug-certificate-এ signed compact test build; production release নয়।

## যাচাই ও সীমা
Build সফল, **46 JVM unit tests** এবং **22 source/XML regression checks** পাস। Package/version, আগের certificate-এর সঙ্গে মিল, APK signature এবং ZIP alignment যাচাই হয়েছে। `verification/pip-fix/`-এ log, diff ও summary আছে। এই source checks Android lifecycle বা ভিডিও rendering-এর runtime test নয়। আগের audio verifier-এর পুরোনো two-file-only historical diff এই নতুন পরিবর্তনের জন্য প্রযোজ্য নয়; তার চারটি feature check চালানো হয়েছে, আর নতুন verifier সর্বশেষ audio-downloads ZIP-এর সঙ্গে সম্পূর্ণ app-file comparison করেছে।

কোনো physical Android device বা emulator সংযুক্ত নেই। ফোনে install, PiP-তে সত্যিকারের চলমান ছবি, pause/play, ফিরে আসা, resize, notification বা gestures-এর end-to-end test হয়নি। তাই ফোনে সমস্যাটি নিশ্চিতভাবে সেরেছে বলা যাচ্ছে না। Offline cache-এ lint dependency না থাকায় lintVital tasks বাদ দেওয়া হয়েছে; lint পাস দাবি করা হচ্ছে না।

## ফোনে ছোট পরীক্ষা
ভিডিওতে চলমান ছবি দেখা গেলে Home চাপুন এবং PiP button দিয়েও আলাদাভাবে পরীক্ষা করুন। পপআপে ছবি চলতে থাকা, pause/play, ছোট-বড় করা, পূর্ণ প্লেয়ারে ফেরা, portrait/landscape এবং close করে app খুললে mini-player দেখা যাচাই করুন। এরপর Audio/Video switch, notification controls ও Library/download pages দেখুন। সমস্যা থাকলে ফোনের model/Android version এবং সমস্যার সময়ের SparkTube crash/logcat output প্রয়োজন হবে।

## সোর্স থেকে বিল্ড
JDK 21 ও Android SDK প্রয়োজন। নিজের SDK path দিয়ে `local.properties` তৈরি করুন; version অপরিবর্তিত রাখুন। সাধারণ build:

```sh
./gradlew :app:assembleCompactTest :app:testCompactTestUnitTest
python3 tools/verify-pip-fix.py
```

এখানে ব্যবহৃত offline build:

```sh
JAVA_HOME=/workspace/.jdk/temurin-21 ANDROID_HOME=/workspace/android-sdk ./gradlew --offline :app:assembleCompactTest :app:testCompactTestUnitTest -x :app:lintVitalAnalyzeCompactTest -x :app:lintVitalReportCompactTest -x :app:lintVitalCompactTest
```

APK build/JVM tests-এর জন্য পুরোনো ZIP লাগে না। Historical byte-comparison verifier-এর জন্য parent directory-তে আগের audio-downloads ও player-fixed source ZIP প্রয়োজন। Source ZIP-এ editable source, wrapper, dependencies-এর vendored JAR, tests ও verification আছে; local SDK path, cache, build output, APK ও signing key নেই। APK ও ZIP-এর SHA-256 আলাদা manifest-এ দেওয়া হয়েছে।
'''
(ROOT / 'PIP_FIX_BN.md').write_text(notes)
excluded = {'.git', '.gradle', '.kotlin', 'build', '__pycache__'}
with zipfile.ZipFile(SOURCE, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT)
        if not path.is_file() or any(part in excluded for part in rel.parts):
            continue
        if rel.parts[0] == 'verification' and 'pip-fix' not in rel.parts:
            continue
        if path.name == 'local.properties' or path.suffix in {'.jks', '.keystore', '.apk'}:
            continue
        archive.write(path, 'SparkTube-main/' + str(rel))
with zipfile.ZipFile(SOURCE) as archive:
    assert archive.testzip() is None
    for path in (ROOT / 'app/src').rglob('*'):
        if path.is_file():
            assert archive.read('SparkTube-main/' + str(path.relative_to(ROOT))) == path.read_bytes()
    assert archive.read('SparkTube-main/PIP_FIX_BN.md').decode() == notes
MANIFEST.write_text(''.join(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n' for path in [DEST, SOURCE]))
for path in [DEST, SOURCE, MANIFEST]:
    assert path.is_file() and path.stat().st_size > 0
    print(f'{path}: {path.stat().st_size} bytes')
print(json.dumps(summary, indent=2))
