#!/usr/bin/env python3
"""Verify/package matching test APK and editable source; not a device test."""
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
V = R/'verification/compact-controls-bottom-seek'
B = O/'android-sdk/build-tools/36.0.0'
APK = R/'app/build/outputs/apk/compactTest/app-compactTest.apk'
PREVIOUS = O/'SparkTube-1.4.1-clean-player-overlay-test.apk'
DEST = O/'SparkTube-1.4.1-compact-controls-bottom-seek-test.apk'
SRC = O/'SparkTube-1.4.1-compact-controls-bottom-seek-source.zip'
SUM = O/'SHA256SUMS-SparkTube-1.4.1-compact-controls-bottom-seek.txt'

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
# Read the compiled portrait/default values, not source/XML assumptions.
aapt2 = command([B/'aapt2', 'dump', 'resources', APK], 'apk-resources-aapt2.txt')
match = re.search(r'resource \S+ dimen/exo_styled_progress_margin_bottom\n((?:[ \t]+.*\n)+)', aapt2)
assert match, 'Missing merged Media3 progress dimension'
entry = match.group(1)
assert re.search(r'\(\)\s+52(?:\.0+)?dp', entry), entry
assert re.search(r'\(port\)\s+0(?:\.0+)?dp', entry), entry
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
    'certificate_matches_previous_clean_player_overlay_apk': True,
    'certificate_sha256': certificates[1],
    'jvm_tests': counts, 'source_regression_checks': 7,
    'visible_disc_insets_dp': 10,
    'transport_touch_targets_and_icon_sizes_unchanged': True,
    'portrait_progress_bottom_margin_dp': 0,
    'landscape_progress_default_bottom_margin_dp': 52,
    'portrait_resource_override_verified_in_compiled_apk': True,
    'portrait_bottom_bar_transparent': True,
    'portrait_bottom_row_above_seek_touch_target': True,
    'landscape_controller_xml_and_original_z_order_preserved': True,
    'clean_autohiding_arrow_preserved': True,
    'audio_download_timer_placement_and_playback_logic_byte_identical': True,
    'android_device_or_emulator_tested': False,
    'lint_completed': False,
    'lint_limit': 'Offline lint-gradle:31.6.1 dependency unavailable in prior baseline; lint vital tasks excluded. No lint pass claimed.',
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
        if rel.parts[0] == 'verification' and 'compact-controls-bottom-seek' not in rel.parts:
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
