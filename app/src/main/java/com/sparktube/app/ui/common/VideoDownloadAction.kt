package com.sparktube.app.ui.common

import android.content.Context
import android.content.ContextWrapper
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.lifecycle.lifecycleScope
import com.sparktube.app.R
import com.sparktube.app.data.YtRepository
import com.sparktube.app.download.DownloadCenter
import com.sparktube.app.playback.StreamCatalog
import com.sparktube.app.ui.MainActivity
import com.sparktube.app.ui.player.DownloadSheet
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import java.util.WeakHashMap

/** Starts the existing download picker without changing current playback. */
internal object VideoDownloadAction {
    // Accessed only on the UI thread. Do not retain a finished screen globally.
    private val resolving = WeakHashMap<ComponentActivity, MutableSet<String>>()

    fun start(context: Context, item: VideoUiModel) {
        if (DownloadCenter.isDownloaded(context, item.url) ||
            DownloadCenter.hasActiveDownload(context, item.url)) {
            MainActivity.openDownloads(context)
            return
        }
        val activity = activityFrom(context) ?: return
        if (activity.isFinishing || activity.isDestroyed) return
        val urls = resolving.getOrPut(activity) { mutableSetOf() }
        if (!urls.add(item.url)) return
        val appContext = context.applicationContext
        val entry = item.toQueueEntry()
        activity.lifecycleScope.launch {
            try {
                val catalog = StreamCatalog(YtRepository.streamInfo(item.url))
                if (!activity.isFinishing && !activity.isDestroyed) {
                    DownloadSheet(activity, entry, catalog).show()
                }
            } catch (cancelled: CancellationException) {
                throw cancelled
            } catch (_: Exception) {
                Toast.makeText(appContext, R.string.error_no_streams, Toast.LENGTH_SHORT).show()
            } finally {
                urls.remove(item.url)
                if (urls.isEmpty()) resolving.remove(activity)
            }
        }
    }

    private fun activityFrom(context: Context): ComponentActivity? {
        var current = context
        while (true) {
            if (current is ComponentActivity) return current
            val base = (current as? ContextWrapper)?.baseContext ?: return null
            if (base === current) return null
            current = base
        }
    }
}
