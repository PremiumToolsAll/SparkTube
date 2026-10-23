#!/usr/bin/env python3
"""Verify and package an already-built compact APK. No Android runtime test is claimed."""
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
VERIFY = ROOT/'verification/render-controls'
SDK = Path('/workspace/android-sdk')
BIN = SDK/'build-tools/36.0.0'
APK = ROOT/'app/build/outputs/apk/compactTest/app-compactTest.apk'
OLD = OUT/'SparkTube-1.4.1-player-fixed-test.apk'
DEST = OUT/'SparkTube-1.4.1-render-controls-test.apk'
SOURCE = OUT/'SparkTube-1.4.1-render-controls-source.zip'
MANIFEST = OUT/'SHA256SUMS-SparkTube-1.4.1-render-controls.txt'

def run(program, *args):
    return subprocess.check_output([str(program), *map(str,args)], text=True, stderr=subprocess.STDOUT)

def record(name, text):
    (VERIFY/name).write_text(text)
    return text

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert APK.is_file()
# Source hashes were captured for the exact compilation inputs before the final successful build.
subprocess.run(['sha256sum','-c',str(VERIFY/'compiled-source.sha256')], cwd=ROOT, check=True,
               stdout=subprocess.DEVNULL)
badging = record('apk-badging.txt', run(BIN/'aapt2','dump','badging',APK))
assert "versionCode='10'" in badging.splitlines()[0]
assert "versionName='1.4.1'" in badging.splitlines()[0]
signature = record('signature-after.txt', run(BIN/'apksigner','verify','--print-certs',APK))
old_signature = record('signature-before.txt', run(BIN/'apksigner','verify','--print-certs',OLD))
cert = re.search(r'certificate SHA-256 digest: (\w+)', signature).group(1)
assert cert == re.search(r'certificate SHA-256 digest: (\w+)', old_signature).group(1)
record('zipalign.txt', run(BIN/'zipalign','-c','-v','4',APK))
resources = record('resources.txt',run(BIN/'aapt2','dump','resources',APK))

def resource_id(name):
    return re.search(r'resource (0x[0-9a-f]+) '+re.escape(name)+r'\b',resources).group(1)

def layout(name):
    path = re.search(r'layout/'+re.escape(name)+r'\n\s+\(\) \(file\) (\S+)',resources).group(1)
    return run(BIN/'aapt2','dump','xmltree',APK,'--file',path)

player_xml = record('compiled-player-layout.txt',layout('activity_player'))
controller_xml = record('compiled-controller-layout.txt',layout('player_queue_controller'))
mini_xml = record('compiled-mini-layout.txt',layout('activity_main'))
for name in ['transportControls','queuePrevious','queuePlayPause','queueNext']:
    assert '=@'+resource_id('id/'+name) in player_xml
assert re.search(r'surface_type\([^)]*\)=2\b',player_xml)
assert re.search(r'surface_type\([^)]*\)=2\b',mini_xml)
assert '=@'+resource_id('layout/player_queue_controller') in player_xml
for name in ['exo_play_pause','exo_prev','exo_next']:
    assert '=@'+resource_id('id/'+name) not in controller_xml

results = list((ROOT/'app/build/test-results/testCompactTestUnitTest').glob('TEST-*.xml'))
counts = dict(tests=0,failures=0,errors=0,skipped=0)
for path in results:
    elem=ET.parse(path).getroot()
    for key in counts:
        counts[key] += int(elem.get(key,'0'))
    shutil.copy2(path,VERIFY/path.name)
assert counts['tests'] == 38 and counts['failures'] == counts['errors'] == counts['skipped'] == 0, counts
record('adb-devices.txt',run(SDK/'platform-tools/adb','devices'))
new_bridge = ROOT/'app/build/intermediates/javac/compactTest/compileCompactTestJavaWithJavac/classes/com/sparktube/app/playback/PlayerListenerBridge.class'
bytecode = record('fixed-listener-bridge-bytecode.txt',run('/workspace/jdk-17/bin/javap','-p','-c',new_bridge))
for name in ['onRenderedFirstFrame','onTracksChanged','onVideoSizeChanged']:
    assert re.search(r'public void '+name+r'\(',bytecode)

shutil.copy2(APK,DEST)
summary = {
 'package':'com.sparktube.app','versionName':'1.4.1','versionCode':10,
 'apk':DEST.name,'apk_bytes':DEST.stat().st_size,'previous_apk_bytes':OLD.stat().st_size,
 'size_delta_bytes':DEST.stat().st_size-OLD.stat().st_size,
 'apk_sha256':sha(DEST),'same_signing_certificate':True,'certificate_sha256':cert,
 'jvm_tests':counts,'structural_tests':10,'compiled_apk_layout_verified':True,
 'source_hashes_match_compiled_inputs':True,'physical_android_device_attached':False,
 'android_runtime_or_emulator_tested':False,'owner_phone_black_screen_confirmed_fixed':False,
 'root_cause_evidence':'Old Kotlin Player.Listener by delegate compiled only two explicit overrides; Java-default first-frame/tracks/size callbacks were swallowed. Regression reproduces old loss and checks all 37 callbacks on new explicit bridge.',
 'lint_completed':False,
 'lint_note':'See lint.log; offline lint dependency availability is checked separately.',
 'unchanged_features':'PlaybackService, queue policy, Library, gestures, Audio-Video music view, download UI/metrics/sharing, dependencies and Gradle version settings byte-identical to previous source ZIP.'
}
lint=(VERIFY/'lint.log').read_text() if (VERIFY/'lint.log').exists() else ''
if 'LINT_EXIT_CODE=0' in lint:
    summary['lint_completed']=True
    summary['lint_note']='Completed; see lint.log.'
elif 'LINT_EXIT_CODE=' in lint:
    summary['lint_note']='Lint did not complete successfully; see lint.log. Not counted as a passed test.'
record('verification-summary.json',json.dumps(summary,indent=2)+'\n')

# Include source, vendored libraries, wrapper, tests and evidence; never local keys/caches/build outputs.
excluded={'.git','.gradle','.kotlin','build','__pycache__'}
with zipfile.ZipFile(SOURCE,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
    for path in sorted(ROOT.rglob('*')):
        relative=path.relative_to(ROOT)
        if not path.is_file() or any(part in excluded for part in relative.parts):
            continue
        if path.name == 'local.properties' or path.suffix in {'.jks','.keystore','.apk'}:
            continue
        archive.write(path,'SparkTube-main/'+str(relative))
with zipfile.ZipFile(SOURCE) as archive:
    assert archive.testzip() is None
    for relative in ['app/src/main/java/com/sparktube/app/playback/PlaybackCenter.kt',
                     'app/src/main/java/com/sparktube/app/playback/PlayerListenerBridge.java',
                     'app/src/main/res/layout/activity_player.xml',
                     'app/src/test/java/com/sparktube/app/playback/PlayerListenerBridgeTest.kt']:
        assert archive.read('SparkTube-main/'+relative)==(ROOT/relative).read_bytes()
MANIFEST.write_text(''.join(f'{sha(path)}  {path.name}\n' for path in [DEST,SOURCE]))
for path in [DEST,SOURCE,MANIFEST]:
    assert path.is_file() and path.stat().st_size>0
    print(f'{path}: {path.stat().st_size} bytes')
print(json.dumps(summary,indent=2))
