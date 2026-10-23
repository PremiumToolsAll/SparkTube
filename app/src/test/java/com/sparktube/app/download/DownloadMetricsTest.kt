package com.sparktube.app.download

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class DownloadMetricsTest {
    @Test fun totalsAndEtaUseBytesAndCeilSeconds() {
        val metrics = calculateDownloadMetrics(2_000_000L, listOf(5_000_000L), 1_000_000.0)
        assertEquals(2_000_000L, metrics.downloadedBytes)
        assertEquals(5_000_000L, metrics.totalBytes)
        assertEquals(40, metrics.progressPercent)
        assertEquals(3L, metrics.remainingSeconds)
    }

    @Test fun etaRoundsUpRatherThanClaimingCompletionEarly() {
        assertEquals(2L, calculateDownloadMetrics(0L, listOf(101L), 100.0).remainingSeconds)
    }

    @Test fun hugeProgressDoesNotOverflow() {
        assertEquals(100, calculateDownloadMetrics(Long.MAX_VALUE, listOf(Long.MAX_VALUE), 0.0).progressPercent)
    }

    @Test fun outOfOrderParallelUpdateCannotResetSampleBaseline() {
        val sampler = DownloadSpeedSampler()
        sampler.onBytes(0L, 0L)
        sampler.onBytes(500L, 500_000_000L)
        sampler.onBytes(100L, 600_000_000L)
        sampler.onBytes(1_000L, 1_000_000_000L)
        assertEquals(1_000.0, sampler.bytesPerSecond(1_000_000_000L), 0.001)
    }

    @Test fun unknownOrPartiallyKnownTotalsStayUnknown() {
        val unknown = calculateDownloadMetrics(900L, listOf(null), 100.0)
        assertNull(unknown.totalBytes)
        assertNull(unknown.remainingSeconds)
        assertEquals(0, unknown.progressPercent)
        assertNull(calculateDownloadMetrics(10L, listOf(20L, null), 1.0).totalBytes)
    }

    @Test fun pairedTransferAggregatesEveryKnownComponentIncludingFinishedOne() {
        val pair = calculateDownloadMetrics(400L + 300L, listOf(400L, 1_000L), 100.0)
        assertEquals(1_400L, pair.totalBytes)
        assertEquals(50, pair.progressPercent)
        assertEquals(7L, pair.remainingSeconds)
    }

    @Test fun samplerIsIndependentOfReadsAndResetsAcrossPauseResume() {
        val sampler = DownloadSpeedSampler()
        sampler.onBytes(0L, 0L)
        sampler.onBytes(500L, 500_000_000L)
        assertEquals(1_000.0, sampler.bytesPerSecond(500_000_000L), 0.001)
        sampler.reset(1_000_000_000L, 500L) // pause
        assertEquals(0.0, sampler.bytesPerSecond(1_000_000_000L), 0.0)
        sampler.onBytes(500L, 2_000_000_000L) // resumed, baseline only
        sampler.onBytes(1_000L, 2_500_000_000L)
        assertEquals(1_000.0, sampler.bytesPerSecond(2_500_000_000L), 0.001)
    }

    @Test fun staleTransferReportsZeroSpeed() {
        val sampler = DownloadSpeedSampler()
        sampler.onBytes(0L, 10L)
        sampler.onBytes(250L, 250_000_010L)
        assertEquals(0.0, sampler.bytesPerSecond(1_750_000_011L), 0.0)
    }
}
