package com.sparktube.app.ui.home

import android.content.Context
import com.sparktube.app.ui.common.VideoUiModel
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/** Cache policy and storage for display-only Home cards (watch-page URLs, never resolved stream URLs). */
internal object HomeFeedCache {
    const val MAX_ENTRIES = 60
    const val TTL_MILLIS = 3L * 24 * 60 * 60 * 1000
    private const val VERSION = 1
    private val memory = mutableMapOf<String, Snapshot>()

    data class Snapshot(val savedAtMillis: Long, val items: List<VideoUiModel>)

    /** Pure policy: only a nonempty, recent snapshot is eligible for instant display. */
    fun isUsable(savedAtMillis: Long, nowMillis: Long): Boolean =
        savedAtMillis > 0L && nowMillis >= savedAtMillis && nowMillis - savedAtMillis <= TTL_MILLIS

    /** Bounds entries and rejects blank/non-video destinations; URLs remain page URLs from VideoUiModel. */
    fun bounded(items: List<VideoUiModel>): List<VideoUiModel> = items
        .asSequence()
        .filter { it.url.isNotBlank() && it.title.isNotBlank() }
        .distinctBy { it.url }
        .take(MAX_ENTRIES)
        .toList()

    @Synchronized
    fun read(context: Context, country: String, nowMillis: Long = System.currentTimeMillis()): List<VideoUiModel> {
        val mem = memory[country]
        if (mem != null && isUsable(mem.savedAtMillis, nowMillis) && mem.items.isNotEmpty()) return mem.items
        val file = cacheFile(context, country)
        val snapshot = runCatching {
            val root = JSONObject(file.readText())
            if (root.optInt("version") != VERSION || root.optString("country") != country) return@runCatching null
            val saved = root.optLong("savedAt", 0L)
            if (!isUsable(saved, nowMillis)) return@runCatching null
            val arr = root.optJSONArray("items") ?: return@runCatching null
            val result = ArrayList<VideoUiModel>(arr.length().coerceAtMost(MAX_ENTRIES))
            for (i in 0 until arr.length().coerceAtMost(MAX_ENTRIES)) {
                val row = arr.optJSONObject(i) ?: continue
                result += VideoUiModel(
                    url = row.optString("url"), title = row.optString("title"),
                    uploader = row.optString("uploader"), thumbnailUrl = row.optString("thumbnail"),
                    durationSec = row.optLong("duration"), viewCount = row.optLong("views", -1L),
                    uploadDate = row.optString("date"), uploaderAvatarUrl = row.optString("avatar")
                )
            }
            Snapshot(saved, bounded(result)).takeIf { it.items.isNotEmpty() }
        }.getOrNull()
        if (snapshot == null) {
            memory.remove(country)
            runCatching { file.delete() }
            return emptyList()
        }
        memory[country] = snapshot
        return snapshot.items
    }

    @Synchronized
    fun write(
        context: Context,
        country: String,
        items: List<VideoUiModel>,
        savedAtMillis: Long = System.currentTimeMillis(),
        shouldWrite: () -> Boolean = { true }
    ) {
        // Recheck after acquiring the cache lock, not before waiting behind another writer.
        if (!shouldWrite()) return
        val safeItems = bounded(items)
        if (safeItems.isEmpty() || country.isBlank() || savedAtMillis <= 0L) return
        val rows = JSONArray()
        safeItems.forEach { model ->
            rows.put(JSONObject().put("url", model.url).put("title", model.title)
                .put("uploader", model.uploader).put("thumbnail", model.thumbnailUrl)
                .put("duration", model.durationSec).put("views", model.viewCount)
                .put("date", model.uploadDate).put("avatar", model.uploaderAvatarUrl))
        }
        val snapshot = Snapshot(savedAtMillis, safeItems)
        memory[country] = snapshot
        val file = cacheFile(context, country)
        runCatching {
            file.parentFile?.mkdirs()
            val payload = JSONObject().put("version", VERSION).put("country", country)
                .put("savedAt", savedAtMillis).put("items", rows).toString()
            val temp = File(file.parentFile, file.name + ".tmp")
            temp.writeText(payload)
            if (!temp.renameTo(file)) {
                file.writeText(payload)
                temp.delete()
            }
        }
    }

    @Synchronized
    internal fun clearMemoryForTests() = memory.clear()

    private fun cacheFile(context: Context, country: String): File {
        val key = country.uppercase().filter { it.isLetterOrDigit() }.take(8).ifBlank { "default" }
        return File(File(context.applicationContext.filesDir, "home-feed"), "$key.json")
    }
}
