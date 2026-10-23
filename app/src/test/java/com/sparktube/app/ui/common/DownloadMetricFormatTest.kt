package com.sparktube.app.ui.common

import org.junit.Assert.assertEquals
import org.junit.Test

class DownloadMetricFormatTest {
    @Test fun usesDecimalMegabytesNotBitsOrMebibytes() {
        assertEquals("1.00 MB", DownloadMetricFormat.megabytes(1_000_000L))
        assertEquals("1.00 MB/s", DownloadMetricFormat.rate(1_000_000.0))
    }
    @Test fun formatsReferenceDownloadedAndTotal() {
        assertEquals("70.20 MB", DownloadMetricFormat.megabytes(70_200_000L))
        assertEquals("222.20 MB", DownloadMetricFormat.megabytes(222_200_000L))
        assertEquals("36.80 MB/s", DownloadMetricFormat.rate(36_800_000.0))
    }
    @Test fun smallPositiveTransferIsNotShownAsZero() {
        assertEquals("<0.01 MB", DownloadMetricFormat.megabytes(1L))
        assertEquals("<0.01 MB/s", DownloadMetricFormat.rate(1.0))
    }
    @Test fun invalidRatesAreZero() {
        listOf(Double.NaN, Double.POSITIVE_INFINITY, -1.0, 0.0).forEach {
            assertEquals("0.00 MB/s", DownloadMetricFormat.rate(it))
        }
    }
    @Test fun negativeBytesAreClamped() {
        assertEquals("0.00 MB", DownloadMetricFormat.megabytes(-1L))
    }
    @Test fun durationUsesSecondsMinutesAndHours() {
        assertEquals("5 s", DownloadMetricFormat.duration(5L))
        assertEquals("1 min 5 s", DownloadMetricFormat.duration(65L))
        assertEquals("1 h 1 min", DownloadMetricFormat.duration(3_665L))
    }
    @Test fun zeroAndNegativeDurationAreSafe() {
        assertEquals("0 s", DownloadMetricFormat.duration(0L))
        assertEquals("0 s", DownloadMetricFormat.duration(-10L))
    }
    @Test fun veryLargeByteCountDoesNotOverflow() {
        assertEquals("9223372036854.78 MB", DownloadMetricFormat.megabytes(Long.MAX_VALUE))
    }
}
