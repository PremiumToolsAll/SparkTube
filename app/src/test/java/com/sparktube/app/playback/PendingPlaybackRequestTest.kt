package com.sparktube.app.playback

import org.junit.Assert.*
import org.junit.Test

class PendingPlaybackRequestTest {
    @Test fun startsInactive() {
        assertFalse(PendingPlaybackRequest().active)
    }

    @Test fun selectingNextRequestsPlaybackImmediately() {
        val request = PendingPlaybackRequest()
        request.begin()
        assertTrue(request.active)
        assertTrue(request.playWhenReady)
    }

    @Test fun pauseDuringResolutionIsPreservedUntilCompletion() {
        val request = PendingPlaybackRequest()
        val token = request.begin()
        request.setPlayWhenReady(false)
        assertFalse(request.playWhenReady)
        assertTrue(request.complete(token))
        assertFalse(request.active)
        assertFalse(request.playWhenReady)
    }

    @Test fun repeatedTapsToggleIntentEvenWithoutPlayingFrames() {
        val request = PendingPlaybackRequest()
        request.begin()
        repeat(5) { request.setPlayWhenReady(!request.playWhenReady) }
        assertFalse(request.playWhenReady)
        request.setPlayWhenReady(!request.playWhenReady)
        assertTrue(request.playWhenReady)
    }

    @Test fun staleResolveCannotEndNewerSelection() {
        val request = PendingPlaybackRequest()
        val first = request.begin()
        val second = request.begin()
        request.setPlayWhenReady(false)
        assertFalse(request.complete(first))
        assertTrue(request.active)
        assertFalse(request.playWhenReady)
        assertTrue(request.complete(second))
        assertFalse(request.active)
    }

    @Test fun cancelledRequestCannotAffectReplacement() {
        val request = PendingPlaybackRequest()
        val first = request.begin()
        request.cancel()
        assertFalse(request.active)
        assertFalse(request.complete(first))
        val second = request.begin()
        assertFalse(request.complete(first))
        assertTrue(request.complete(second))
    }

    @Test fun newSelectionResetsPreviousPauseAsExistingNextBehaviorDoes() {
        val request = PendingPlaybackRequest()
        request.begin()
        request.setPlayWhenReady(false)
        request.begin()
        assertTrue(request.playWhenReady)
    }

    @Test fun completionIsIdempotent() {
        val request = PendingPlaybackRequest()
        val token = request.begin()
        assertTrue(request.complete(token))
        assertFalse(request.complete(token))
    }
}
