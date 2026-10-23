#!/usr/bin/env python3
"""Source regression checks, not Android runtime/UI tests."""
from pathlib import Path
import unittest
import zipfile

R = Path(__file__).resolve().parents[1]
P = 'app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt'
C = 'app/src/main/java/com/sparktube/app/playback/PlaybackCenter.kt'
S = 'app/src/main/java/com/sparktube/app/playback/PipSessionState.kt'
T = 'app/src/test/java/com/sparktube/app/playback/PipSessionStateTest.kt'
p = (R/P).read_text()
c = (R/C).read_text()

class RegressionChecks(unittest.TestCase):
    def test_only_intended_app_files_changed(self):
        with zipfile.ZipFile(R.parent/'SparkTube-1.4.1-compact-controls-bottom-seek-source.zip') as z:
            old = {n.removeprefix('SparkTube-main/'): z.read(n) for n in z.namelist() if n.startswith('SparkTube-main/app/src/')}
            current = {str(f.relative_to(R)): f.read_bytes() for f in (R/'app/src').rglob('*') if f.is_file()}
            self.assertEqual(set(current)-set(old), {S, T})
            self.assertFalse(set(old)-set(current))
            self.assertEqual({n for n in old if old[n] != current[n]}, {P, C})
            for rel in ['app/build.gradle.kts', 'build.gradle.kts', 'gradle.properties', 'app/src/main/AndroidManifest.xml']:
                self.assertEqual((R/rel).read_bytes(), z.read('SparkTube-main/'+rel))

    def test_brightness_is_guarded_before_write_and_feedback(self):
        start = p.index('// Side brightness and volume adjustments')
        end = p.index('return true', p.index('R.string.gesture_brightness', start))
        branch = p[start:end]
        guard = branch.index('if (resources.configuration.orientation != Configuration.ORIENTATION_LANDSCAPE) return true')
        self.assertLess(guard, branch.index('PlayerGestureMath.brightness'))
        self.assertLess(guard, branch.index('screenBrightness = brightness'))
        self.assertIn('screenBrightness = WindowManager.LayoutParams.BRIGHTNESS_OVERRIDE_NONE', p)

    def test_all_explicit_replacements_close_before_stopping_player(self):
        for func, nextfunc in [('fun playVideo(', 'fun playPlaylist('), ('fun playPlaylist(', 'fun playMusic('), ('fun playMusicQueue(', 'fun playQueueIndex(')]:
            block = c[c.index(func):c.index(nextfunc)]
            self.assertLess(block.index('closePreviousPip()'), block.index('stopPlayerNow()'))
        self.assertLess(p.index('PlaybackCenter.closePreviousPip()'), p.index('binding = ActivityPlayerBinding.inflate'))

    def test_retired_activity_cannot_reclaim_surface(self):
        for name in ['onStart', 'onResume', 'onUserLeaveHint', 'onPictureInPictureModeChanged']:
            start = p.index('override fun '+name)
            end = p.index('\n    }', start)
            self.assertIn('if (retiringPip || isFinishing) return', p[start:end])
        block = p[p.index('private fun closeReplacedPip()'):p.index('override fun onUserLeaveHint')]
        for text in ['retiringPip = true', 'PlaybackCenter.removeListener(playbackListener)', 'PlaybackCenter.detachView(binding.playerView)', 'finish()']:
            self.assertIn(text, block)
        self.assertNotIn('stopPlayback()', block)
        self.assertNotIn('pause()', block)

    def test_no_unowned_global_pip_writes(self):
        for file in (R/'app/src/main').rglob('*.kt'):
            self.assertNotIn('PlaybackCenter.inPip =', file.read_text())
        self.assertIn('val inPip: Boolean get() = pipSession.active', c)
        self.assertIn('if (activePlayerView !== view) return', c)
        stopped = p[p.index('override fun onStop()'):p.index('override fun onDestroy()')]
        self.assertIn('if (!isInPictureInPictureMode || isFinishing || retiringPip)', stopped)

    def test_existing_controls_and_gestures_preserved(self):
        with zipfile.ZipFile(R.parent/'SparkTube-1.4.1-compact-controls-bottom-seek-source.zip') as z:
            old = z.read('SparkTube-main/'+P).decode()
            for begin, end in [('override fun onDoubleTap', 'override fun onScroll'), ('val totalY =', 'val width = binding.playerView.width'), ('if (start.x >= width / 2f)', '} else {')]:
                def segment(s):
                    a = s.index(begin)
                    return s[a:s.index(end, a)]
                self.assertEqual(segment(p), segment(old))
        self.assertIn('if (landscape) 0f else dp(1).toFloat()', p)
        self.assertIn('binding.backButton.isVisible = visible', p)

    def test_automatic_queue_advance_does_not_close_pip(self):
        block = c[c.index('fun playQueueIndex('):c.index('fun togglePlayPause(')]
        self.assertNotIn('closePreviousPip', block)
        block = c[c.index('private fun resolveCurrent('):]
        self.assertNotIn('closePreviousPip()', block)

if __name__ == '__main__':
    unittest.main(verbosity=2)
