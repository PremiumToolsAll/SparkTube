package com.sparktube.app.playback

import org.junit.Assert.*
import org.junit.Test

class SleepTimerStateTest {
    @Test fun durationCountsDownFromMonotonicTimeAndExpiresAtDeadline() {
        val timer = SleepTimerState()
        timer.setDuration(minutes = 2, nowMs = 10_000L)

        assertEquals(SleepTimerState.Mode.DURATION, timer.mode)
        assertEquals(130_000L, timer.deadlineMs)
        assertEquals(120_000L, timer.remainingMs(nowMs = 10_000L))
        // Wall-clock changes are irrelevant: callers only provide monotonic elapsed time.
        assertEquals(30_000L, timer.remainingMs(nowMs = 100_000L))
        assertFalse(timer.isExpired(nowMs = 129_999L))
        assertTrue(timer.isExpired(nowMs = 130_000L))
        assertEquals(0L, timer.remainingMs(nowMs = 130_001L))
    }

    @Test fun settingAnotherDurationReplacesThePreviousOne() {
        val timer = SleepTimerState()
        timer.setDuration(minutes = 10, nowMs = 5_000L)
        timer.setDuration(minutes = 3, nowMs = 20_000L)

        assertEquals(200_000L, timer.deadlineMs)
        assertEquals(180_000L, timer.remainingMs(nowMs = 20_000L))
    }

    @Test fun clearCancelsAnyTimer() {
        val timer = SleepTimerState()
        timer.setDuration(minutes = 1, nowMs = 0L)
        timer.clear()
        assertEquals(SleepTimerState.Mode.OFF, timer.mode)
        assertNull(timer.deadlineMs)
        assertNull(timer.remainingMs(nowMs = 60_000L))
        assertFalse(timer.isExpired(nowMs = Long.MAX_VALUE))

        timer.setEndOfItem("track-1")
        timer.clear()
        assertEquals(SleepTimerState.Mode.OFF, timer.mode)
        assertFalse(timer.shouldStopAtEnd("track-1"))
    }

    @Test fun durationMustBePositiveAndDeadlineAdditionCannotOverflow() {
        val timer = SleepTimerState()
        try {
            timer.setDuration(minutes = 0, nowMs = 0L)
            fail("Expected non-positive duration to be rejected")
        } catch (_: IllegalArgumentException) {
            // Expected.
        }

        timer.setDuration(minutes = Int.MAX_VALUE, nowMs = Long.MAX_VALUE - 1L)
        assertEquals(Long.MAX_VALUE, timer.deadlineMs)
    }

    @Test fun endOfItemIsBoundToCapturedItemAndMatchesItsNaturalEnd() {
        val timer = SleepTimerState()
        timer.setEndOfItem("track-1")

        assertEquals(SleepTimerState.Mode.END_OF_ITEM, timer.mode)
        assertNull(timer.deadlineMs)
        assertTrue(timer.shouldStopAtEnd("track-1"))
        assertFalse(timer.shouldStopAtEnd("track-2"))
        assertFalse(timer.shouldStopAtEnd(null))
        assertNull(timer.remainingMs(nowMs = 0L))
        assertFalse(timer.isExpired(nowMs = Long.MAX_VALUE))
    }

    @Test fun automaticTransitionAndRepeatStopButManualTransitionDoesNot() {
        val timer = SleepTimerState()
        timer.setEndOfItem("track-1")

        assertTrue(timer.shouldStopOnTransition(previousMediaId = "track-1", automatic = true))
        assertTrue(timer.shouldStopOnTransition(previousMediaId = "track-1", automatic = true)) // repeat
        assertFalse(timer.shouldStopOnTransition(previousMediaId = "track-1", automatic = false))
        assertFalse(timer.shouldStopOnTransition(previousMediaId = "track-2", automatic = true))
    }

    @Test fun settingOneModeReplacesTheOtherMode() {
        val timer = SleepTimerState()
        timer.setDuration(minutes = 1, nowMs = 100L)
        timer.setEndOfItem("track-1")
        assertNull(timer.deadlineMs)
        assertNull(timer.remainingMs(nowMs = 100L))
        assertTrue(timer.shouldStopAtEnd("track-1"))

        timer.setDuration(minutes = 1, nowMs = 100L)
        assertEquals(SleepTimerState.Mode.DURATION, timer.mode)
        assertFalse(timer.shouldStopAtEnd("track-1"))
    }
}
