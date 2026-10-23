package com.sparktube.app.ui.home

import com.sparktube.app.ui.common.VideoUiModel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class HomeFeedCachePolicyTest {
    @Test fun cacheExpiresAfterPolicyTtlAndRejectsFutureOrMissingTimestamp() {
        val now = 10_000_000L
        assertTrue(HomeFeedCache.isUsable(now, now))
        assertTrue(HomeFeedCache.isUsable(now, now + HomeFeedCache.TTL_MILLIS))
        assertFalse(HomeFeedCache.isUsable(now, now + HomeFeedCache.TTL_MILLIS + 1))
        assertFalse(HomeFeedCache.isUsable(0L, now))
        assertFalse(HomeFeedCache.isUsable(now + 1, now))
    }

    @Test fun cacheIsDeduplicatedAndHardBounded() {
        val repeated = VideoUiModel("watch/0", "title", "", "", 0, -1, "")
        val input = (0 until HomeFeedCache.MAX_ENTRIES + 5).map {
            VideoUiModel("watch/$it", "title$it", "", "", 0, -1, "")
        } + repeated
        val output = HomeFeedCache.bounded(input)
        assertEquals(HomeFeedCache.MAX_ENTRIES, output.size)
        assertEquals(output.size, output.map { it.url }.distinct().size)
        assertTrue(output.all { it.url.isNotBlank() && it.title.isNotBlank() })
    }

    @Test fun cacheRejectsUnrenderableEntries() {
        assertTrue(HomeFeedCache.bounded(listOf(
            VideoUiModel("", "title", "", "", 0, -1, ""),
            VideoUiModel("watch/1", "", "", "", 0, -1, "")
        )).isEmpty())
    }
}
