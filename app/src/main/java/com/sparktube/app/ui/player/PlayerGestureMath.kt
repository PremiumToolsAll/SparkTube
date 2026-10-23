package com.sparktube.app.ui.player

/** Pure calculations shared by touch handling and local JVM regression tests. */
internal object PlayerGestureMath {
    enum class Axis { NONE, HORIZONTAL, VERTICAL }

    /** Intentional surface seeks work in either orientation, never across a rotation. */
    fun canSeekVideoSurface(startedInLandscape: Boolean, isLandscape: Boolean): Boolean =
        startedInLandscape == isLandscape

    /** Do not promote an unrelated diagonal portrait drag into a surface seek. */
    fun rejectAmbiguousPortraitMovement(startedInLandscape: Boolean, dx: Float, dy: Float, slop: Float): Boolean =
        !startedInLandscape && maxOf(kotlin.math.abs(dx), kotlin.math.abs(dy)) >= slop &&
            chooseAxis(dx, dy, slop) == Axis.NONE

    /** Lock only after meaningful movement, preferring the clearly dominant axis. */
    fun chooseAxis(dx: Float, dy: Float, slop: Float, dominance: Float = 1.3f): Axis {
        val x = kotlin.math.abs(dx)
        val y = kotlin.math.abs(dy)
        if (maxOf(x, y) < slop) return Axis.NONE
        return when {
            x > y * dominance -> Axis.HORIZONTAL
            y > x * dominance -> Axis.VERTICAL
            else -> Axis.NONE
        }
    }

    /** Horizontal seek: 120 dp of travel corresponds to a 10-second seek. */
    fun horizontalSeekTarget(positionMs: Long, durationMs: Long, deltaX: Float, pixelsPerTenSeconds: Float): Long {
        if (durationMs <= 0L || pixelsPerTenSeconds <= 0f) return positionMs.coerceAtLeast(0L)
        val current = positionMs.coerceIn(0L, durationMs)
        val delta = (deltaX.toDouble() / pixelsPerTenSeconds * 10_000.0).toLong()
        return (current.toDouble() + delta.toDouble()).coerceIn(0.0, durationMs.toDouble()).toLong()
    }

    fun seekTarget(positionMs: Long, durationMs: Long, forward: Boolean): Long {
        if (durationMs <= 0L) return positionMs.coerceAtLeast(0L)
        val current = positionMs.coerceIn(0L, durationMs)
        return if (forward) current + minOf(10_000L, durationMs - current)
        else (current - 10_000L).coerceAtLeast(0L)
    }

    fun volume(initial: Int, fraction: Float, max: Int): Int =
        (initial + fraction * max.coerceAtLeast(0)).toInt().coerceIn(0, max.coerceAtLeast(0))

    fun brightness(initial: Float, fraction: Float): Float =
        (initial + fraction).coerceIn(0.01f, 1f)
}
