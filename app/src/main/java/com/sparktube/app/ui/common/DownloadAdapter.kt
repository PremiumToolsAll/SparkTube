package com.sparktube.app.ui.common

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.appcompat.widget.PopupMenu
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.sparktube.app.R
import com.sparktube.app.data.DownloadRecord
import com.sparktube.app.databinding.ItemDownloadBinding
import com.sparktube.app.download.DownloadCenter
import com.sparktube.app.download.DownloadSharing
import com.sparktube.app.util.Thumbs

/** Download entries on the Library > Downloads tab. */
class DownloadAdapter(
    private val onClick: (DownloadRecord) -> Unit,
    private val onLongClick: (DownloadRecord) -> Unit,
    private val onPause: ((DownloadRecord) -> Unit)? = null,
    private val audioStyle: Boolean = false
) : ListAdapter<DownloadRecord, DownloadAdapter.VH>(DIFF) {
    companion object {
        private val DIFF = object : DiffUtil.ItemCallback<DownloadRecord>() {
            override fun areItemsTheSame(a: DownloadRecord, b: DownloadRecord): Boolean =
                a.videoId == b.videoId && a.type == b.type && a.quality == b.quality
            override fun areContentsTheSame(a: DownloadRecord, b: DownloadRecord): Boolean =
                a.status == b.status && a.title == b.title && a.filePaths == b.filePaths
        }
    }

    class VH(val binding: ItemDownloadBinding) : RecyclerView.ViewHolder(binding.root)

    /** Runtime metrics are not persisted in DownloadRecord or compared by DiffUtil. */
    fun refreshLiveMetrics() { notifyItemRangeChanged(0, itemCount) }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH =
        VH(ItemDownloadBinding.inflate(LayoutInflater.from(parent.context), parent, false))

    override fun onBindViewHolder(holder: VH, position: Int) {
        val item = getItem(position)
        val b = holder.binding
        val context = b.root.context
        if (audioStyle) {
            val density = context.resources.displayMetrics.density
            val imageSize = (60 * density).toInt()
            b.thumb.layoutParams = b.thumb.layoutParams.apply {
                width = imageSize
                height = imageSize
            }
            b.title.maxLines = 1
            b.title.textSize = 15f
            b.meta.maxLines = 1
            b.root.setPadding((8 * density).toInt(), (8 * density).toInt(), (4 * density).toInt(), (8 * density).toInt())
        }
        b.title.text = item.title
        val typeLabel = when (item.type) {
            DownloadCenter.TYPE_AUDIO -> context.getString(R.string.download_type_audio)
            DownloadCenter.TYPE_AV -> context.getString(R.string.download_type_av)
            else -> context.getString(R.string.download_type_video)
        }
        val statusLabel = when (item.status) {
            DownloadCenter.STATUS_DONE -> context.getString(R.string.download_status_done)
            DownloadCenter.STATUS_RUNNING -> context.getString(R.string.download_status_running)
            DownloadCenter.STATUS_FAILED -> context.getString(R.string.download_status_failed)
            DownloadCenter.STATUS_PAUSED -> context.getString(R.string.download_paused)
            else -> context.getString(R.string.download_status_pending)
        }
        b.meta.text = if (audioStyle) item.uploader.ifBlank { typeLabel }
            else "$typeLabel • ${item.quality} • $statusLabel"
        val active = item.status == DownloadCenter.STATUS_PENDING ||
            item.status == DownloadCenter.STATUS_RUNNING || item.status == DownloadCenter.STATUS_PAUSED
        val paused = item.status == DownloadCenter.STATUS_PAUSED
        b.pauseButton.visibility = if (active) View.VISIBLE else View.GONE
        b.pauseButton.text = context.getString(if (paused) R.string.download_resume else R.string.download_pause)
        b.pauseButton.setOnClickListener {
            onPause?.invoke(item) ?: DownloadCenter.togglePause(context, item)
        }

        // Exactly one snapshot per bind; getters must not change the sampling period.
        val metrics = DownloadCenter.metrics(item)
        val total = metrics.totalBytes
        val downloaded = DownloadMetricFormat.megabytes(metrics.downloadedBytes)
        val sizeText = context.getString(R.string.download_size_progress, downloaded,
            total?.let(DownloadMetricFormat::megabytes) ?: context.getString(R.string.download_total_unknown))
        b.progress.visibility = if (active) View.VISIBLE else View.GONE
        b.progress.isIndeterminate = active && !paused && total == null
        b.progress.progress = if (total != null && total > 0L) {
            (metrics.downloadedBytes.toDouble() / total.toDouble() * 100.0).toInt().coerceIn(0, 100)
        } else 0
        b.speed.text = when {
            paused -> "$sizeText\n${context.getString(R.string.download_paused)}"
            active -> {
                val eta = metrics.remainingSeconds
                val timeText = when {
                    total == null -> context.getString(R.string.download_time_unknown)
                    eta != null -> context.getString(R.string.download_remaining, DownloadMetricFormat.duration(eta))
                    metrics.bytesPerSecond <= 0.0 && metrics.downloadedBytes > 0L -> context.getString(R.string.download_waiting)
                    else -> context.getString(R.string.download_estimating)
                }
                "$sizeText\n${DownloadMetricFormat.rate(metrics.bytesPerSecond)} · $timeText"
            }
            item.status == DownloadCenter.STATUS_DONE -> downloaded
            else -> ""
        }
        if (audioStyle) {
            b.speed.text = when {
                active -> {
                    val percent = if (total != null && total > 0L) "${metrics.progressPercent}% · " else ""
                    "$percent${b.speed.text}\n${item.quality} • $statusLabel"
                }
                item.status == DownloadCenter.STATUS_DONE -> listOfNotNull(
                    item.quality.takeIf { it.isNotBlank() },
                    downloaded
                ).joinToString(" • ")
                else -> statusLabel
            }
        }
        b.overflowButton.visibility = if (item.status == DownloadCenter.STATUS_DONE) View.VISIBLE else View.GONE
        b.overflowButton.setOnClickListener { anchor ->
            PopupMenu(context, anchor).apply {
                menu.add(0, 1, 0, R.string.download_open)
                menu.add(0, 2, 1, R.string.download_share)
                menu.add(0, 3, 2, R.string.download_delete)
                setOnMenuItemClickListener { action ->
                    when (action.itemId) {
                        1 -> onClick(item)
                        2 -> DownloadSharing.share(context, item)
                        3 -> onLongClick(item) // Preserve Library's existing delete confirmation.
                    }
                    true
                }
                show()
            }
        }
        Thumbs.load(b.thumb, item.thumbnailUrl)
        b.root.setOnClickListener { if (item.status == DownloadCenter.STATUS_DONE) onClick(item) }
        b.root.setOnLongClickListener { onLongClick(item); true }
    }
}
