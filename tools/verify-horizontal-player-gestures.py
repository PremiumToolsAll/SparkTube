#!/usr/bin/env python3
"""Focused structural checks for horizontal player seeking and existing gestures."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLAYER = ROOT / "app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt"
MATH = ROOT / "app/src/main/java/com/sparktube/app/ui/player/PlayerGestureMath.kt"
TEST = ROOT / "app/src/test/java/com/sparktube/app/ui/player/PlayerGestureMathTest.kt"


class HorizontalPlayerGestureTest(unittest.TestCase):
    def test_axis_lock_and_seek_preview_commit(self):
        player, math = PLAYER.read_text(), MATH.read_text()
        self.assertIn("PlayerGestureMath.chooseAxis(totalX, totalY, dp(14).toFloat())", player)
        self.assertIn("gestureAxis == PlayerGestureMath.Axis.HORIZONTAL", player)
        self.assertIn("pendingSeekTarget = PlayerGestureMath.horizontalSeekTarget", player)
        self.assertIn("pendingSeekTarget?.let(PlaybackCenter::seekTo)", player)
        self.assertIn("event.actionMasked == MotionEvent.ACTION_UP", player)
        self.assertIn("enum class Axis { NONE, HORIZONTAL, VERTICAL }", math)

    def test_vertical_volume_brightness_and_doubletap_remain(self):
        player = PLAYER.read_text()
        self.assertIn("PlaybackCenter.seekTo(PlayerGestureMath.seekTarget", player)
        self.assertIn("PlayerGestureMath.volume(gestureStartVolume, fraction, max)", player)
        self.assertIn("PlayerGestureMath.brightness(gestureStartBrightness, fraction)", player)
        self.assertIn("if (totalY < -dp(100)) finish()", player)
        self.assertIn("hitsPlayerControl(binding.root", player)

    def test_math_regressions_cover_slop_scaling_and_clamps(self):
        tests = TEST.read_text()
        self.assertIn("axisWaitsForSlopAndLocksOnlyForDominantDirection", tests)
        self.assertIn("horizontalSwipeSeeksProportionallyInBothDirections", tests)
        self.assertIn("horizontalSeekClampsToDurationAndStartAndIgnoresUnknownDuration", tests)


if __name__ == "__main__":
    unittest.main(verbosity=2)
