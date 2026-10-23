package com.sparktube.app.playback

/** Pure state for playback sleep timers. Time values are monotonic milliseconds supplied by the caller. */
class SleepTimerState {
    enum class Mode { OFF, DURATION, END_OF_ITEM }

    var mode: Mode = Mode.OFF
        private set

    /** Monotonic deadline for [Mode.DURATION], otherwise null. */
    var deadlineMs: Long? = null
        private set

    private var endOfItemMediaId: String? = null

    /** Starts or replaces a duration timer. Valid minutes are positive Int values. */
    fun setDuration(minutes: Int, nowMs: Long) {
        require(minutes > 0) { "minutes must be positive" }
        val durationMs = minutes.toLong() * MILLIS_PER_MINUTE
        // Saturation is defensive for unusual caller-supplied clocks; normal elapsedRealtime values fit.
        deadlineMs = if (nowMs > Long.MAX_VALUE - durationMs) Long.MAX_VALUE else nowMs + durationMs
        mode = Mode.DURATION
        endOfItemMediaId = null
    }

    /** Stops at the end of the item whose ID is captured now (including automatic repeat). */
    fun setEndOfItem(mediaId: String?) {
        mode = Mode.END_OF_ITEM
        deadlineMs = null
        endOfItemMediaId = mediaId
    }

    fun clear() {
        mode = Mode.OFF
        deadlineMs = null
        endOfItemMediaId = null
    }

    /** Remaining duration, clamped to zero; null unless a duration timer is active. */
    fun remainingMs(nowMs: Long): Long? =
        if (mode == Mode.DURATION) ((deadlineMs!! - nowMs).coerceAtLeast(0L)) else null

    fun isExpired(nowMs: Long): Boolean =
        mode == Mode.DURATION && nowMs >= deadlineMs!!

    /** True only when the item reaching its end is the item captured by END_OF_ITEM. */
    fun shouldStopAtEnd(mediaId: String?): Boolean =
        mode == Mode.END_OF_ITEM && mediaId == endOfItemMediaId

    /** Stops before an automatic transition (including repeat) out of the captured item. */
    fun shouldStopOnTransition(previousMediaId: String?, automatic: Boolean): Boolean =
        automatic && mode == Mode.END_OF_ITEM && previousMediaId == endOfItemMediaId

    private companion object {
        const val MILLIS_PER_MINUTE = 60_000L
    }
}
