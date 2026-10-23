package com.sparktube.app.ui.player

import org.junit.Assert.assertEquals
import org.junit.Test

class PlayerGestureMathTest {
    @Test fun axisWaitsForSlopAndLocksOnlyForDominantDirection() {
        assertEquals(PlayerGestureMath.Axis.NONE, PlayerGestureMath.chooseAxis(9f, 1f, 10f))
        assertEquals(PlayerGestureMath.Axis.HORIZONTAL, PlayerGestureMath.chooseAxis(30f, 10f, 10f))
        assertEquals(PlayerGestureMath.Axis.VERTICAL, PlayerGestureMath.chooseAxis(10f, -30f, 10f))
        assertEquals(PlayerGestureMath.Axis.NONE, PlayerGestureMath.chooseAxis(20f, 16f, 10f))
    }

    @Test fun horizontalSwipeSeeksProportionallyInBothDirections() {
        assertEquals(40_000L, PlayerGestureMath.horizontalSeekTarget(30_000L, 120_000L, 120f, 120f))
        assertEquals(20_000L, PlayerGestureMath.horizontalSeekTarget(30_000L, 120_000L, -120f, 120f))
        assertEquals(35_000L, PlayerGestureMath.horizontalSeekTarget(30_000L, 120_000L, 60f, 120f))
    }

    @Test fun horizontalSeekClampsToDurationAndStartAndIgnoresUnknownDuration() {
        assertEquals(0L, PlayerGestureMath.horizontalSeekTarget(2_000L, 90_000L, -120f, 120f))
        assertEquals(90_000L, PlayerGestureMath.horizontalSeekTarget(87_000L, 90_000L, 120f, 120f))
        assertEquals(2_000L, PlayerGestureMath.horizontalSeekTarget(2_000L, 0L, 120f, 120f))
    }

    @Test fun doubleTapRightSeeksTenSeconds() {
        assertEquals(30_000L, PlayerGestureMath.seekTarget(20_000L, 90_000L, true))
    }
    @Test fun doubleTapLeftSeeksTenSeconds() {
        assertEquals(10_000L, PlayerGestureMath.seekTarget(20_000L, 90_000L, false))
    }
    @Test fun seekCannotPassStartOrEnd() {
        assertEquals(0L, PlayerGestureMath.seekTarget(2_000L, 90_000L, false))
        assertEquals(90_000L, PlayerGestureMath.seekTarget(87_000L, 90_000L, true))
    }
    @Test fun unknownDurationDoesNotJump() {
        assertEquals(2_000L, PlayerGestureMath.seekTarget(2_000L, 0L, true))
    }
    @Test fun hugeDurationDoesNotOverflow() {
        assertEquals(Long.MAX_VALUE, PlayerGestureMath.seekTarget(Long.MAX_VALUE - 5, Long.MAX_VALUE, true))
    }
    @Test fun volumeClampsAndMovesBothDirections() {
        assertEquals(10, PlayerGestureMath.volume(5, 0.5f, 10))
        assertEquals(0, PlayerGestureMath.volume(5, -2f, 10))
        assertEquals(10, PlayerGestureMath.volume(5, 2f, 10))
        assertEquals(0, PlayerGestureMath.volume(5, 2f, 0))
    }
    @Test fun brightnessNeverBlacksOutScreen() {
        assertEquals(0.01f, PlayerGestureMath.brightness(0.5f, -2f), 0.001f)
        assertEquals(1f, PlayerGestureMath.brightness(0.5f, 2f), 0.001f)
        assertEquals(0.75f, PlayerGestureMath.brightness(0.5f, 0.25f), 0.001f)
    }
}
