package com.sparktube.app.playback

/** Main-thread PiP ownership. Late callbacks from a retired page cannot clear a new owner. */
internal class PipSessionState<T : Any> {
    private var owner: T? = null
    private var closeOwner: (() -> Unit)? = null
    val active: Boolean get() = owner != null

    fun claim(candidate: T, onClose: () -> Unit) {
        if (owner !== candidate) close()
        owner = candidate
        closeOwner = onClose
    }

    fun release(candidate: T) {
        if (owner !== candidate) return
        owner = null
        closeOwner = null
    }

    fun close() {
        val close = closeOwner
        // Clear before invoking Android lifecycle code: finish can re-enter callbacks.
        owner = null
        closeOwner = null
        close?.invoke()
    }
}
