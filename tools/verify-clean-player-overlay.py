#!/usr/bin/env python3
"""Source regression checks only: not Android runtime/UI tests."""
from pathlib import Path
import unittest
import zipfile
import xml.etree.ElementTree as ET

R = Path(__file__).resolve().parents[1]
P = 'app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt'
TEXT = (R/P).read_text()

class CleanOverlayChecks(unittest.TestCase):
    def test_only_player_activity_changed_from_latest(self):
        with zipfile.ZipFile(R.parent/'SparkTube-1.4.1-audio-timer-position-source.zip') as z:
            names = {n.removeprefix('SparkTube-main/'): n for n in z.namelist() if n.startswith('SparkTube-main/app/src/')}
            current = {str(p.relative_to(R)) for p in (R/'app/src').rglob('*') if p.is_file()}
            self.assertEqual(current, set(names))
            changed = {rel for rel, name in names.items() if (R/rel).read_bytes() != z.read(name)}
            self.assertEqual(changed, {P, 'app/src/main/res/layout/activity_player.xml'})
            for rel in ['app/build.gradle.kts', 'build.gradle.kts', 'gradle.properties', 'app/src/main/AndroidManifest.xml']:
                self.assertEqual((R/rel).read_bytes(), z.read('SparkTube-main/'+rel))

    def test_clean_arrow_only_layout_change(self):
        rel = 'app/src/main/res/layout/activity_player.xml'
        with zipfile.ZipFile(R.parent/'SparkTube-1.4.1-audio-timer-position-source.zip') as z:
            old = z.read('SparkTube-main/'+rel).decode()
        expected = old.replace(
            'android:background="@drawable/bg_icon_scrim"\n        android:contentDescription="@string/collapse_video_player"',
            'android:background="@android:color/transparent"\n        android:contentDescription="@string/collapse_video_player"'
        )
        self.assertEqual((R/rel).read_text(), expected)
        a = '{http://schemas.android.com/apk/res/android}'
        button = next(e for e in ET.parse(R/rel).iter() if e.get(a+'id') == '@+id/backButton')
        self.assertEqual(button.get(a+'background'), '@android:color/transparent')
        self.assertEqual(button.get(a+'src'), '@drawable/ic_chevron_right')
        self.assertEqual(button.get(a+'rotation'), '90')
        self.assertIsNone(button.get(a+'elevation'))

    def test_collapse_and_transport_share_visibility(self):
        body = TEXT.split('private fun syncFullscreenButtonVisibility()', 1)[1].split('/** Latest top inset', 1)[0]
        self.assertIn('val visible = !isInPictureInPictureMode && controllerVisible', body)
        for view in ['backButton', 'transportControls', 'fullscreenButton', 'modeSwitch']:
            self.assertIn(f'binding.{view}.isVisible = visible', body)
        self.assertIn('controllerVisible = visibility == View.VISIBLE', TEXT)
        listener = TEXT.split('override fun onVisibilityChanged', 1)[1].split('Watch-page chrome', 1)[0]
        self.assertIn('syncFullscreenButtonVisibility()', listener)

    def test_single_and_double_taps_preserved(self):
        body = TEXT.split('override fun onSingleTapConfirmed', 1)[1].split('override fun onDoubleTap', 1)[0]
        self.assertIn('if (binding.playerView.isControllerFullyVisible) binding.playerView.hideController()', body)
        self.assertIn('else binding.playerView.showController()', body)
        self.assertIn('PlaybackCenter.seekTo(PlayerGestureMath.seekTarget', TEXT)
        self.assertIn('if (!view.isShown) return false', TEXT)
        self.assertIn('view is android.widget.ImageButton', TEXT)
        self.assertIn('binding.backButton.setOnClickListener { finish() }', TEXT)

    def test_background_switches_on_each_orientation_application(self):
        body = TEXT.split('private fun applyOrientation(config: Configuration)', 1)[1].split('// ----- Binding', 1)[0]
        self.assertIn('val landscape = config.orientation == Configuration.ORIENTATION_LANDSCAPE', body)
        self.assertIn('findViewById<View>(Media3R.id.exo_bottom_bar)?.setBackgroundResource(', body)
        self.assertIn('if (landscape) Media3R.color.exo_bottom_bar_background else android.R.color.transparent', body)
        self.assertIn('applyOrientation(resources.configuration)', TEXT)
        self.assertIn('override fun onConfigurationChanged(newConfig: Configuration)', TEXT)
        self.assertIn('applyOrientation(newConfig)', TEXT)

    def test_pip_and_restore_still_hide_reveal_controls(self):
        body = TEXT.split('private fun applyPipLayout()', 1)[1].split('// ----- Orientation', 1)[0]
        self.assertIn('binding.backButton.isVisible = false', body)
        self.assertIn('binding.playerView.hideController()', body)
        self.assertIn('if (!isInPictureInPictureMode) binding.playerView.showController()', TEXT)

    def test_no_unrelated_logic_modified(self):
        with zipfile.ZipFile(R.parent/'SparkTube-1.4.1-audio-timer-position-source.zip') as z:
            old = z.read('SparkTube-main/'+P).decode()
        expected = old.replace(
            '/** Fullscreen + scale buttons follow the built-in controller\'s visibility. */',
            '/** All overlay buttons follow the built-in controller\'s visibility. */'
        ).replace(
            '// Collapse stays reachable even when the transport/seek controls auto-hide.\n        binding.backButton.isVisible = !isInPictureInPictureMode',
            '// Single-tap reveal and auto-hide apply to collapse just like transport.\n        binding.backButton.isVisible = visible'
        ).replace(
            '        val landscape = config.orientation == Configuration.ORIENTATION_LANDSCAPE\n',
            '        val landscape = config.orientation == Configuration.ORIENTATION_LANDSCAPE\n'
            '        // This activity handles rotation without reinflating the controller.\n'
            '        // Clear only the portrait bottom strip; restore Media3\'s original\n'
            '        // background in landscape without changing seek layout or behavior.\n'
            '        binding.playerView.findViewById<View>(Media3R.id.exo_bottom_bar)?.setBackgroundResource(\n'
            '            if (landscape) Media3R.color.exo_bottom_bar_background else android.R.color.transparent\n'
            '        )\n'
        )
        self.assertEqual(TEXT, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)
