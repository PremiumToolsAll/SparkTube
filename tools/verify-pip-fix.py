#!/usr/bin/env python3
"""Static regression checks only; these do not exercise Android rendering."""
from pathlib import Path
import unittest
import zipfile
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent / 'SparkTube-1.4.1-audio-downloads-source.zip'
ACTIVITY = 'app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt'
SOURCE = (ROOT / ACTIVITY).read_text()
def section(start, end):
    return SOURCE.split(start, 1)[1].split(end, 1)[0]
class PipFixChecks(unittest.TestCase):
    def test_no_output_detach_on_pause(self):
        self.assertNotIn('override fun onPause()', SOURCE)
    def test_visible_start_and_resume_attach(self):
        for start, end in [('override fun onStart()', 'override fun onResume()'), ('override fun onResume()', '// ----- Close animation -----')]:
            body = section(start, end)
            self.assertIn('PlaybackCenter.attachView(binding.playerView)', body)
            self.assertNotIn('if (!isInPictureInPictureMode)', body)
    def test_stop_and_destroy_detach(self):
        body = section('override fun onStop()', '// ----- PiP -----')
        self.assertEqual(body.count('PlaybackCenter.detachView(binding.playerView)'), 2)
        self.assertIn('PlaybackCenter.inPip = false', body)
    def test_pip_callback_recovers_surface_and_restores_controls(self):
        body = section('override fun onPictureInPictureModeChanged(', 'private fun applyPipLayout()')
        self.assertIn('if (isInPictureInPictureMode) PlaybackCenter.attachView(binding.playerView)', body)
        self.assertIn('binding.playerView.useController = !isInPictureInPictureMode', body)
        self.assertIn('applyOrientation(newConfig)', body)
        self.assertIn('if (!isInPictureInPictureMode) binding.playerView.showController()', body)
    def test_configuration_gives_pip_priority(self):
        body = section('private fun applyOrientation(config: Configuration)', '// ----- Binding -----')
        self.assertLess(body.index('applyPipLayout()'), body.index('val landscape'))
        self.assertIn('applyPipLayout()\n            return', body)
    def test_pip_video_fills_window_without_page_or_insets(self):
        body = section('private fun applyPipLayout()', '// ----- Orientation -----')
        for text in ['height = ViewGroup.LayoutParams.MATCH_PARENT', 'dimensionRatio = null', 'topMargin = 0', 'RESIZE_MODE_FIT', 'binding.scrollArea.isVisible = false', 'binding.playerView.hideController()']:
            self.assertIn(text, body)
    def test_only_player_activity_changed_since_latest_source(self):
        changed = []
        with zipfile.ZipFile(BASE) as archive:
            for name in archive.namelist():
                rel = name.removeprefix('SparkTube-main/')
                if not (rel.startswith('app/src/') or rel.startswith('app/libs/') or rel.endswith('.gradle.kts') or rel == 'gradle.properties'):
                    continue
                path = ROOT / rel
                if not path.is_file() or path.read_bytes() != archive.read(name):
                    changed.append(rel)
        self.assertEqual(changed, [ACTIVITY])
    def test_manifest_and_xml(self):
        for path in (ROOT / 'app/src/main').rglob('*.xml'):
            ET.parse(path)
        ns = '{http://schemas.android.com/apk/res/android}'
        manifest = ET.parse(ROOT / 'app/src/main/AndroidManifest.xml')
        player = next(e for e in manifest.iter('activity') if e.get(ns+'name') == '.ui.player.PlayerActivity')
        self.assertEqual(player.get(ns+'supportsPictureInPicture'), 'true')
        config = player.get(ns+'configChanges').split('|')
        self.assertTrue({'orientation', 'screenSize', 'smallestScreenSize', 'screenLayout'} <= set(config))
if __name__ == '__main__':
    unittest.main(verbosity=2)
