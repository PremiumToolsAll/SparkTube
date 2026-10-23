package com.sparktube.app.ui.player

/** Pixel geometry of the painted Media3 track, not its larger invisible touch target. */
internal data class SeekBarTouchGeometry(
    val left: Int, val top: Int, val right: Int, val bottom: Int
) {
    fun contains(x: Float, y: Float, positionMs: Long, durationMs: Long, thumbRadius: Int): Boolean {
        if (right <= left || bottom <= top || durationMs <= 0 || !x.isFinite() || !y.isFinite()) return false
        if (x >= left && x < right && y >= top && y < bottom) return true
        if (thumbRadius <= 0) return false
        // Match DefaultTimeBar's integer progress position and circle center.
        val thumbX = left + ((right - left).toLong() * positionMs.coerceIn(0, durationMs) / durationMs).toInt()
        val thumbY = (top + bottom) / 2
        val dx = x - thumbX
        val dy = y - thumbY
        return dx * dx + dy * dy <= thumbRadius.toFloat() * thumbRadius
    }

    companion object {
        /** Matches DefaultTimeBar 1.3.1 onLayout, including bottom gravity and thumb inset. */
        fun layout(width: Int, height: Int, paddingLeft: Int, paddingRight: Int,
                   paddingBottom: Int, barHeight: Int, scrubberPadding: Int, bottomGravity: Boolean): SeekBarTouchGeometry {
            val top = if (bottomGravity) height - paddingBottom - barHeight -
                maxOf(scrubberPadding - barHeight / 2, 0) else (height - barHeight) / 2
            return SeekBarTouchGeometry(paddingLeft + scrubberPadding, top,
                width - paddingRight - scrubberPadding, top + barHeight)
        }
    }
}
