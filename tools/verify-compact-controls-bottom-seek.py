#!/usr/bin/env python3
"""Static regression checks only; these do not execute Android UI."""
from pathlib import Path
import unittest
import zipfile
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[1]
P = 'app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt'
D = 'app/src/main/res/drawable/bg_transport_circle.xml'
Q = 'app/src/main/res/values-port/dimens_player.xml'
A = '{http://schemas.android.com/apk/res/android}'
TEXT = (R/P).read_text()

class CompactControlsChecks(unittest.TestCase):
    def test_exact_app_change_scope(self):
        with zipfile.ZipFile(R.parent/'SparkTube-1.4.1-clean-player-overlay-source.zip') as z:
            old = {n.removeprefix('SparkTube-main/'): z.read(n) for n in z.namelist() if n.startswith('SparkTube-main/app/src/')}
            current = {str(p.relative_to(R)): p.read_bytes() for p in (R/'app/src').rglob('*') if p.is_file()}
            self.assertEqual(set(current) - set(old), {Q})
            self.assertFalse(set(old) - set(current))
            self.assertEqual({n for n in old if old[n] != current[n]}, {P, D})
            for rel in ['app/build.gradle.kts', 'build.gradle.kts', 'gradle.properties', 'app/src/main/AndroidManifest.xml']:
                self.assertEqual((R/rel).read_bytes(), z.read('SparkTube-main/'+rel))

    def test_original_landscape_controller_and_touch_sizes_unchanged(self):
        with zipfile.ZipFile(R.parent/'SparkTube-1.4.1-clean-player-overlay-source.zip') as z:
            for rel in ['app/src/main/res/layout/player_queue_controller.xml', 'app/src/main/res/layout/activity_player.xml']:
                self.assertEqual((R/rel).read_bytes(), z.read('SparkTube-main/'+rel))
        root = ET.parse(R/'app/src/main/res/layout/activity_player.xml')
        sizes = {'queuePrevious': '52dp', 'queuePlayPause': '76dp', 'queueNext': '52dp'}
        for node in root.iter():
            name = node.get(A+'id', '').removeprefix('@+id/')
            if name in sizes:
                self.assertEqual(node.get(A+'layout_width'), sizes[name])
                self.assertEqual(node.get(A+'layout_height'), sizes[name])

    def test_smaller_visible_discs(self):
        root = ET.parse(R/D).getroot()
        item = root.find('item')
        for edge in ['left', 'top', 'right', 'bottom']:
            self.assertEqual(item.get(A+edge), '10dp')
        self.assertEqual(item.find('shape').get(A+'shape'), 'oval')
        self.assertEqual(item.find('shape/solid').get(A+'color'), '#66000000')

    def test_dimension_override_only_in_portrait(self):
        overrides = []
        for p in (R/'app/src/main/res').glob('values*/*.xml'):
            for node in ET.parse(p).getroot():
                if node.get('name') == 'exo_styled_progress_margin_bottom':
                    overrides.append((str(p.relative_to(R)), node.text))
        self.assertEqual(overrides, [(Q, '0dp')])
        self.assertIn('bottomMargin = resources.getDimensionPixelSize(Media3R.dimen.exo_styled_progress_margin_bottom)', TEXT)
        self.assertIn('if (landscape) 0f else dp(1).toFloat()', TEXT)

    def test_player_logic_only_has_orientation_styling_addition(self):
        start = TEXT.index('        // The portrait-only dimension')
        end = TEXT.index('        binding.fullscreenButton.setImageResource(', start)
        with zipfile.ZipFile(R.parent/'SparkTube-1.4.1-clean-player-overlay-source.zip') as z:
            self.assertEqual(TEXT[:start] + TEXT[end:], z.read('SparkTube-main/'+P).decode())

    def test_clean_autohiding_arrow_and_strip_preserved(self):
        root = ET.parse(R/'app/src/main/res/layout/activity_player.xml')
        arrow = next(e for e in root.iter() if e.get(A+'id') == '@+id/backButton')
        self.assertEqual(arrow.get(A+'background'), '@android:color/transparent')
        self.assertIn('binding.backButton.isVisible = visible', TEXT)
        self.assertIn('if (landscape) Media3R.color.exo_bottom_bar_background else android.R.color.transparent', TEXT)
        self.assertIn('controllerVisible = visibility == View.VISIBLE', TEXT)

    def test_audio_layout_and_all_playback_features_byte_identical(self):
        with zipfile.ZipFile(R.parent/'SparkTube-1.4.1-clean-player-overlay-source.zip') as z:
            for name in z.namelist():
                rel = name.removeprefix('SparkTube-main/')
                if rel.startswith('app/src/') and rel not in {P, D}:
                    self.assertEqual((R/rel).read_bytes(), z.read(name), rel)

if __name__ == '__main__':
    unittest.main(verbosity=2)
