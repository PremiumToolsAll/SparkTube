package com.sparktube.app.ui.music

import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.view.Gravity
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import com.google.android.material.bottomsheet.BottomSheetBehavior
import com.google.android.material.bottomsheet.BottomSheetDialog
import com.sparktube.app.R
import com.sparktube.app.playback.PlaybackCenter
import com.sparktube.app.playback.SleepTimerState
import java.util.Locale

/** Same selector for the music screen and the video action row. */
class SleepTimerSheet(context: Context) : BottomSheetDialog(context) {
    private fun dp(n: Int) = (n * context.resources.displayMetrics.density).toInt()
    private val green = context.getColor(R.color.music_green)
    private val textColor = context.getColor(R.color.on_surface)
    private val root = LinearLayout(context).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(0, dp(10), 0, dp(16))
        background = GradientDrawable().apply {
            setColor(context.getColor(R.color.sheet_bg))
            cornerRadii = floatArrayOf(dp(24).toFloat(), dp(24).toFloat(), dp(24).toFloat(), dp(24).toFloat(), 0f, 0f, 0f, 0f)
            setStroke(dp(1), green)
        }
    }
    private val listener = object : PlaybackCenter.Listener {
        override fun onSleepTimerExpired() { dismiss() }
        override fun onItemChanged(entry: com.sparktube.app.playback.QueueEntry?) { dismiss() }
    }

    init {
        root.addView(android.view.View(context).apply {
            background = context.getDrawable(R.drawable.bg_sheet_handle)
        }, LinearLayout.LayoutParams(dp(36), dp(4)).apply { gravity = Gravity.CENTER_HORIZONTAL; bottomMargin = dp(12) })
        root.addView(TextView(context).apply {
            text = context.getString(R.string.sleep_timer_title)
            textSize = 22f
            setTextColor(textColor)
            setTypeface(typeface, Typeface.BOLD)
            setPadding(dp(22), dp(8), dp(22), dp(16))
        })
        root.addView(android.view.View(context).apply { setBackgroundColor(context.getColor(R.color.outline)) }, LinearLayout.LayoutParams(-1, dp(1)))
        val rows = LinearLayout(context).apply { orientation = LinearLayout.VERTICAL }
        val mode = PlaybackCenter.sleepTimerMode
        addRow(rows, context.getString(R.string.sleep_timer_off), R.drawable.ic_close, mode == SleepTimerState.Mode.OFF) {
            PlaybackCenter.clearSleepTimer()
        }
        for (minutes in listOf(10, 15, 20, 30, 45, 60)) {
            val label = if (minutes == 60) context.getString(R.string.sleep_timer_hour)
                else context.getString(R.string.sleep_timer_minutes, minutes)
            addRow(rows, label, R.drawable.ic_sleep_timer,
                mode == SleepTimerState.Mode.DURATION && PlaybackCenter.sleepTimerMinutes == minutes) {
                PlaybackCenter.setSleepTimer(minutes)
            }
        }
        val remaining = (PlaybackCenter.durationMs - PlaybackCenter.positionMs).coerceAtLeast(0)
        val end = context.getString(R.string.sleep_timer_end)
        addRow(rows, if (PlaybackCenter.durationMs > 0) "$end (${formatRemaining(remaining)})" else end,
            R.drawable.ic_sleep_timer, mode == SleepTimerState.Mode.END_OF_ITEM) {
            PlaybackCenter.setSleepTimerEndOfItem()
        }
        val scroll = ScrollView(context).apply { isFillViewport = false; addView(rows) }
        root.addView(scroll, LinearLayout.LayoutParams(-1, -2))
        setContentView(root)
        behavior.skipCollapsed = true
        setOnShowListener {
            (root.parent as? android.view.View)?.setBackgroundColor(Color.TRANSPARENT)
            root.layoutParams = root.layoutParams.apply {
                height = minOf(root.measuredHeight, (context.resources.displayMetrics.heightPixels * 0.86f).toInt())
            }
            behavior.state = BottomSheetBehavior.STATE_EXPANDED
        }
    }

    private fun addRow(parent: LinearLayout, label: String, icon: Int, selected: Boolean, action: () -> Unit) {
        val tint = if (selected) green else textColor
        val row = LinearLayout(context).apply {
            gravity = Gravity.CENTER_VERTICAL
            orientation = LinearLayout.HORIZONTAL
            minimumHeight = dp(48)
            setPadding(dp(22), dp(14), dp(22), dp(14))
            isClickable = true
            isFocusable = true
            isSelected = selected
            contentDescription = if (selected) context.getString(R.string.sleep_timer_selected, label) else label
            val out = android.util.TypedValue()
            context.theme.resolveAttribute(android.R.attr.selectableItemBackground, out, true)
            setBackgroundResource(out.resourceId)
            setOnClickListener { action(); dismiss() }
        }
        row.addView(ImageView(context).apply { setImageResource(icon); setColorFilter(tint); importantForAccessibility = android.view.View.IMPORTANT_FOR_ACCESSIBILITY_NO }, LinearLayout.LayoutParams(dp(24), dp(24)))
        row.addView(TextView(context).apply { text = label; textSize = 18f; setTextColor(tint); setPadding(dp(20), 0, dp(8), 0) }, LinearLayout.LayoutParams(0, -2, 1f))
        row.addView(ImageView(context).apply {
            setImageResource(R.drawable.ic_check); setColorFilter(green)
            visibility = if (selected) android.view.View.VISIBLE else android.view.View.INVISIBLE
            importantForAccessibility = android.view.View.IMPORTANT_FOR_ACCESSIBILITY_NO
        }, LinearLayout.LayoutParams(dp(24), dp(24)))
        parent.addView(row, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))
    }

    override fun onStart() { super.onStart(); PlaybackCenter.addListener(listener) }
    override fun onStop() { PlaybackCenter.removeListener(listener); super.onStop() }

    companion object {
        private fun formatRemaining(ms: Long): String {
            val seconds = (ms.coerceAtLeast(0) + 999) / 1000
            return String.format(Locale.getDefault(), "%d:%02d", seconds / 60, seconds % 60)
        }
        fun buttonLabel(context: Context): String = when (PlaybackCenter.sleepTimerMode) {
            SleepTimerState.Mode.OFF -> context.getString(R.string.sleep_timer_button)
            SleepTimerState.Mode.DURATION -> formatRemaining(PlaybackCenter.sleepTimerRemainingMs ?: 0)
            SleepTimerState.Mode.END_OF_ITEM -> context.getString(R.string.sleep_timer_end_countdown,
                formatRemaining((PlaybackCenter.durationMs - PlaybackCenter.positionMs).coerceAtLeast(0)))
        }
        fun accessibilityLabel(context: Context): String = context.getString(R.string.sleep_timer_accessibility, buttonLabel(context))
    }
}
