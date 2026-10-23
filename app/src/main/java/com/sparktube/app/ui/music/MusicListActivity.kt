package com.sparktube.app.ui.music

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import androidx.recyclerview.widget.LinearLayoutManager
import com.sparktube.app.R
import com.sparktube.app.data.DownloadRecord
import com.sparktube.app.data.LocalStore
import com.sparktube.app.data.VideoEntry
import com.sparktube.app.databinding.ActivityMusicListBinding
import com.sparktube.app.download.DownloadCenter
import com.sparktube.app.playback.PlaybackCenter
import com.sparktube.app.playback.QueueEntry
import com.sparktube.app.ui.common.DownloadAdapter
import com.sparktube.app.ui.common.MusicRowAdapter
import com.sparktube.app.ui.common.VideoUiModel
import com.sparktube.app.util.Themes

/** Music favorites and the audio download library, including live transfers. */
class MusicListActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMusicListBinding
    private lateinit var adapter: MusicRowAdapter
    private lateinit var downloadAdapter: DownloadAdapter
    private var favourites = true
    private var entries: List<QueueEntry> = emptyList()
    private val uiHandler = Handler(Looper.getMainLooper())
    private val refreshDownloads = object : Runnable {
        override fun run() {
            reload()
            uiHandler.postDelayed(this, 1000L)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        Themes.apply(this)
        super.onCreate(savedInstanceState)
        binding = ActivityMusicListBinding.inflate(layoutInflater)
        setContentView(binding.root)

        favourites = intent.getBooleanExtra(EXTRA_FAVOURITES, true)
        binding.title.text =
            getString(if (favourites) R.string.music_favorites else R.string.music_downloads)

        adapter = MusicRowAdapter(onClick = { model ->
            val index = entries.indexOfFirst { it.url == model.url }
            if (index >= 0) playQueue(index)
        })
        downloadAdapter = DownloadAdapter(
            onClick = { record -> openDownload(record) },
            onLongClick = { record -> confirmDelete(record) },
            onPause = { record ->
                if (record.status != DownloadCenter.STATUS_PAUSED) {
                    AlertDialog.Builder(this)
                        .setMessage(R.string.download_process_limit)
                        .setPositiveButton(android.R.string.ok) { _, _ ->
                            DownloadCenter.togglePause(this, record)
                            reload()
                        }
                        .setNegativeButton(android.R.string.cancel, null)
                        .show()
                } else {
                    DownloadCenter.togglePause(this, record)
                    reload()
                }
            },
            audioStyle = true
        )
        binding.list.layoutManager = LinearLayoutManager(this)
        binding.list.adapter = if (favourites) adapter else downloadAdapter
        // Avoid a change animation on every one-second metrics refresh.
        if (!favourites) binding.list.itemAnimator = null
        binding.backButton.setOnClickListener { finish() }
        binding.playAllButton.setOnClickListener {
            // Re-check disk and completion state at the instant Play all is tapped.
            reload()
            if (entries.isNotEmpty()) playQueue(0)
        }
    }

    override fun onResume() {
        super.onResume()
        Themes.recreateIfNeeded(this)
        uiHandler.removeCallbacks(refreshDownloads)
        reload()
        if (!favourites) uiHandler.postDelayed(refreshDownloads, 1000L)
    }

    override fun onPause() {
        uiHandler.removeCallbacks(refreshDownloads)
        super.onPause()
    }

    override fun onDestroy() {
        uiHandler.removeCallbacks(refreshDownloads)
        super.onDestroy()
    }

    private fun reload() {
        val hasRows: Boolean
        if (favourites) {
            entries = LocalStore.musicFavorites(this).map { it.toQueueEntry() }
            adapter.submitList(entries.map { it.toRowModel() })
            binding.emptyView.setText(R.string.empty_music_favorites)
            hasRows = entries.isNotEmpty()
        } else {
            DownloadCenter.refreshStatuses(this)
            val records = AudioDownloadLibrary.rows(LocalStore.downloads(this))
            entries = AudioDownloadLibrary.playable(records).map { (record, path) -> record.toQueueEntry(path) }
            downloadAdapter.submitList(records) { downloadAdapter.refreshLiveMetrics() }
            binding.emptyView.setText(R.string.empty_music_downloads)
            hasRows = records.isNotEmpty()
        }
        binding.emptyView.isVisible = !hasRows
        binding.summaryRow.isVisible = hasRows
        binding.subtitle.text = getString(R.string.music_songs_fmt, entries.size)
        binding.playAllButton.isEnabled = entries.isNotEmpty()
        binding.playAllButton.alpha = if (entries.isNotEmpty()) 1f else 0.45f
    }

    private fun playQueue(index: Int) {
        PlaybackCenter.playMusicQueue(entries, index)
        NowPlayingActivity.start(this)
    }

    private fun openDownload(record: DownloadRecord) {
        reload()
        val path = AudioDownloadLibrary.playable(listOf(record)).firstOrNull()?.second
        val index = entries.indexOfFirst { it.url == "file://$path" }
        if (path != null && index >= 0) playQueue(index)
        else Toast.makeText(this, R.string.download_file_missing, Toast.LENGTH_SHORT).show()
    }

    private fun confirmDelete(record: DownloadRecord) {
        AlertDialog.Builder(this)
            .setTitle(R.string.download_delete_confirm)
            .setMessage(record.title)
            .setPositiveButton(android.R.string.ok) { _, _ ->
                DownloadCenter.delete(this, record)
                Toast.makeText(this, R.string.download_deleted, Toast.LENGTH_SHORT).show()
                reload()
            }
            .setNegativeButton(android.R.string.cancel, null)
            .show()
    }

    companion object {
        private const val EXTRA_FAVOURITES = "extra_favourites"

        fun start(context: Context, favourites: Boolean) {
            context.startActivity(
                Intent(context, MusicListActivity::class.java)
                    .putExtra(EXTRA_FAVOURITES, favourites)
            )
        }
    }
}

private fun VideoEntry.toQueueEntry(): QueueEntry = QueueEntry(
    url = url, title = title, uploader = uploader, thumbnailUrl = thumbnailUrl,
    durationSec = durationSec, isMusic = true
)

private fun QueueEntry.toRowModel(): VideoUiModel = VideoUiModel(
    url = url, title = title, uploader = uploader, thumbnailUrl = thumbnailUrl,
    durationSec = durationSec, viewCount = -1L, uploadDate = ""
)

private fun DownloadRecord.toQueueEntry(path: String): QueueEntry = QueueEntry(
    url = "file://$path", title = title, uploader = uploader, thumbnailUrl = thumbnailUrl,
    durationSec = 0L, isMusic = true
)
