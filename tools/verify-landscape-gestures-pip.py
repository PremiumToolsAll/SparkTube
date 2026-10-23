#!/usr/bin/env python3
"""Static regression tests only; these do not simulate an Android device."""
from pathlib import Path
import importlib.util
import unittest
import zipfile

R = Path(__file__).resolve().parents[1]
P = 'app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt'
p = (R/P).read_text()
spec = importlib.util.spec_from_file_location('previous_checks', R/'tools/verify-landscape-brightness-pip.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

class LandscapeGestureChecks(previous.RegressionChecks):
    def test_only_intended_app_files_changed(self):
        with zipfile.ZipFile(R.parent/'SparkTube-1.4.1-landscape-brightness-pip-source.zip') as z:
            old = {n.removeprefix('SparkTube-main/'): z.read(n) for n in z.namelist() if n.startswith('SparkTube-main/app/src/')}
            current = {str(f.relative_to(R)): f.read_bytes() for f in (R/'app/src').rglob('*') if f.is_file()}
            self.assertEqual(set(old), set(current))
            self.assertEqual({n for n in old if old[n] != current[n]}, {P})
            restored = p.replace(
                '                // Side brightness and volume adjustments are landscape only.\n'
                '                if (resources.configuration.orientation != Configuration.ORIENTATION_LANDSCAPE) return true\n', '', 1)
            restored = restored.replace(
                '                } else {\n                    val brightness = PlayerGestureMath.brightness',
                '                } else {\n'
                '                    // Left-side brightness adjustment is fullscreen/landscape only.\n'
                '                    if (resources.configuration.orientation != Configuration.ORIENTATION_LANDSCAPE) return true\n'
                '                    val brightness = PlayerGestureMath.brightness', 1)
            self.assertEqual(restored.encode(), old[P])
            for rel in ['app/build.gradle.kts', 'build.gradle.kts', 'gradle.properties', 'app/src/main/AndroidManifest.xml']:
                self.assertEqual((R/rel).read_bytes(), z.read('SparkTube-main/'+rel))

    def test_shared_guard_precedes_both_media_level_branches(self):
        block = p[p.index('override fun onScroll'):p.index('hookGearMenu()')]
        guard = block.index('if (resources.configuration.orientation != Configuration.ORIENTATION_LANDSCAPE) return true')
        self.assertLess(block.index('pendingSeekTarget = PlayerGestureMath.horizontalSeekTarget'), guard)
        self.assertLess(block.index('if (totalY < -dp(100)) finish()'), guard)
        for operation in ['val fraction =', 'if (start.x >= width / 2f)', 'audio.setStreamVolume', 'R.string.gesture_volume', 'PlayerGestureMath.brightness', 'screenBrightness = brightness', 'R.string.gesture_brightness']:
            self.assertLess(guard, block.index(operation))
        self.assertEqual(block.count('Configuration.ORIENTATION_LANDSCAPE'), 1)

if __name__ == '__main__':
    unittest.main(verbosity=2)
