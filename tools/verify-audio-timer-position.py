#!/usr/bin/env python3
"""Static layout/scope regression checks; these do not execute Android UI."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LAYOUT = 'app/src/main/res/layout/activity_now_playing.xml'
ANDROID = '{http://schemas.android.com/apk/res/android}'

class AudioTimerPositionChecks(unittest.TestCase):
    def setUp(self):
        self.root = ET.parse(ROOT / LAYOUT).getroot()

    def test_timer_is_immediately_after_download(self):
        row = next(e for e in self.root.iter() if e.get(ANDROID+'id') == '@+id/actionsRow')
        self.assertEqual([e.get(ANDROID+'id') for e in row],
                         ['@+id/radioButton', '@+id/downloadButton', '@+id/timerButton'])
        self.assertEqual(row.get(ANDROID+'orientation'), 'horizontal')

    def test_timer_is_unique_and_favorite_remains(self):
        ids = [e.get(ANDROID+'id') for e in self.root.iter()]
        self.assertEqual(ids.count('@+id/timerButton'), 1)
        self.assertEqual(ids.count('@+id/favoriteButton'), 1)

    def test_action_columns_share_available_width(self):
        row = next(e for e in self.root.iter() if e.get(ANDROID+'id') == '@+id/actionsRow')
        for child in row:
            self.assertEqual(child.get(ANDROID+'layout_width'), '0dp')
            self.assertEqual(child.get(ANDROID+'layout_weight'), '1')

    def test_only_audio_layout_changed_from_sleep_timer_source(self):
        with zipfile.ZipFile(ROOT.parent/'SparkTube-1.4.1-sleep-timer-source.zip') as old:
            changed = []
            for name in old.namelist():
                rel = name.removeprefix('SparkTube-main/')
                if not rel.startswith('app/src/'):
                    continue
                current = ROOT / rel
                self.assertTrue(current.is_file(), rel)
                if current.read_bytes() != old.read(name):
                    changed.append(rel)
            self.assertEqual(changed, [LAYOUT])
            old_sources = {n.removeprefix('SparkTube-main/') for n in old.namelist() if n.startswith('SparkTube-main/app/src/')}
            current_sources = {str(p.relative_to(ROOT)) for p in (ROOT/'app/src').rglob('*') if p.is_file()}
            self.assertEqual(old_sources, current_sources)
            self.assertEqual((ROOT/'app/build.gradle.kts').read_bytes(), old.read('SparkTube-main/app/build.gradle.kts'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
