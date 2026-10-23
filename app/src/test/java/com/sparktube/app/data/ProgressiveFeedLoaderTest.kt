package com.sparktube.app.data

import java.io.IOException
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.async
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import org.junit.Assert.*
import org.junit.Test

class ProgressiveFeedLoaderTest {
    @Test fun firstUsefulCardsAppearBeforeSlowerSourceCompletes() = runBlocking {
        withTimeout(5_000) {
            val slowStarted = CompletableDeferred<Unit>()
            val releaseSlow = CompletableDeferred<Unit>()
            val preview = CompletableDeferred<List<String>>()
            val loaders: List<suspend () -> List<String>> = listOf(
                { slowStarted.complete(Unit); releaseSlow.await(); listOf("slow") },
                { slowStarted.await(); listOf("fast") }
            )
            val result = async { ProgressiveFeedLoader.load(loaders) { preview.complete(it) } }
            assertEquals(listOf("fast"), preview.await())
            assertFalse(result.isCompleted)
            releaseSlow.complete(Unit)
            // Final ordering remains input ordering, not network completion ordering.
            assertEquals(listOf(listOf("slow"), listOf("fast")), result.await())
        }
    }

    @Test fun oneFailedSourceDoesNotHideSuccessfulCards() = runBlocking {
        val loaders: List<suspend () -> List<String>> = listOf(
            { throw IOException("offline source") }, { listOf("video") }
        )
        var preview = emptyList<String>()
        assertEquals(listOf(listOf("video")), ProgressiveFeedLoader.load(loaders) { preview = it })
        assertEquals(listOf("video"), preview)
    }

    @Test fun publishesOnlyOneNonemptyInitialList() = runBlocking {
        val calls = AtomicInteger()
        val loaders: List<suspend () -> List<String>> = listOf(
            { emptyList() }, { listOf("a") }, { listOf("b") }
        )
        val result = ProgressiveFeedLoader.load(loaders) { assertTrue(it.isNotEmpty()); calls.incrementAndGet() }
        assertEquals(1, calls.get())
        assertEquals(listOf(listOf("a"), listOf("b")), result)
    }

    @Test fun allEmptyResultsProduceAnErrorInsteadOfBlankSuccessfulCache() = runBlocking {
        val loaders: List<suspend () -> List<String>> = listOf({ emptyList() })
        try {
            ProgressiveFeedLoader.load(loaders) { fail("No preview expected") }
            fail("Expected an error")
        } catch (expected: IOException) {
            assertTrue(expected.message!!.contains("No content"))
        }
    }

    @Test fun allFailuresPreserveUsefulFailureReason() = runBlocking {
        val loaders: List<suspend () -> List<String>> = listOf({ throw IOException("network unavailable") })
        try {
            ProgressiveFeedLoader.load(loaders) {}
            fail("Expected original error")
        } catch (expected: IOException) {
            assertEquals("network unavailable", expected.message)
        }
    }

    @Test fun cancellationIsNotSwallowedAsAnEmptyFeed() = runBlocking {
        val loaders: List<suspend () -> List<String>> = listOf({ throw CancellationException("new country selected") })
        try {
            ProgressiveFeedLoader.load(loaders) {}
            fail("Expected cancellation")
        } catch (expected: CancellationException) {
            assertEquals("new country selected", expected.message)
        }
    }
}
