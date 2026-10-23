package com.sparktube.app.ui.player

import org.junit.Assert.*
import org.junit.Test

class SeekBarDragGateTest {
    private val gate = SeekBarDragGate()
    private fun down() = gate.down(100f, 20f)

    @Test fun tapDoesNotStartScrubbing() {
        down()
        assertEquals(SeekBarDragGate.State.PENDING, gate.state)
        gate.reset()
        assertEquals(SeekBarDragGate.State.IDLE, gate.state)
    }
    @Test fun smallJitterDoesNotStartScrubbing() {
        down()
        assertFalse(gate.move(108f, 23f, 14f))
    }
    @Test fun horizontalDragRightStartsScrubbing() {
        down()
        assertTrue(gate.move(120f, 22f, 14f))
    }
    @Test fun horizontalDragLeftStartsScrubbing() {
        down()
        assertTrue(gate.move(80f, 22f, 14f))
    }
    @Test fun verticalDragIsRejected() {
        down()
        assertFalse(gate.move(103f, 40f, 14f))
        assertEquals(SeekBarDragGate.State.REJECTED, gate.state)
    }
    @Test fun verticalThenHorizontalCannotBecomeScrub() {
        down()
        gate.move(103f, 40f, 14f)
        assertFalse(gate.move(200f, 20f, 14f))
    }
    @Test fun ambiguousDiagonalIsRejected() {
        down()
        assertFalse(gate.move(120f, 40f, 14f))
        assertFalse(gate.move(220f, 40f, 14f))
    }
    @Test fun ownershipStaysWithRecognizedHorizontalDrag() {
        down()
        gate.move(120f, 22f, 14f)
        assertTrue(gate.move(100f, 80f, 14f))
    }
    @Test fun cancelResetsAndDoesNotResumeWithoutDown() {
        down()
        gate.move(120f, 22f, 14f)
        gate.reset()
        assertFalse(gate.move(180f, 22f, 14f))
    }
    @Test fun multiTouchRejectionCannotResume() {
        down()
        gate.reject()
        assertFalse(gate.move(180f, 22f, 14f))
    }
    @Test fun freshDownClearsRejectedState() {
        down()
        gate.reject()
        down()
        assertTrue(gate.move(120f, 22f, 14f))
    }
    @Test fun belowSlopDoesNotLockAxisPrematurely() {
        down()
        assertFalse(gate.move(105f, 26f, 14f))
        assertTrue(gate.move(120f, 24f, 14f))
    }
    @Test fun downOutsidePaintedTrackCannotStartScrub() {
        gate.down(100f, 10f, false)
        assertFalse(gate.move(150f, 10f, 14f))
        assertEquals(SeekBarDragGate.State.REJECTED, gate.state)
    }
    @Test fun enteringTrackAfterOutsideDownCannotTakeOwnership() {
        gate.down(100f, 10f, false)
        assertFalse(gate.move(105f, 40f, 14f))
        assertFalse(gate.move(200f, 40f, 14f))
    }
    @Test fun freshInsideDownAfterOutsideRejectionCanScrub() {
        gate.down(100f, 10f, false)
        gate.reset()
        gate.down(100f, 40f, true)
        assertTrue(gate.move(125f, 40f, 14f))
    }
}
