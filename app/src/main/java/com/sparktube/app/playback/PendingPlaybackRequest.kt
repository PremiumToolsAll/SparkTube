package com.sparktube.app.playback

/** User intent while a video URL is resolving; stale jobs may not clear a newer request. */
internal class PendingPlaybackRequest {
    private var generation = 0L
    var active = false
        private set
    var playWhenReady = true
        private set

    fun begin(): Long {
        generation++
        active = true
        playWhenReady = true
        return generation
    }

    fun setPlayWhenReady(value: Boolean) {
        playWhenReady = value
    }

    fun complete(token: Long): Boolean {
        if (token != generation || !active) return false
        active = false
        return true
    }

    fun cancel() {
        generation++
        active = false
    }
}
