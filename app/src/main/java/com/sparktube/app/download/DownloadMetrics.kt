package com.sparktube.app.download

/** Pure transfer metrics helpers; time values are monotonic nanoseconds. */
data class DownloadMetrics(
    val downloadedBytes: Long,
    val totalBytes: Long?,
    val bytesPerSecond: Double,
    val remainingSeconds: Long?
) {
    val progressPercent: Int
        get() = totalBytes?.takeIf { it > 0L }
            ?.let { (downloadedBytes.coerceAtLeast(0L).coerceAtMost(it).toDouble() / it.toDouble() * 100.0).toInt().coerceIn(0, 100) }
            ?: 0
}

/**
 * Samples cumulative byte-counter updates, not UI getter calls. A gap with no
 * transfer updates is considered a stall and reports zero speed.
 */
internal class DownloadSpeedSampler(
    private val minSampleNanos: Long = 250_000_000L,
    private val staleAfterNanos: Long = 1_500_000_000L
) {
    private var lastBytes = 0L
    private var lastUpdateNanos: Long? = null
    private var rate = 0.0

    @Synchronized
    fun onBytes(cumulativeBytes: Long, nowNanos: Long) {
        // Parallel writers may reach this monitor out of counter-update order.
        if (cumulativeBytes < lastBytes) return
        val previousTime = lastUpdateNanos
        if (previousTime != null && nowNanos > previousTime) {
            val elapsed = nowNanos - previousTime
            if (elapsed >= minSampleNanos) {
                rate = ((cumulativeBytes - lastBytes).coerceAtLeast(0L)).toDouble() * 1_000_000_000.0 / elapsed
                lastBytes = cumulativeBytes
                lastUpdateNanos = nowNanos
                return
            }
        }
        if (previousTime == null) {
            lastBytes = cumulativeBytes
            lastUpdateNanos = nowNanos
        }
    }

    @Synchronized
    fun bytesPerSecond(nowNanos: Long): Double =
        if (lastUpdateNanos == null || nowNanos - lastUpdateNanos!! > staleAfterNanos) 0.0 else rate

    @Synchronized
    fun reset(nowNanos: Long, cumulativeBytes: Long = 0L) {
        lastBytes = cumulativeBytes
        lastUpdateNanos = nowNanos
        rate = 0.0
    }
}

internal fun calculateDownloadMetrics(
    downloadedBytes: Long,
    totals: List<Long?>,
    bytesPerSecond: Double
): DownloadMetrics {
    val validTotals = totals.filterNotNull().filter { it > 0L }
    // Any missing component makes the aggregate total unknown.
    val total = if (totals.isNotEmpty() && totals.all { it != null && it > 0L }) validTotals.sum() else null
    val downloaded = downloadedBytes.coerceAtLeast(0L)
    val eta = if (total != null && bytesPerSecond > 0.0 && bytesPerSecond.isFinite()) {
        kotlin.math.ceil((total - downloaded).coerceAtLeast(0L).toDouble() / bytesPerSecond).toLong()
    } else null
    return DownloadMetrics(downloaded, total, bytesPerSecond.takeIf { it.isFinite() && it > 0.0 } ?: 0.0, eta)
}
