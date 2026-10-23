#!/usr/bin/env python3
"""Source/XML regression checks, not Android UI or playback tests."""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'app/src/main'
PLAYER = (SRC / 'java/com/sparktube/app/ui/player/PlayerActivity.kt').read_text()
AUDIO = (SRC / 'java/com/sparktube/app/ui/music/NowPlayingActivity.kt').read_text()
A = '{http://schemas.android.com/apk/res/android}'
APP = '{http://schemas.android.com/apk/res-auto}'
LAYOUT = ET.parse(SRC / 'res/layout/activity_player.xml')
BUTTON = next(e for e in LAYOUT.iter() if e.get(A + 'id') == '@+id/backButton')

class VideoCollapseChecks(unittest.TestCase):
    def test_same_finish_only_action_as_audio(self):
        for text in (PLAYER, AUDIO):
            self.assertIn('binding.backButton.setOnClickListener { finish() }', text)

    def test_same_down_chevron_as_audio(self):
        audio = ET.parse(SRC / 'res/layout/activity_now_playing.xml')
        button = next(e for e in audio.iter() if e.get(A + 'id') == '@+id/backButton')
        for attr in ('src', 'rotation', 'layout_width', 'layout_height'):
            self.assertEqual(BUTTON.get(A + attr), button.get(A + attr))

    def test_visible_accessible_button(self):
        self.assertNotIn(BUTTON.get(A + 'visibility'), ('gone', 'invisible'))
        self.assertEqual(BUTTON.get(A + 'contentDescription'), '@string/collapse_video_player')
        strings = ET.parse(SRC / 'res/values/strings_player_controls.xml')
        self.assertTrue(any(e.get('name') == 'collapse_video_player' and e.text for e in strings.getroot()))

    def test_button_anchored_inside_video(self):
        for attr in ('layout_constraintStart_toStartOf', 'layout_constraintTop_toTopOf'):
            self.assertEqual(BUTTON.get(APP + attr), '@id/playerView')
        self.assertEqual(BUTTON.get(A + 'layout_marginTop'), '4dp')

    def test_controller_hiding_does_not_hide_collapse(self):
        body = PLAYER.split('private fun syncFullscreenButtonVisibility()', 1)[1].split('/** Latest top inset', 1)[0]
        self.assertIn('binding.backButton.isVisible = !isInPictureInPictureMode', body)
        self.assertIn('binding.transportControls.isVisible = visible', body)

    def test_pip_hides_button_and_exit_restores_it(self):
        body = PLAYER.split('private fun applyPipLayout()', 1)[1].split('// ----- Orientation', 1)[0]
        self.assertIn('binding.backButton.isVisible = false', body)
        orientation = PLAYER.split('private fun applyOrientation(config: Configuration)', 1)[1].split('// ----- Binding', 1)[0]
        self.assertIn('applyPipLayout()', orientation)
        self.assertIn('syncFullscreenButtonVisibility()', orientation)

    def test_insets_not_double_applied(self):
        body = PLAYER.split('binding.backButton.updateLayoutParams', 1)[1].split('binding.fullscreenButton', 1)[0]
        self.assertIn('topMargin = dp(4) + if (resources.configuration.orientation == Configuration.ORIENTATION_LANDSCAPE) bars.top else 0', body)
        self.assertIn('marginStart = dp(4) + startInset', body)

    def test_touch_dispatch_preserves_button_taps(self):
        self.assertIn('!hitsPlayerControl(binding.root, event.rawX.toInt(), event.rawY.toInt())', PLAYER)
        self.assertIn('view is android.widget.ImageButton', PLAYER)
        self.assertEqual(BUTTON.tag, 'ImageButton')

    def test_finish_does_not_stop_or_change_playback(self):
        body = PLAYER.split('override fun finish()', 1)[1].split('// Do NOT detach', 1)[0]
        self.assertIn('super.finish()', body)
        self.assertIn('R.anim.slide_down_out', body)
        self.assertNotIn('PlaybackCenter.', body)

    def test_latest_scope_preserves_other_features_build_and_libraries(self):
        baseline = ROOT.parent / 'SparkTube-1.4.1-notification-audio-source.zip'
        if not baseline.exists():
            self.skipTest('Historical source ZIP required only for change-scope audit')
        allowed = {
            'app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt',
            'app/src/main/res/layout/activity_player.xml',
            'app/src/main/res/values/strings_player_controls.xml',
        }
        tracked = lambda rel: rel.startswith(('app/src/', 'app/libs/')) or rel.endswith('.gradle.kts') or rel == 'gradle.properties'
        with zipfile.ZipFile(baseline) as old:
            names = {n.removeprefix('SparkTube-main/'): n for n in old.namelist()}
            changed = {rel for rel, name in names.items() if tracked(rel) and (not (ROOT / rel).is_file() or (ROOT / rel).read_bytes() != old.read(name))}
            added = {str(p.relative_to(ROOT)) for p in (ROOT / 'app').rglob('*') if p.is_file() and tracked(str(p.relative_to(ROOT)))} - set(names)
        self.assertEqual(changed, allowed)
        self.assertFalse(added)

if __name__ == '__main__':
    unittest.main(verbosity=2)
