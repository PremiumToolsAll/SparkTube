package com.sparktube.app.ui.common

import java.util.Locale

/** Decimal MB (1,000,000 bytes), never megabits or mislabeled binary MiB. */
internal object DownloadMetricFormat {
    fun megabytes(bytes: Long): String {
        val value = bytes.coerceAtLeast(0L)
        if (value in 1L..4_999L) return "<0.01 MB"
        return String.format(Locale.US, "%.2f MB", value.toDouble() / 1_000_000.0)
    }

    fun rate(bytesPerSecond: Double): String {
        val value = bytesPerSecond.takeIf { it.isFinite() && it > 0.0 } ?: 0.0
        if (value > 0.0 && value < 5_000.0) return "<0.01 MB/s"
        return String.format(Locale.US, "%.2f MB/s", value / 1_000_000.0)
    }

    fun duration(seconds: Long): String {
        val value = seconds.coerceAtLeast(0L)
        val hours = value / 3_600L
        val minutes = value % 3_600L / 60L
        val remainder = value % 60L
        return when {
            hours > 0 -> "$hours h $minutes min"
            minutes > 0 -> "$minutes min $remainder s"
            else -> "$remainder s"
        }
    }
}
