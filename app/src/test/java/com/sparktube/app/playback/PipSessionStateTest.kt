package com.sparktube.app.playback

import org.junit.Assert.*
import org.junit.Test

class PipSessionStateTest {
    @Test fun replacementClosesTheActualOwnerExactlyOnce() {
        val state = PipSessionState<Any>()
        var closes = 0
        state.claim(Any()) { closes++ }
        assertTrue(state.active)
        state.close()
        state.close()
        assertFalse(state.active)
        assertEquals(1, closes)
    }

    @Test fun lateExitFromOldPageDoesNotClearNewPip() {
        val state = PipSessionState<Any>()
        val old = Any()
        val fresh = Any()
        var oldCloses = 0
        var freshCloses = 0
        state.claim(old) { oldCloses++ }
        state.close()
        state.claim(fresh) { freshCloses++ }
        state.release(old)
        assertTrue(state.active)
        assertEquals(1, oldCloses)
        assertEquals(0, freshCloses)
        state.close()
        assertEquals(1, freshCloses)
    }

    @Test fun repeatedCallbacksForSameOwnerDoNotFinishIt() {
        val state = PipSessionState<Any>()
        val owner = Any()
        var closes = 0
        repeat(3) { state.claim(owner) { closes++ } }
        assertTrue(state.active)
        assertEquals(0, closes)
        state.release(owner)
        state.close()
        assertFalse(state.active)
        assertEquals(0, closes)
    }

    @Test fun claimingDifferentOwnerClosesOldOwnerBeforeInstallingNewOne() {
        val state = PipSessionState<Any>()
        val old = Any()
        val fresh = Any()
        var closed = false
        state.claim(old) {
            assertFalse(state.active)
            state.release(old)
            closed = true
        }
        state.claim(fresh) { }
        assertTrue(closed)
        assertTrue(state.active)
        state.release(old)
        assertTrue(state.active)
    }

    @Test fun identityRatherThanEqualityProtectsNewOwner() {
        data class Owner(val name: String)
        val state = PipSessionState<Owner>()
        val old = Owner("player")
        val fresh = Owner("player")
        state.claim(fresh) { }
        state.release(old)
        assertTrue(state.active)
        state.release(fresh)
        assertFalse(state.active)
    }

    @Test fun clearingBeforeCloseAllowsReentrantNewSession() {
        val state = PipSessionState<Any>()
        val fresh = Any()
        state.claim(Any()) { state.claim(fresh) { } }
        state.close()
        assertTrue(state.active)
        state.release(fresh)
        assertFalse(state.active)
    }
}
