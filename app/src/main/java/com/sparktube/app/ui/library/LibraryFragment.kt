package com.sparktube.app.ui.library

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.MotionEvent
import android.os.Handler
import android.os.Looper
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.tabs.TabLayout
import com.sparktube.app.R
import com.sparktube.app.data.LocalStore
import com.sparktube.app.databinding.FragmentLibraryBinding
import com.sparktube.app.download.DownloadCenter
import com.sparktube.app.playback.PlaybackCenter
import com.sparktube.app.playback.QueueEntry
import com.sparktube.app.ui.channel.ChannelActivity
import com.sparktube.app.ui.common.ChannelRowAdapter
import com.sparktube.app.ui.common.DownloadAdapter
import com.sparktube.app.ui.common.PlaylistAdapter
import com.sparktube.app.ui.common.VideoAdapter
import com.sparktube.app.ui.common.toEntry
import com.sparktube.app.ui.common.toUiModel
import com.sparktube.app.ui.player.PlayerActivity
import com.sparktube.app.ui.playlist.PlaylistActivity
import com.sparktube.app.ui.music.AudioDownloadLibrary
import com.sparktube.app.ui.music.NowPlayingActivity

/**
 * Library: History, Favorites, Subscriptions, Downloads and Playlists tabs.
 * Everything is stored locally on the device.
 */
class LibraryFragment : Fragment() {

    private var _binding: FragmentLibraryBinding? = null
    private val binding get() = _binding!!

    private lateinit var videoAdapter: VideoAdapter
    private lateinit var channelAdapter: ChannelRowAdapter
    private lateinit var downloadAdapter: DownloadAdapter
    private lateinit var playlistAdapter: PlaylistAdapter

    private var tab = TAB_HISTORY
    private val uiHandler = Handler(Looper.getMainLooper())
    private val refreshDownloads = object : Runnable {
        override fun run() { if (_binding != null && tab == TAB_DOWNLOADS) { refresh(); uiHandler.postDelayed(this, 1000) } }
    }
    private var downX = 0f
    private var downY = 0f

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentLibraryBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        videoAdapter = VideoAdapter(
            onClick = { model -> PlayerActivity.start(requireContext(), model) },
            onLongClick = { model ->
                if (tab == TAB_HISTORY) {
                    LocalStore.removeFromHistory(requireContext(), model.url)
                    Toast.makeText(requireContext(), R.string.removed_from_history, Toast.LENGTH_SHORT).show()
                } else {
                    LocalStore.toggleFavorite(requireContext(), model.toEntry())
                    Toast.makeText(requireContext(), R.string.removed_from_favorites, Toast.LENGTH_SHORT).show()
                }
                refresh()
                true
            }
        )
        channelAdapter = ChannelRowAdapter(
            onClick = { channel ->
                ChannelActivity.start(requireContext(), channel.url, channel.name)
            },
            onUnsubscribe = { channel ->
                LocalStore.toggleSubscription(requireContext(), channel)
                Toast.makeText(requireContext(), R.string.unsubscribed_toast, Toast.LENGTH_SHORT).show()
                refresh()
            }
        )
        downloadAdapter = DownloadAdapter(
            onClick = { record -> openDownload(record) },
            onLongClick = { record -> confirmDelete(record) },
            onPause = { record ->
                if (record.status != DownloadCenter.STATUS_PAUSED) AlertDialog.Builder(requireContext())
                    .setMessage(R.string.download_process_limit).setPositiveButton(android.R.string.ok) { _, _ ->
                        DownloadCenter.togglePause(requireContext(), record); refresh()
                    }.setNegativeButton(android.R.string.cancel, null).show()
                else { DownloadCenter.togglePause(requireContext(), record); refresh() }
            }
        )
        playlistAdapter = PlaylistAdapter(
            onClick = { playlist ->
                PlaylistActivity.start(requireContext(), playlist.id)
            },
            onLongClick = { playlist -> confirmDeletePlaylist(playlist) }
        )

        binding.list.layoutManager = LinearLayoutManager(requireContext())
        binding.list.adapter = videoAdapter

        binding.tabs.addOnTabSelectedListener(object : TabLayout.OnTabSelectedListener {
            override fun onTabSelected(tab: TabLayout.Tab) {
                this@LibraryFragment.tab = tab.position
                uiHandler.removeCallbacks(refreshDownloads)
                refresh()
                if (tab.position == TAB_DOWNLOADS) uiHandler.post(refreshDownloads)
            }

            override fun onTabUnselected(tab: TabLayout.Tab) = Unit
            override fun onTabReselected(tab: TabLayout.Tab) = Unit
        })

        binding.tabs.selectTab(binding.tabs.getTabAt(tab))
        binding.list.addOnItemTouchListener(object : RecyclerView.SimpleOnItemTouchListener() {
            private var switched = false
            override fun onInterceptTouchEvent(rv: RecyclerView, event: MotionEvent): Boolean {
                when (event.actionMasked) {
                    MotionEvent.ACTION_DOWN -> { downX = event.x; downY = event.y; switched = false }
                    MotionEvent.ACTION_MOVE -> {
                        val dx = event.x - downX
                        val dy = event.y - downY
                        val threshold = 56 * resources.displayMetrics.density
                        if (!switched && kotlin.math.abs(dx) > threshold && kotlin.math.abs(dx) > kotlin.math.abs(dy) * 1.4f) {
                            switched = true
                            val direction = if (rv.layoutDirection == View.LAYOUT_DIRECTION_RTL) -1 else 1
                            val next = (this@LibraryFragment.tab + (if (dx < 0) direction else -direction)).coerceIn(TAB_HISTORY, TAB_PLAYLISTS)
                            binding.tabs.getTabAt(next)?.select()
                            return true
                        }
                    }
                }
                return false
            }
        })
    }

    fun showDownloadsTab() {
        if (_binding == null) return
        binding.tabs.getTabAt(TAB_DOWNLOADS)?.select()
        refresh()
        uiHandler.removeCallbacks(refreshDownloads)
        uiHandler.post(refreshDownloads)
    }

    override fun onResume() {
        super.onResume()
        refresh()
        uiHandler.removeCallbacks(refreshDownloads)
        if (tab == TAB_DOWNLOADS) uiHandler.post(refreshDownloads)
    }

    override fun onPause() { uiHandler.removeCallbacks(refreshDownloads); super.onPause() }

    override fun onHiddenChanged(hidden: Boolean) {
        super.onHiddenChanged(hidden)
        uiHandler.removeCallbacks(refreshDownloads)
        if (!hidden) {
            refresh()
            if (tab == TAB_DOWNLOADS) uiHandler.post(refreshDownloads)
        }
    }

    private fun refresh() {
        val context = context ?: return
        when (tab) {
            TAB_HISTORY -> bindVideos(LocalStore.history(context), R.string.empty_history)
            TAB_FAVORITES -> bindVideos(LocalStore.videoFavorites(context), R.string.empty_favorites)
            TAB_SUBSCRIPTIONS -> bindChannels()
            TAB_PLAYLISTS -> bindPlaylists()
            else -> bindDownloads()
        }
    }

    private fun bindVideos(entries: List<com.sparktube.app.data.VideoEntry>, emptyText: Int) {
        binding.list.adapter = videoAdapter
        videoAdapter.submitList(entries.map { it.toUiModel() })
        binding.emptyView.setText(emptyText)
        binding.emptyView.isVisible = entries.isEmpty()
    }

    private fun bindChannels() {
        val context = context ?: return
        val channels = LocalStore.subscriptions(context)
        binding.list.adapter = channelAdapter
        channelAdapter.submitList(channels)
        binding.emptyView.setText(R.string.empty_subscriptions)
        binding.emptyView.isVisible = channels.isEmpty()
    }

    private fun bindDownloads() {
        val context = context ?: return
        DownloadCenter.refreshStatuses(context)
        // Include audio too so every transfer can be paused, resumed and shared here.
        val downloads = LocalStore.downloads(context)
        if (binding.list.adapter !== downloadAdapter) binding.list.adapter = downloadAdapter
        downloadAdapter.submitList(downloads) { downloadAdapter.refreshLiveMetrics() }
        binding.emptyView.setText(R.string.empty_downloads)
        binding.emptyView.isVisible = downloads.isEmpty()
    }

    private fun openDownload(record: com.sparktube.app.data.DownloadRecord) {
        if (record.type != DownloadCenter.TYPE_AUDIO) {
            PlaybackCenter.playDownload(record)
            return
        }
        val playable = AudioDownloadLibrary.playable(listOf(record)).firstOrNull()
        if (playable == null) {
            Toast.makeText(requireContext(), R.string.download_file_missing, Toast.LENGTH_SHORT).show()
            return
        }
        val (audio, path) = playable
        PlaybackCenter.playMusicQueue(
            listOf(QueueEntry(
                url = "file://$path",
                title = audio.title,
                uploader = audio.uploader,
                thumbnailUrl = audio.thumbnailUrl,
                durationSec = 0L,
                isMusic = true
            )),
            0
        )
        NowPlayingActivity.start(requireContext())
    }

    private fun bindPlaylists() {
        val context = context ?: return
        val playlists = LocalStore.playlists(context)
        binding.list.adapter = playlistAdapter
        playlistAdapter.submitList(playlists)
        binding.emptyView.setText(R.string.empty_playlists)
        binding.emptyView.isVisible = playlists.isEmpty()
    }

    private fun confirmDeletePlaylist(playlist: com.sparktube.app.data.Playlist) {
        AlertDialog.Builder(requireContext())
            .setTitle(R.string.delete_playlist_confirm)
            .setMessage(playlist.name)
            .setPositiveButton(android.R.string.ok) { _, _ ->
                LocalStore.deletePlaylist(requireContext(), playlist.id)
                Toast.makeText(requireContext(), R.string.playlist_deleted, Toast.LENGTH_SHORT).show()
                refresh()
            }
            .setNegativeButton(android.R.string.cancel, null)
            .show()
    }

    private fun confirmDelete(record: com.sparktube.app.data.DownloadRecord) {
        AlertDialog.Builder(requireContext())
            .setTitle(R.string.download_delete_confirm)
            .setMessage(record.title)
            .setPositiveButton(android.R.string.ok) { _, _ ->
                DownloadCenter.delete(requireContext(), record)
                Toast.makeText(requireContext(), R.string.download_deleted, Toast.LENGTH_SHORT).show()
                refresh()
            }
            .setNegativeButton(android.R.string.cancel, null)
            .show()
    }

    override fun onDestroyView() {
        uiHandler.removeCallbacks(refreshDownloads)
        super.onDestroyView()
        _binding = null
    }

    companion object {
        private const val TAB_HISTORY = 0
        private const val TAB_FAVORITES = 1
        private const val TAB_SUBSCRIPTIONS = 2
        private const val TAB_DOWNLOADS = 3
        private const val TAB_PLAYLISTS = 4
    }
}
