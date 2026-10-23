package com.sparktube.app.playback

/** Playback can be READY because of audio alone; only a rendered frame proves video output. */
internal object VideoFramePolicy {
    const val TIMEOUT_MS = 8_000L
    enum class Action { WAIT, REBIND_OUTPUT, RETRY_SOURCE, SHOW_ERROR }

    fun action(visibleWaitMs: Long, firstFrameSeen: Boolean, recoveryStep: Int): Action {
        if (firstFrameSeen || visibleWaitMs < TIMEOUT_MS) return Action.WAIT
        return when (recoveryStep) {
            0 -> Action.REBIND_OUTPUT
            1 -> Action.RETRY_SOURCE
            else -> Action.SHOW_ERROR
        }
    }
}
