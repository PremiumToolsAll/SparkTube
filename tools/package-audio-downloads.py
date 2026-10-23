#!/usr/bin/env python3
"""Package audio download test build with verification; never claims runtime testing."""
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
VERIFY = ROOT / 'verification/audio-downloads'
BIN = OUT / 'android-sdk/build-tools/36.0.0'
APK = ROOT / 'app/build/outputs/apk/compactTest/app-compactTest.apk'
PREVIOUS = OUT / 'SparkTube-1.4.1-compact-toggle-test.apk'
DEST = OUT / 'SparkTube-1.4.1-audio-downloads-test.apk'
SOURCE = OUT / 'SparkTube-1.4.1-audio-downloads-source.zip'
MANIFEST = OUT / 'SHA256SUMS-SparkTube-1.4.1-audio-downloads.txt'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(*args):
    return subprocess.check_output(list(map(str, args)), text=True, stderr=subprocess.STDOUT)

def record(name, text):
    (VERIFY / name).write_text(text)
    return text

for script, log in [('verify-player-correction.py', 'player-structure-tests.log'), ('verify-audio-downloads.py', 'audio-structure-tests.log')]:
    record(log, run('python3', ROOT / 'tools' / script))
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
assert counts['tests'] == 46 and counts['failures'] == counts['errors'] == counts['skipped'] == 0, counts
record('adb-devices.txt', run(OUT / 'android-sdk/platform-tools/adb', 'devices'))
shutil.copy2(APK, DEST)
summary = {
    'versionName': '1.4.1', 'versionCode': 10,
    'apk_bytes': DEST.stat().st_size, 'previous_apk_bytes': PREVIOUS.stat().st_size,
    'size_delta_bytes': DEST.stat().st_size - PREVIOUS.stat().st_size,
    'same_signing_certificate': True, 'certificate_sha256': cert,
    'jvm_tests': counts, 'structural_tests': 15,
    'new_dependencies': False,
    'existing_modified_app_files': ['ui/common/DownloadAdapter.kt', 'ui/music/MusicListActivity.kt'],
    'new_app_files': ['ui/music/AudioDownloadLibrary.kt'],
    'video_engine_player_and_compact_toggle_source_unchanged': True,
    'android_runtime_or_emulator_tested': False,
    'lint_completed': False,
    'lint_limit': 'lint-gradle:31.6.1 not available in offline cache; lintVital tasks excluded',
}
record('verification-summary.json', json.dumps(summary, indent=2) + '\n')
notes = f'''# SparkTube 1.4.1 — অডিও ডাউনলোড টেস্ট বিল্ড

## নতুন কী

Music → Downloads পেজে এখন শুধু সম্পন্ন গান নয়, চলমান, অপেক্ষমাণ, paused ও ব্যর্থ অডিও ডাউনলোডও দেখা যায়। ভিডিওর একই download adapter/engine দিয়ে pause/resume, progress bar, শতাংশ (মোট সাইজ জানা থাকলে), downloaded/total MB, MB/s এবং বাকি সময় দেখায়। অজানা মোট সাইজ বা সময়কে অনুমান করে দেখায় না।

গানের সারিতে বর্গাকার album art, শিরোনাম ও artist আছে। উপরে গানের সংখ্যা ও সবুজ Play all রাখা হয়েছে। গান গোনা ও Play all-এর কিউতে শুধু সম্পূর্ণ এবং ডিস্কে থাকা অডিও যায়; আংশিক ফাইল বাজানো হয় না। সম্পন্ন গানের তিন-ডট মেনুতে Open, Share, Delete আছে; Delete-এ confirmation দেখায়। চলমান/ব্যর্থ সারি long-press করে মুছতে পারেন। পেজ খোলা থাকলে প্রতি সেকেন্ডে অগ্রগতি আপডেট হয়; অন্য পেজে গেলে polling বন্ধ হয়।

## যা অপরিবর্তিত

`com.sparktube.app`, versionName **1.4.1**, versionCode **10** এবং আগের টেস্ট APK-এর signing certificate একই। ভিডিও download engine, Library downloads, player ও compact Audio/Video toggle-এর সোর্স অপরিবর্তিত। DownloadAdapter-এ audioStyle opt-in; পুরোনো default video view আগের পথেই চলে। নতুন dependency, native library বা বড় image asset যোগ হয়নি।

APK: **{DEST.stat().st_size:,} bytes** ({DEST.stat().st_size / 1_000_000:.2f} MB); আগের compact-toggle APK থেকে পরিবর্তন **{summary['size_delta_bytes']:+,} bytes**। এটি debug-signed test build, store release নয়।

## যাচাই ও সীমা

বিল্ড সফল; **46 JVM tests** (অডিও লাইব্রেরির 8 নতুন test-সহ) এবং **15 source/XML structure checks** পাস। APK package/version, signature এবং ZIP alignment যাচাই করা হয়েছে। আগের editable ZIP-এর সঙ্গে মিলিয়ে পুরোনো app source-এ কেবল MusicListActivity ও DownloadAdapter বদলানোর বিষয়টি পরীক্ষা হয়েছে। এটি source-level regression evidence, runtime-এর নিশ্চয়তা নয়।

কোনো Android ফোন বা emulator সংযুক্ত নেই। তাই আসল ফোনে install, screen rendering, download, pause/resume, Play all, playback, share/delete-এর end-to-end পরীক্ষা হয়নি। Android lint offline cache-এ প্রয়োজনীয় `lint-gradle:31.6.1` না থাকায় lintVital ধাপ বাদ দেওয়া হয়েছে; full lint সম্পন্ন হয়নি। আগের deprecation warnings আছে।

আগের সীমাবদ্ধতা একই: pause/resume কেবল চলমান app process-এর মধ্যে; process kill বা restart-এর পর অসম্পূর্ণ download আবার শুরু করতে হবে। Range সমর্থন না করা server pause-এর সময় সংযোগ ছিন্ন করলে download ব্যর্থ হতে পারে। ব্যর্থ item long-press করে মুছে পুনরায় download করতে হবে; নতুন retry/restart button যোগ করা হয়নি।

## সোর্স থেকে বিল্ড

JDK 21 ও Android SDK ব্যবহার করুন; নিজের SDK path দিয়ে `local.properties` তৈরি করুন। `app/build.gradle.kts`-এ version বদলাবেন না।

```sh
./gradlew :app:assembleCompactTest :app:testCompactTestUnitTest
```

এই পরিবেশে offline build command:

```sh
JAVA_HOME=/workspace/.jdk/temurin-21 ANDROID_HOME=/workspace/android-sdk ./gradlew --offline :app:assembleCompactTest :app:testCompactTestUnitTest -x :app:lintVitalAnalyzeCompactTest -x :app:lintVitalReportCompactTest -x :app:lintVitalCompactTest
python3 tools/verify-player-correction.py
python3 tools/verify-audio-downloads.py
```

`verification/audio-downloads/`-এ বর্তমান বিল্ড ও টেস্ট ফল রয়েছে। আগের ZIP-নির্ভর byte comparison script-এর জন্য আগের compact-toggle source ZIP parent folder-এ রাখতে হয়; APK build বা JVM tests-এর জন্য তা লাগে না। সোর্স ZIP-এ local SDK path, build cache, APK ও signing key নেই। চূড়ান্ত APK ও source ZIP-এর SHA-256 আলাদা manifest-এ আছে।
'''
(ROOT / 'AUDIO_DOWNLOADS_BN.md').write_text(notes)
excluded = {'.git', '.gradle', '.kotlin', 'build', '__pycache__'}
with zipfile.ZipFile(SOURCE, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT)
        if not path.is_file() or any(part in excluded for part in rel.parts):
            continue
        if rel.parts[0] == 'verification' and 'audio-downloads' not in rel.parts:
            continue
        if path.name == 'local.properties' or path.suffix in {'.jks', '.keystore', '.apk'}:
            continue
        archive.write(path, 'SparkTube-main/' + str(rel))
with zipfile.ZipFile(SOURCE) as archive:
    assert archive.testzip() is None
    for path in (ROOT / 'app/src').rglob('*'):
        if path.is_file():
            assert archive.read('SparkTube-main/' + str(path.relative_to(ROOT))) == path.read_bytes()
    assert archive.read('SparkTube-main/AUDIO_DOWNLOADS_BN.md').decode() == notes
MANIFEST.write_text(''.join(f'{sha(path)}  {path.name}\n' for path in [DEST, SOURCE]))
for path in [DEST, SOURCE, MANIFEST]:
    assert path.is_file() and path.stat().st_size > 0
    print(f'{path}: {path.stat().st_size} bytes')
print(json.dumps(summary, indent=2))
