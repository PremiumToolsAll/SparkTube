package com.sparktube.app.ui.player

import android.content.Context
import android.content.res.Configuration
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.ViewConfiguration
import androidx.media3.common.util.UnstableApi
import androidx.media3.ui.DefaultTimeBar

/** Native Media3 time bar, with a portrait-only deliberate-drag touch gate.
 * Keyboard and accessibility seeking retain Media3's implementation.
 */
@UnstableApi
class DeliberateSeekTimeBar @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : DefaultTimeBar(context, attrs, defStyleAttr, attrs,
    androidx.media3.ui.R.style.ExoStyledControls_TimeBar) {
    private val gate = SeekBarDragGate()
    private var pendingDown: MotionEvent? = null
    private var nativeDragging = false
    private var portraitSequence = false
    private val dragSlop = maxOf(ViewConfiguration.get(context).scaledTouchSlop.toFloat(),
        14f * resources.displayMetrics.density)

    // Read the same style as DefaultTimeBar. Its 48dp seekBounds are intentionally
    // NOT used: only the painted 2dp track or the current circular thumb qualify.
    private val touchStyle = context.obtainStyledAttributes(attrs,
        androidx.media3.ui.R.styleable.DefaultTimeBar, defStyleAttr,
        androidx.media3.ui.R.style.ExoStyledControls_TimeBar)
    private val trackHeight = touchStyle.getDimensionPixelSize(
        androidx.media3.ui.R.styleable.DefaultTimeBar_bar_height, dp(4))
    private val bottomGravity = touchStyle.getInt(
        androidx.media3.ui.R.styleable.DefaultTimeBar_bar_gravity, 0) == 1
    private val enabledThumbSize = touchStyle.getDimensionPixelSize(
        androidx.media3.ui.R.styleable.DefaultTimeBar_scrubber_enabled_size, dp(12))
    private val draggedThumbSize = touchStyle.getDimensionPixelSize(
        androidx.media3.ui.R.styleable.DefaultTimeBar_scrubber_dragged_size, dp(16))
    private val disabledThumbSize = touchStyle.getDimensionPixelSize(
        androidx.media3.ui.R.styleable.DefaultTimeBar_scrubber_disabled_size, 0)
    private val thumbInset = (maxOf(enabledThumbSize, draggedThumbSize, disabledThumbSize) + 1) / 2
    private var insetDisabled = false
    private var thumbReadyAt = 0L
    private var touchPositionMs = 0L
    private var touchDurationMs = 0L
    private var paintedTrack = SeekBarTouchGeometry(0, 0, 0, 0)

    init { touchStyle.recycle() }

    private fun dp(value: Int) = (value * resources.displayMetrics.density + 0.5f).toInt()

    override fun onLayout(changed: Boolean, left: Int, top: Int, right: Int, bottom: Int) {
        super.onLayout(changed, left, top, right, bottom)
        paintedTrack = SeekBarTouchGeometry.layout(width, height, paddingLeft, paddingRight,
            paddingBottom, trackHeight, if (insetDisabled) 0 else thumbInset, bottomGravity)
    }

    override fun setPosition(position: Long) {
        touchPositionMs = position
        super.setPosition(position)
    }

    override fun setDuration(duration: Long) {
        touchDurationMs = duration
        super.setDuration(duration)
    }

    override fun showScrubber() {
        insetDisabled = false
        thumbReadyAt = 0L
        super.showScrubber()
    }

    override fun showScrubber(animationDuration: Long) {
        insetDisabled = false
        // During scaling accept only the track, never a larger-than-painted thumb.
        thumbReadyAt = android.os.SystemClock.uptimeMillis() + animationDuration
        super.showScrubber(animationDuration)
    }

    override fun hideScrubber(disableScrubberPadding: Boolean) {
        insetDisabled = disableScrubberPadding
        thumbReadyAt = Long.MAX_VALUE
        super.hideScrubber(disableScrubberPadding)
    }

    override fun hideScrubber(animationDuration: Long) {
        thumbReadyAt = Long.MAX_VALUE
        super.hideScrubber(animationDuration)
    }

    /** Used by Activity routing too, so transparent padding remains video surface. */
    fun hitsVisibleSeekBar(x: Float, y: Float): Boolean {
        if (!isShown || !isEnabled || alpha <= 0f) return false
        val radius = if (android.os.SystemClock.uptimeMillis() >= thumbReadyAt)
            (if (isFocused) draggedThumbSize else enabledThumbSize) / 2 else 0
        return paintedTrack.contains(x, y, touchPositionMs, touchDurationMs, radius)
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (event.actionMasked == MotionEvent.ACTION_DOWN) {
            cancelPortraitSequence()
            portraitSequence = resources.configuration.orientation != Configuration.ORIENTATION_LANDSCAPE
        }
        // Exact native touch behavior for sequences started in landscape.
        if (!portraitSequence) return super.onTouchEvent(event)
        if (!isEnabled || resources.configuration.orientation == Configuration.ORIENTATION_LANDSCAPE) {
            cancelPortraitSequence()
            return true
        }
        when (event.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                gate.down(event.x, event.y, event.pointerCount == 1 && hitsVisibleSeekBar(event.x, event.y))
                if (gate.state == SeekBarDragGate.State.REJECTED) return false
                pendingDown = MotionEvent.obtain(event)
            }
            MotionEvent.ACTION_MOVE -> {
                if (event.pointerCount != 1) {
                    cancelPortraitSequence()
                    gate.reject()
                    return true
                }
                if (gate.move(event.x, event.y, dragSlop)) {
                    if (!nativeDragging) {
                        val down = pendingDown ?: return true
                        nativeDragging = super.onTouchEvent(down)
                        down.recycle()
                        pendingDown = null
                        if (!nativeDragging) gate.reject()
                    }
                    if (nativeDragging) super.onTouchEvent(event)
                }
            }
            MotionEvent.ACTION_POINTER_DOWN, MotionEvent.ACTION_POINTER_UP -> {
                cancelPortraitSequence()
                gate.reject()
            }
            MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {
                // No DOWN/UP is delivered for taps or rejected drags, so no
                // transient thumb jump, scrub listener, or playback seek occurs.
                if (nativeDragging) super.onTouchEvent(event)
                nativeDragging = false
                clearPending()
                gate.reset()
                portraitSequence = false
            }
        }
        return true
    }

    private fun clearPending() {
        pendingDown?.recycle()
        pendingDown = null
    }

    private fun cancelPortraitSequence() {
        if (nativeDragging) {
            val now = android.os.SystemClock.uptimeMillis()
            val cancel = MotionEvent.obtain(now, now, MotionEvent.ACTION_CANCEL, 0f, 0f, 0)
            super.onTouchEvent(cancel)
            cancel.recycle()
        }
        nativeDragging = false
        clearPending()
        gate.reset()
    }

    override fun onConfigurationChanged(newConfig: Configuration) {
        cancelPortraitSequence()
        // Keep an interrupted portrait sequence consumed until its UP/CANCEL;
        // never forward an orphan MOVE to the native landscape bar.
        super.onConfigurationChanged(newConfig)
    }

    override fun onDetachedFromWindow() {
        cancelPortraitSequence()
        super.onDetachedFromWindow()
    }
}
