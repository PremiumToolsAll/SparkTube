package com.sparktube.app.ui.player

/** Touch-only gate: taps never reach Media3, a clear horizontal drag does. */
internal class SeekBarDragGate {
    enum class State { IDLE, PENDING, DRAGGING, REJECTED }
    var state = State.IDLE
        private set
    private var startX = 0f
    private var startY = 0f

    fun down(x: Float, y: Float, onVisibleBar: Boolean = true) {
        startX = x
        startY = y
        state = if (onVisibleBar) State.PENDING else State.REJECTED
    }

    fun move(x: Float, y: Float, slop: Float): Boolean {
        if (state == State.PENDING) {
            val dx = x - startX
            val dy = y - startY
            // Once meaningful non-horizontal movement starts, this sequence
            // cannot become a scrub later by wandering sideways into the bar.
            if (maxOf(kotlin.math.abs(dx), kotlin.math.abs(dy)) >= slop) {
                state = if (PlayerGestureMath.chooseAxis(dx, dy, slop) == PlayerGestureMath.Axis.HORIZONTAL)
                    State.DRAGGING else State.REJECTED
            }
        }
        return state == State.DRAGGING
    }

    fun reset() { state = State.IDLE }
    fun reject() { state = State.REJECTED }
}
