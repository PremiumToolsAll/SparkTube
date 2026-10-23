#!/usr/bin/env python3
"""Compare APK ZIP payloads and defined DEX classes without external packages.

Usage: python3 tools/apk-size-audit.py OLD.apk NEW.apk [REPORT.json]
This is a static preservation check, not a device/runtime test.
"""
import collections
import hashlib
import json
from pathlib import Path
import struct
import sys
import zipfile


def u32(data, offset):
    return struct.unpack_from('<I', data, offset)[0]


def uleb(data, offset):
    value = shift = 0
    while True:
        byte = data[offset]
        offset += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, offset
        shift += 7


def dex_classes(data):
    if not data.startswith(b'dex\n'):
        raise ValueError('Unsupported DEX header')
    string_count, string_offset = struct.unpack_from('<II', data, 56)
    strings = []
    for i in range(string_count):
        pos = u32(data, string_offset + 4 * i)
        _, pos = uleb(data, pos)
        strings.append(data[pos:data.index(b'\0', pos)].decode('utf-8', errors='replace'))
    type_count, type_offset = struct.unpack_from('<II', data, 64)
    types = [strings[u32(data, type_offset + 4 * i)] for i in range(type_count)]
    count, offset = struct.unpack_from('<II', data, 96)
    return {types[u32(data, offset + 32 * i)] for i in range(count)}


def inspect(path):
    groups = collections.defaultdict(lambda: {'entries': 0, 'raw_bytes': 0, 'compressed_bytes': 0})
    classes = set()
    payloads = {}
    dex_entries = []
    with zipfile.ZipFile(path) as apk:
        if apk.testzip() is not None:
            raise ValueError('Corrupt ZIP: ' + str(path))
        for entry in apk.infolist():
            name = entry.filename
            is_dex = name.endswith('.dex') and '/' not in name
            group = 'DEX' if is_dex else name.split('/')[0]
            groups[group]['entries'] += 1
            groups[group]['raw_bytes'] += entry.file_size
            groups[group]['compressed_bytes'] += entry.compress_size
            data = apk.read(name)
            if is_dex:
                classes.update(dex_classes(data))
                dex_entries.append(name)
            elif name != 'AndroidManifest.xml' and not name.upper().startswith('META-INF/'):
                payloads[name] = hashlib.sha256(data).hexdigest()
    return {
        'path': str(path),
        'bytes': Path(path).stat().st_size,
        'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        'dex_entries': dex_entries,
        'defined_class_count': len(classes),
        'groups': dict(groups),
    }, classes, payloads


def main():
    if len(sys.argv) not in (3, 4):
        raise SystemExit(__doc__)
    before, before_classes, before_payloads = inspect(sys.argv[1])
    after, after_classes, after_payloads = inspect(sys.argv[2])
    report = {
        'before': before,
        'after': after,
        'saved_bytes': before['bytes'] - after['bytes'],
        'reduction_percent': round((1 - after['bytes'] / before['bytes']) * 100, 4),
        'missing_defined_classes': sorted(before_classes - after_classes),
        'added_defined_classes': sorted(after_classes - before_classes),
        'missing_non_code_payloads': sorted(before_payloads.keys() - after_payloads.keys()),
        'added_non_code_payloads': sorted(after_payloads.keys() - before_payloads.keys()),
        'changed_non_code_payloads': sorted(k for k in before_payloads.keys() & after_payloads.keys()
                                            if before_payloads[k] != after_payloads[k]),
        'note': 'Manifest/signing are checked separately. Class presence does not prove runtime equivalence. D8 may change compiler-generated synthetic classes between modes.',
    }
    text = json.dumps(report, indent=2, ensure_ascii=False) + '\n'
    if len(sys.argv) == 4:
        Path(sys.argv[3]).write_text(text)
    print(text, end='')


if __name__ == '__main__':
    main()
