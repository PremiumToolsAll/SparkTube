package com.sparktube.app.ui.player

import org.junit.Assert.*
import org.junit.Test

class SeekBarTouchGeometryTest {
    private val track = SeekBarTouchGeometry.layout(300, 48, 0, 0, 0, 2, 7, true)
    private fun hit(x: Float, y: Float, radius: Int = 5, position: Long = 50) =
        track.contains(x, y, position, 100, radius)

    @Test fun bottomTrackUsesThumbInsetNot48dpTouchTarget() {
        assertEquals(SeekBarTouchGeometry(7, 40, 293, 42), track)
    }
    @Test fun visibleTrackAcceptsDownAwayFromThumb() { assertTrue(hit(50f, 41f)) }
    @Test fun onePixelAboveTrackAwayFromThumbIsRejected() { assertFalse(hit(50f, 39f)) }
    @Test fun invisiblePaddingAboveTrackIsRejected() { assertFalse(hit(50f, 20f)) }
    @Test fun onePixelBelowTrackAwayFromThumbIsRejected() { assertFalse(hit(50f, 42f)) }
    @Test fun actualThumbExtendsAboveTrack() { assertTrue(hit(150f, 37f)) }
    @Test fun justOutsideThumbIsRejected() { assertFalse(hit(150f, 35f)) }
    @Test fun thumbUsesCircleNotExpandedRectangle() { assertFalse(hit(154f, 37f)) }
    @Test fun horizontalTrackPaddingIsRejected() { assertFalse(hit(2f, 41f)) }
    @Test fun thumbAtStartCanUsePaintedCircleInInset() { assertTrue(hit(3f, 41f, position = 0)) }
    @Test fun thumbAtEndCanUsePaintedCircleInInset() { assertTrue(hit(297f, 41f, position = 100)) }
    @Test fun hiddenThumbDoesNotAddTouchArea() { assertFalse(hit(150f, 37f, radius = 0)) }
    @Test fun unknownOrZeroDurationCannotScrub() {
        assertFalse(track.contains(50f, 41f, 0, 0, 5))
        assertFalse(track.contains(50f, 41f, 0, -1, 5))
    }
    @Test fun emptyTrackCannotScrub() {
        assertFalse(SeekBarTouchGeometry(10, 10, 10, 12).contains(10f, 11f, 50, 100, 5))
    }
    @Test fun highDensityStillRejectsAbovePaintedTrack() {
        val hd = SeekBarTouchGeometry.layout(900, 144, 0, 0, 0, 6, 21, true)
        assertEquals(SeekBarTouchGeometry(21, 120, 879, 126), hd)
        assertTrue(hd.contains(150f, 123f, 50, 100, 15))
        assertFalse(hd.contains(150f, 119f, 50, 100, 15))
    }
    @Test fun centerGravityMatchesNativeLayout() {
        assertEquals(SeekBarTouchGeometry(7, 23, 293, 25),
            SeekBarTouchGeometry.layout(300, 48, 0, 0, 0, 2, 7, false))
    }
    @Test fun noThumbPaddingMatchesMinimalLayout() {
        assertEquals(SeekBarTouchGeometry(0, 46, 300, 48),
            SeekBarTouchGeometry.layout(300, 48, 0, 0, 0, 2, 0, true))
    }
    @Test fun asymmetricPaddingAndOddSizesMatchNativeIntegerMath() {
        assertEquals(SeekBarTouchGeometry(15, 73, 300, 78),
            SeekBarTouchGeometry.layout(320, 90, 8, 13, 7, 5, 7, true))
    }
    @Test fun nonFiniteTouchCoordinatesRejected() {
        assertFalse(hit(Float.NaN, 41f))
        assertFalse(hit(150f, Float.POSITIVE_INFINITY))
    }
    @Test fun outsideDownThenMovingIntoTrackDoesNotScrub() {
        val gate = SeekBarDragGate()
        gate.down(50f, 39f, hit(50f, 39f))
        assertFalse(gate.move(100f, 41f, 14f))
        assertFalse(gate.move(200f, 41f, 14f))
    }
}
