#!/usr/bin/env python3
"""Package the validated APK, matching editable sources and checksum manifest."""
from pathlib import Path
import difflib
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
R=Path(__file__).resolve().parents[1]
V=R/'verification/sleep-timer'
O=R.parent
APK=R/'app/build/outputs/apk/compactTest/app-compactTest.apk'
DEST=O/'SparkTube-1.4.1-sleep-timer-test.apk'
SRC=O/'SparkTube-1.4.1-sleep-timer-source.zip'
SUM=O/'SHA256SUMS-SparkTube-1.4.1-sleep-timer.txt'
B=O/'android-sdk/build-tools/36.0.0'
def command(args,path):
    result=subprocess.run([str(x) for x in args],capture_output=True,text=True,check=True)
    path.write_text(result.stdout+result.stderr)
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert 'BUILD SUCCESSFUL' in (V/'build.log').read_text()
checks=(V/'feature-checks.log').read_text()
assert '\nOK\n' in checks
command([B/'aapt','dump','badging',APK], V/'apk-badging.txt')
command([B/'apksigner','verify','--verbose','--print-certs',O/'SparkTube-1.4.1-video-collapse-test.apk'],V/'signature-before.txt')
command([B/'apksigner','verify','--verbose','--print-certs',APK],V/'signature-after.txt')
command([B/'zipalign','-c','-v','4',APK],V/'zipalign.txt')
badging=(V/'apk-badging.txt').read_text().splitlines()[0]
for expected in ["name='com.sparktube.app'", "versionCode='10'", "versionName='1.4.1'"]: assert expected in badging
certs=[re.search(r'certificate SHA-256 digest: (\w+)',(V/name).read_text()).group(1) for name in ['signature-before.txt','signature-after.txt']]
assert certs[0]==certs[1]
assert 'Verification successful' in (V/'zipalign.txt').read_text()
counts=dict(tests=0,failures=0,errors=0,skipped=0)
for p in sorted((R/'app/build/test-results/testCompactTestUnitTest').glob('TEST-*.xml')):
    elem=ET.parse(p).getroot()
    for key in counts: counts[key]+=int(elem.get(key,'0'))
    shutil.copy2(p,V/p.name)
assert counts['tests']>=77 and not any(counts[k] for k in ['failures','errors','skipped'])
changed=[]
with zipfile.ZipFile(O/'SparkTube-1.4.1-video-collapse-source.zip') as old:
    for name in old.namelist():
        rel=name.removeprefix('SparkTube-main/')
        if not rel.startswith('app/src/'): continue
        p=R/rel
        assert p.is_file()
        if p.read_bytes()!=old.read(name):
            changed.append(rel)
            (V/(p.name+'.diff')).write_text(''.join(difflib.unified_diff(old.read(name).decode().splitlines(True),p.read_text().splitlines(True),fromfile='before/'+rel,tofile='after/'+rel)))
oldbytes=(O/'SparkTube-1.4.1-video-collapse-test.apk').stat().st_size
summary={
    'versionName':'1.4.1','versionCode':10,
    'certificate_matches_previous_video_collapse_apk':True,
    'certificate_sha256':certs[1], 'jvm_tests':counts,
    'source_xml_checks':int(re.search(r'Ran (\d+) tests',checks).group(1)),
    'modified_existing_app_files':changed,
    'android_device_or_emulator_tested':False,
    'lint_completed':False,
    'lint_limit':'Offline lint dependencies unavailable; lintVital tasks excluded.',
    'apk_bytes':APK.stat().st_size,'previous_apk_bytes':oldbytes,
    'apk_size_delta_bytes':APK.stat().st_size-oldbytes,
    'apk_sha256':digest(APK),
    'timer_process_death_persistence':False,
    'video_to_audio_retains_source':True,
    'cold_music_to_video_may_resolve_online':True,
}
(V/'verification-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
shutil.copy2(R/'app/build/outputs/apk/compactTest/output-metadata.json',V/'output-metadata.json')
# Keep only useful final evidence, not superseded failure logs.
for name in ['regression-checks-initial.log','timer-checks.log']:
    (V/name).unlink(missing_ok=True)
shutil.copy2(APK,DEST)
excluded={'.git','.gradle','.kotlin','build','__pycache__'}
with zipfile.ZipFile(SRC,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(R.rglob('*')):
        rel=p.relative_to(R)
        if not p.is_file() or any(x in excluded for x in rel.parts): continue
        if rel.parts[0]=='verification' and 'sleep-timer' not in rel.parts: continue
        if p.name in {'local.properties','compile.log','.env'} or '.before.' in p.name or p.suffix in {'.jks','.keystore','.apk','.pem','.key'}: continue
        z.write(p,'SparkTube-main/'+str(rel))
with zipfile.ZipFile(SRC) as z:
    assert z.testzip() is None
    for p in (R/'app/src').rglob('*'):
        if p.is_file(): assert z.read('SparkTube-main/'+str(p.relative_to(R)))==p.read_bytes()
    assert z.read('SparkTube-main/SLEEP_TIMER_BN.md')==(R/'SLEEP_TIMER_BN.md').read_bytes()
assert digest(DEST)==digest(APK)
SUM.write_text(''.join(f'{digest(p)}  {p.name}\n' for p in [DEST,SRC]))
for p in [DEST,SRC,SUM]:
    assert p.is_file() and p.stat().st_size>0
    print(f'{p}: {p.stat().st_size} bytes')
print(json.dumps(summary,indent=2))
