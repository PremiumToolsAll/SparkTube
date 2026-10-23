#!/usr/bin/env python3
"""Package verified current-source artifacts, retaining the previous test certificate."""
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
VERIFY = ROOT / 'verification/notification-response'
BIN = OUT / 'android-sdk/build-tools/36.0.0'
APK = ROOT / 'app/build/outputs/apk/compactTest/app-compactTest.apk'
PREVIOUS = OUT / 'SparkTube-1.4.1-pip-fixed-test.apk'
DEST = OUT / 'SparkTube-1.4.1-fast-home-test.apk'
SOURCE = OUT / 'SparkTube-1.4.1-fast-home-source.zip'
MANIFEST = OUT / 'SHA256SUMS-SparkTube-1.4.1-fast-home.txt'

def run(*args):
    return subprocess.check_output(list(map(str, args)), text=True, stderr=subprocess.STDOUT)
def record(name, text):
    (VERIFY / name).write_text(text)
    return text

assert 'BUILD SUCCESSFUL' in (VERIFY / 'build.log').read_text()
checks = record('feature-checks.log', run('python3', ROOT / 'tools/verify-current-update.py'))
assert '\nOK\n' in checks
structure_count = int(re.search(r'Ran (\d+) tests', checks).group(1))
badging = record('apk-badging.txt', run(BIN / 'aapt2', 'dump', 'badging', APK))
assert "versionCode='10'" in badging.splitlines()[0] and "versionName='1.4.1'" in badging.splitlines()[0]
assert "name='com.sparktube.app'" in badging.splitlines()[0]
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
assert counts['tests'] >= 63 and counts['failures'] == counts['errors'] == counts['skipped'] == 0, counts
assert (VERIFY / 'TEST-com.sparktube.app.data.ProgressiveFeedLoaderTest.xml').is_file()
record('adb-devices.txt', run(OUT / 'android-sdk/platform-tools/adb', 'devices'))
changes = []
with zipfile.ZipFile(OUT / 'SparkTube-1.4.1-pip-fixed-source.zip') as previous:
    for name in previous.namelist():
        rel = name.removeprefix('SparkTube-main/')
        if not (rel.startswith('app/') or rel.endswith('.gradle.kts') or rel == 'gradle.properties'):
            continue
        path = ROOT / rel
        if path.is_file() and path.read_bytes() != previous.read(name):
            changes.append(rel)
            if path.suffix in {'.kt', '.java', '.xml', '.kts'}:
                record(path.name + '.diff', ''.join(difflib.unified_diff(previous.read(name).decode().splitlines(True), path.read_text().splitlines(True), fromfile='before/' + rel, tofile='after/' + rel)))
shutil.copy2(APK, DEST)
assert DEST.stat().st_size <= PREVIOUS.stat().st_size + 100_000
summary = {
    'versionName': '1.4.1', 'versionCode': 10,
    'apk_bytes': DEST.stat().st_size, 'previous_apk_bytes': PREVIOUS.stat().st_size,
    'size_delta_bytes': DEST.stat().st_size - PREVIOUS.stat().st_size,
    'same_signing_certificate': True, 'certificate_sha256': cert,
    'jvm_tests': counts, 'source_structure_checks': structure_count,
    'modified_existing_app_files': changes,
    'new_dependencies_or_assets': False,
    'android_device_or_emulator_tested': False,
    'notification_latency_measured': False,
    'lint_completed': False,
    'lint_limit': 'Offline lint dependency unavailable; lintVital tasks excluded, no lint pass claimed.',
}
record('verification-summary.json', json.dumps(summary, indent=2) + '\n')
notes = f'''# SparkTube — দ্রুত হোম ফিড, মিডিয়া কন্ট্রোল ও সোয়াইপ সিক

## নতুন আচরণ
অ্যাপ খোলার সময় আগের সফল হোম ফিডের সীমিত, দেশভিত্তিক cache থেকে ভিডিও কার্ড আগে দেখানো হয়; নতুন ফিড পেছনে refresh হয়। Cache-এ শুধু ভিডিওর তালিকার তথ্য ও thumbnail URL থাকে, playable stream URL নয়। Fresh install বা cache না থাকলে তিনটি feed source একসঙ্গে লোড হয় এবং প্রথম সফল source-এর ফল বাকি source ও পূর্ণ recommendation ranking শেষ হওয়ার আগেই দেখানো হয়। Refresh ব্যর্থ হলে ব্যবহারযোগ্য পুরোনো তালিকা মুছে ফেলা হয় না। প্রথমবারের network request বা uncached thumbnail-কে offline/তাৎক্ষণিক বলে দাবি করা হচ্ছে না।

নোটিফিকেশনের Previous / Play-Pause / Next রাখা হয়েছে। বাফারিং চলাকালে play/pause এখন `isPlaying` নয়, ব্যবহারকারীর `playWhenReady` intent ধরে কাজ করে। নতুন ভিডিওতে Next/Previous চাপলে আগের ভিডিওর অডিও থামে এবং session-এ নতুন শিরোনাম ও সত্যিকারের loading/buffering অবস্থা স্ট্রিম URL পাওয়ার আগেই পাঠানো হয়। লোডিংয়ের মধ্যে Pause দিলে নতুন source তৈরি হওয়ার পর সেটি নিজে থেকে আর বাজবে না। দ্রুত পরপর Next/Previous চাপলে বাতিল পুরোনো কাজ নতুন নির্বাচনের state মুছতে পারে না। প্রকৃত ভিডিও/অডিও শুরু হতে নেটওয়ার্ক সময় লাগতে পারে; READY বা playing-এর মিথ্যা অবস্থা দেখানো হয় না।

ভিডিও পেজের সক্রিয় “Downloading · …%” বাটনে চাপলে Library → Downloads খুলবে এবং বিদ্যমান live progress refresh চলবে। ডাউনলোড না চললে আগের quality/audio-video download sheet এবং সম্পূর্ণ ডাউনলোডের delete confirmation থাকে।

ডানে অনুভূমিক সোয়াইপে ধীরে সামনে, বামে পিছনে seek preview হয়; আঙুল ছাড়লে সেই অবস্থানে যাওয়া হয়। ছোট নড়াচড়া ও দিক নির্বাচন আলাদা করা হয়েছে, যাতে ওপর-নিচের brightness/volume gesture-এর সঙ্গে না মেশে। আগের double-tap ±১০ সেকেন্ডও থাকে। Cancel হলে seek হয় না।

## যা সংরক্ষিত
সংস্করণ **1.4.1**, versionCode **10**, package `com.sparktube.app` এবং আগের test APK-এর signing certificate অপরিবর্তিত। Compact test build; production release নয়। PiP lifecycle/rendering fix, audio/video downloads, কিউ transport, বিদ্যমান controls ও resources রাখা হয়েছে। নতুন dependency বা বড় asset নেই। APK **{DEST.stat().st_size:,} bytes** (প্রায় **{DEST.stat().st_size / 1_000_000:.2f} MB**); আগের PiP test APK থেকে **{summary['size_delta_bytes']:+,} bytes**।

## যাচাই ও সীমা
Build সফল; **{counts['tests']} JVM unit tests** এবং **{structure_count} source/XML regression checks** পাস। Source checks Android runtime test নয়। সর্বশেষ PiP source ZIP-এর সঙ্গে app files তুলনা করে শুধু অনুমোদিত playback, navigation ও gesture files বদলানোর যাচাই আছে। পুরোনো আপডেটগুলোর historical “অন্য কোনো ফাইল বদলাবে না” assertion বর্তমান scope-এর জন্য বাদ দিয়ে নতুন latest-source scope audit চালানো হয়েছে; feature checks রাখা হয়েছে। Signature/certificate match, version/package এবং ZIP alignment যাচাই হয়েছে।

কোনো physical Android device বা emulator সংযুক্ত নেই; ফোনে install, notification latency, swipe feel, PiP rendering বা download navigation-এর end-to-end পরীক্ষা করা হয়নি। তাই ফোনে নিশ্চিত তাৎক্ষণিক প্রতিক্রিয়া দাবি করা হচ্ছে না। Offline lint dependency না থাকায় lintVital tasks বাদ; lint পাস দাবি নেই। Logs, diffs, test XML ও summary `verification/notification-response/`-এ আছে।

## ফোনে সংক্ষিপ্ত পরীক্ষা
০. একবার Home লোড করে অ্যাপ সম্পূর্ণ বন্ধ করে ফের খুলুন; আগের কার্ড আগে দেখা এবং পেছনে refresh পরীক্ষা করুন। Slow/offline network, fresh install, country change ও pull-to-refresh-ও দেখুন; অন্য দেশের cache যেন না আসে।
১. চলমান ও buffering ভিডিও/গানে notification Play/Pause দ্রুত চাপুন; পজ দিলে নেটওয়ার্ক ফেরার পর নিজে থেকে বাজে কি না দেখুন।
২. ভিডিও কিউতে Next/Previous দ্রুত চাপুন; নতুন শিরোনাম/loading, সঠিক শেষ নির্বাচন এবং আগের অডিও বন্ধ হওয়া দেখুন। কিউয়ের শুরু/শেষও পরীক্ষা করুন।
৩. “Downloading · …%” চাপুন; Downloads-এ বর্তমান অগ্রগতি এবং pause/resume/cancel দেখুন। Idle download button-এর sheet ও completed download delete অপরিবর্তিত আছে কি না দেখুন।
৪. ডানে/বামে ধীরে সোয়াইপ, seek preview/release, শুরু/শেষ সীমা, double-tap ±১০ সেকেন্ড, brightness/volume এবং portrait/landscape পরীক্ষা করুন।
৫. Home/PiP, full-player-এ ফেরা এবং audio/video download পরীক্ষা করুন।

## সোর্স থেকে বিল্ড
JDK 21 ও Android SDK দিয়ে নিজের `local.properties` বানিয়ে চালান:

```sh
./gradlew :app:assembleCompactTest :app:testCompactTestUnitTest
```

এখানে ব্যবহৃত offline command:

```sh
JAVA_HOME=/workspace/.jdk/temurin-21 ANDROID_HOME=/workspace/android-sdk ./gradlew --offline :app:assembleCompactTest :app:testCompactTestUnitTest -x :app:lintVitalAnalyzeCompactTest -x :app:lintVitalReportCompactTest -x :app:lintVitalCompactTest
```

ZIP-এ editable source, Gradle wrapper, vendored libraries, unit tests ও verification আছে; build output/cache, local SDK path, APK ও signing key নেই। APK ও ZIP-এর SHA-256 আলাদা manifest-এ আছে। ঐতিহাসিক diff verifier চালাতে আগের source ZIP parent folder-এ লাগে; APK build বা JVM tests-এর জন্য লাগে না।
'''
(ROOT / 'RESPONSIVE_CONTROLS_BN.md').write_text(notes)
excluded = {'.git', '.gradle', '.kotlin', 'build', '__pycache__'}
with zipfile.ZipFile(SOURCE, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(ROOT.rglob('*')):
        rel = path.relative_to(ROOT)
        if not path.is_file() or any(part in excluded for part in rel.parts):
            continue
        if rel.parts[0] == 'verification' and 'notification-response' not in rel.parts:
            continue
        if path.name in {'local.properties', 'compile.log'} or '.before.' in path.name or path.suffix in {'.jks', '.keystore', '.apk'}:
            continue
        archive.write(path, 'SparkTube-main/' + str(rel))
with zipfile.ZipFile(SOURCE) as archive:
    assert archive.testzip() is None
    for path in (ROOT / 'app/src').rglob('*'):
        if path.is_file():
            assert archive.read('SparkTube-main/' + str(path.relative_to(ROOT))) == path.read_bytes()
    assert archive.read('SparkTube-main/RESPONSIVE_CONTROLS_BN.md').decode() == notes
MANIFEST.write_text(''.join(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n' for path in [DEST, SOURCE]))
for path in [DEST, SOURCE, MANIFEST]:
    assert path.is_file() and path.stat().st_size > 0
    print(f'{path}: {path.stat().st_size} bytes')
print(json.dumps(summary, indent=2))
