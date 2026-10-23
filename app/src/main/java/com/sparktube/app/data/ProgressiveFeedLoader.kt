package com.sparktube.app.data

import java.io.IOException
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope

/** Bounded feed fan-out: publish the first useful list without waiting for slower sources. */
internal object ProgressiveFeedLoader {
    suspend fun <T> load(
        loaders: List<suspend () -> List<T>>,
        onInitialItems: suspend (List<T>) -> Unit
    ): List<List<T>> = coroutineScope {
        val published = AtomicBoolean(false)
        val lastError = AtomicReference<Exception?>(null)
        val results = loaders.map { loader ->
            async(Dispatchers.IO) {
                val items = try {
                    loader()
                } catch (e: CancellationException) {
                    throw e
                } catch (e: Exception) {
                    lastError.set(e)
                    emptyList()
                }
                if (items.isNotEmpty() && published.compareAndSet(false, true)) {
                    onInitialItems(items)
                }
                items
            }
        }.awaitAll().filter { it.isNotEmpty() }
        if (results.isEmpty()) throw lastError.get() ?: IOException("No content available for this region")
        results
    }
}
