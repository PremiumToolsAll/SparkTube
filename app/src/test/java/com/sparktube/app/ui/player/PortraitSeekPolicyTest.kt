package com.sparktube.app.ui.player

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PortraitSeekPolicyTest {
    @Test fun portraitIntentionalSurfaceGesturesRemainEnabled() {
        assertTrue(PlayerGestureMath.canSeekVideoSurface(false, false))
    }

    @Test fun landscapeSurfaceGesturesRemainEnabled() {
        assertTrue(PlayerGestureMath.canSeekVideoSurface(true, true))
    }

    @Test fun rotatingToPortraitCannotCommitLandscapeSeek() {
        assertFalse(PlayerGestureMath.canSeekVideoSurface(true, false))
    }

    @Test fun rotatingToLandscapeCannotPromotePortraitDragToSeek() {
        assertFalse(PlayerGestureMath.canSeekVideoSurface(false, true))
    }

    @Test fun ambiguousPortraitMovementIsRejected() {
        assertTrue(PlayerGestureMath.rejectAmbiguousPortraitMovement(false, 20f, 20f, 14f))
    }

    @Test fun landscapeAxisArbitrationIsUnchanged() {
        assertFalse(PlayerGestureMath.rejectAmbiguousPortraitMovement(true, 20f, 20f, 14f))
    }

    @Test fun clearPortraitSwipeIsNotRejected() {
        assertFalse(PlayerGestureMath.rejectAmbiguousPortraitMovement(false, 24f, 3f, 14f))
    }

    @Test fun portraitJitterDoesNotLockOutLaterIntentionalSwipe() {
        assertFalse(PlayerGestureMath.rejectAmbiguousPortraitMovement(false, 5f, 5f, 14f))
    }
}
