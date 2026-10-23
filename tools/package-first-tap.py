#!/usr/bin/env python3
"""Package the current test build, source, evidence and SHA-256 checksums."""
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
VERIFY = ROOT / 'verification/notification-first-tap'
APK = ROOT / 'app/build/outputs/apk/compactTest/app-compactTest.apk'
DEST = OUT / 'SparkTube-1.4.1-notification-audio-test.apk'
SOURCE = OUT / 'SparkTube-1.4.1-notification-audio-source.zip'
SUMS = OUT / 'SHA256SUMS-SparkTube-1.4.1-notification-audio.txt'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert 'BUILD SUCCESSFUL' in (VERIFY / 'build.log').read_text()
checks = (VERIFY / 'feature-checks.log').read_text()
assert '\nOK\n' in checks
check_count = int(re.search(r'Ran (\d+) tests', checks).group(1))
badging = (VERIFY / 'apk-badging.txt').read_text().splitlines()[0]
for part in ["name='com.sparktube.app'", "versionCode='10'", "versionName='1.4.1'"]:
    assert part in badging
signatures = [(VERIFY / name).read_text() for name in ['signature-before.txt', 'signature-after.txt']]
certs = [re.search(r'certificate SHA-256 digest: (\w+)', text).group(1) for text in signatures]
assert certs[0] == certs[1]
assert 'Verification successful' in (VERIFY / 'zipalign.txt').read_text()
counts = dict(tests=0, failures=0, errors=0, skipped=0)
for path in sorted((ROOT / 'app/build/test-results/testCompactTestUnitTest').glob('TEST-*.xml')):
    elem = ET.parse(path).getroot()
    for key in counts:
        counts[key] += int(elem.get(key, '0'))
    shutil.copy2(path, VERIFY / path.name)
assert counts['tests'] >= 77 and counts['failures'] == counts['errors'] == counts['skipped'] == 0
changes = []
with zipfile.ZipFile(OUT / 'SparkTube-1.4.1-fast-home-source.zip') as old:
    for name in old.namelist():
        rel = name.removeprefix('SparkTube-main/')
        if not rel.startswith('app/src/'):
            continue
        path = ROOT / rel
        if path.is_file() and path.read_bytes() != old.read(name):
            changes.append(rel)
            (VERIFY / (path.name + '.diff')).write_text(''.join(difflib.unified_diff(
                old.read(name).decode().splitlines(True), path.read_text().splitlines(True),
                fromfile='before/' + rel, tofile='after/' + rel)))
summary = {
    'versionName': '1.4.1', 'versionCode': 10,
    'same_signing_certificate_as_fast_home_test': True,
    'certificate_sha256': certs[1], 'jvm_tests': counts,
    'source_structure_checks': check_count,
    'modified_existing_app_files': changes,
    'new_app_files': [
        'app/src/main/java/com/sparktube/app/playback/NotificationTransport.kt',
        'app/src/test/java/com/sparktube/app/playback/NotificationTransportTest.kt'],
    'android_device_or_emulator_tested': False,
    'notification_latency_measured': False,
    'lint_completed': False,
    'lint_limit': 'Offline lint dependencies unavailable; lintVital tasks excluded.',
    'apk_sha256': digest(APK), 'apk_bytes': APK.stat().st_size
}
(VERIFY / 'verification-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
notes = f'''# SparkTube 1.4.1 — নোটিফিকেশন ও অডিও ফাইল খোলা

## এই আপডেটে
নোটিফিকেশন থেকে আসা Play/Pause key-down এখন MediaSession callback-এ সরাসরি session player-কে দেওয়া হয় এবং handled হিসেবে ফেরত যায়। এতে ওই ট্যাপ Media3-এর সাধারণ media-key fallback/command-queue পথে যায় না। Media3 1.3.1-এর bytecode-এ কিছু legacy play/pause key-এর জন্য double-tap timeout এবং দ্বিতীয় ট্যাপকে Next হিসেবে নেওয়ার পথ আছে; নোটিফিকেশনের পৃথক ট্যাপে সেই gesture recognizer প্রযোজ্য নয়। এই পরিবর্তন শুধু notification controller-এর toggle key-এ সীমিত; headset, Bluetooth-এর native transport, Previous/Next ও অন্য commands আগের পথে থাকে। নির্দিষ্ট ফোনে আগের ব্যর্থতার একমাত্র কারণ এটি—এমন runtime প্রমাণ নেই।

বাফারিংয়ে `isPlaying` নয়, `playWhenReady` অনুযায়ী Play/Pause বদলায়। একই ট্যাপ দ্বিতীয়বার default handler-এ যায় না, held-key repeat উপেক্ষা করা হয়। Idle source-এ prepare এবং ended source-এ restart-এর আচরণ রাখা হয়েছে। আগে করা pending-video pause, queue ও player fixes অপরিবর্তিত।

Library → Downloads-এ সম্পন্ন AUDIO আইটেমে ট্যাপ করলে তার বিদ্যমান নির্দিষ্ট `file://` ফাইলের এক-আইটেম music queue চালু হয় এবং Now Playing খোলে। অনলাইনে আবার resolve করা হয় না। Audio Downloads তালিকার বিদ্যমান নির্দিষ্ট ফাইল বেছে চালানোর আচরণ রাখা হয়েছে। ফাইল মুছে গেলে missing-file বার্তা আসে; ভিডিও/AV downloads আগের আচরণেই থাকে।

## যাচাই
বিল্ড সফল। {counts['tests']} JVM unit tests ও {check_count} source/XML checks পাস; এগুলো Android runtime test নয়। নতুন transport tests-এ প্রথম ট্যাপ, দ্রুত আলাদা ট্যাপ, buffering, key-up/repeat, headset fallback, command availability এবং idle/ended source আছে। Latest fast-home source-এর সঙ্গে app files তুলনায় কেবল PlaybackService.kt ও LibraryFragment.kt বদলেছে; নতুন handler ও তার unit test যোগ হয়েছে। Version **1.4.1 / code 10**, package ও আগের test APK-এর signing certificate এক। Dependencies, resources ও build configuration অপরিবর্তিত। ZIP alignment এবং signing verification পাস।

কোনো Android ফোন বা emulator সংযুক্ত নেই। Notification tap latency, install/update ও লোকাল অডিও playback-এর device test করা হয়নি; তাৎক্ষণিক audible playback-এর নিশ্চয়তা দেওয়া হচ্ছে না। Network buffering চললে Play চাপার পরে মিডিয়া শুরু হতে সময় লাগতে পারে। Offline lint dependency সীমার কারণে lintVital বাদ ছিল, lint পাস দাবি করা হচ্ছে না।

## ফোনে সংক্ষিপ্ত পরীক্ষা
১. চলমান অডিও ও ভিডিওতে notification Pause একবার চাপুন; তারপর Play একবার। দ্রুত পরপর পৃথক ট্যাপেও কিউ যেন Next না হয়।
২. Buffering ও নতুন ভিডিও resolving অবস্থায় Pause দিয়ে অপেক্ষা করুন; স্ট্রিম তৈরি হলে নিজে থেকে বাজা উচিত নয়। Headset single/double-tap, Previous/Next ও screen-off controls-ও দেখুন।
৩. Downloads এবং Audio Downloads-এ একাধিক সম্পন্ন অডিওর আলাদা আলাদা আইটেম চাপুন; প্রতিবার ট্যাপ করা লোকাল ফাইলই যেন চালু হয়। Offline অবস্থায়ও দেখুন। Missing file, paused/incomplete download ও video/AV download যাচাই করুন।
৪. PiP, home feed, swipe seek ও downloads-এর আগের আচরণ দেখুন।

## সোর্স থেকে বিল্ড
JDK 21 ও Android SDK দিয়ে নিজের local.properties তৈরি করুন।

```sh
./gradlew :app:assembleCompactTest :app:testCompactTestUnitTest
```

এখানে ব্যবহৃত command:

```sh
JAVA_HOME=/workspace/.jdk/temurin-21 ANDROID_HOME=/workspace/android-sdk ./gradlew --offline :app:assembleCompactTest :app:testCompactTestUnitTest --rerun-tasks -x :app:lintVitalAnalyzeCompactTest -x :app:lintVitalReportCompactTest -x :app:lintVitalCompactTest
```

ZIP-এ editable source, Gradle wrapper, vendored libraries, unit tests এবং `verification/notification-first-tap/`-এ যাচাইয়ের প্রমাণ আছে। Signing key, APK, machine-local SDK path ও build caches নেই। সোর্স থেকে নিজের build-এর signing key আলাদা হতে পারে। Historical scope comparison-এর জন্য আগের source ZIP লাগে, APK build বা JVM tests-এর জন্য নয়।
'''
(ROOT / 'NOTIFICATION_AUDIO_FIX_BN.md').write_text(notes)
shutil.copy2(APK, DEST)
excluded = {'.git', '.gradle', '.kotlin', 'build', '__pycache__'}
with zipfile.ZipFile(SOURCE, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT)
        if not path.is_file() or any(part in excluded for part in rel.parts):
            continue
        if rel.parts[0] == 'verification' and 'notification-first-tap' not in rel.parts:
            continue
        if path.name in {'local.properties', 'compile.log'} or '.before.' in path.name or path.suffix in {'.jks', '.keystore', '.apk'}:
            continue
        archive.write(path, 'SparkTube-main/' + str(rel))
with zipfile.ZipFile(SOURCE) as archive:
    assert archive.testzip() is None
    for path in (ROOT / 'app/src').rglob('*'):
        if path.is_file():
            assert archive.read('SparkTube-main/' + str(path.relative_to(ROOT))) == path.read_bytes()
    assert archive.read('SparkTube-main/NOTIFICATION_AUDIO_FIX_BN.md').decode() == notes
SUMS.write_text(''.join(f'{digest(path)}  {path.name}\n' for path in [DEST, SOURCE]))
for path in [DEST, SOURCE, SUMS]:
    assert path.is_file() and path.stat().st_size > 0
    print(f'{path}: {path.stat().st_size} bytes')
print(json.dumps(summary, indent=2))
