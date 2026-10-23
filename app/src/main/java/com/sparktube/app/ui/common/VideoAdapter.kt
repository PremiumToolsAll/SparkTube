package com.sparktube.app.ui.common

import android.content.Intent
import android.view.LayoutInflater
import android.view.ViewGroup
import android.widget.Toast
import androidx.appcompat.widget.PopupMenu
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.sparktube.app.R
import com.sparktube.app.data.LocalStore
import com.sparktube.app.databinding.ItemVideoBinding
import com.sparktube.app.util.Thumbs

class VideoAdapter(
    private val onClick: (VideoUiModel) -> Unit,
    private val onLongClick: ((VideoUiModel) -> Boolean)? = null,
    private val onDownload: ((VideoUiModel) -> Unit)? = null
) : ListAdapter<VideoUiModel, VideoAdapter.VH>(DIFF) {

    companion object {
        private val DIFF = object : DiffUtil.ItemCallback<VideoUiModel>() {
            override fun areItemsTheSame(a: VideoUiModel, b: VideoUiModel): Boolean =
                a.url == b.url

            override fun areContentsTheSame(a: VideoUiModel, b: VideoUiModel): Boolean =
                a.url == b.url && a.title == b.title && a.viewsLabel == b.viewsLabel
        }
    }

    class VH(val binding: ItemVideoBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH =
        VH(ItemVideoBinding.inflate(LayoutInflater.from(parent.context), parent, false))

    override fun onBindViewHolder(holder: VH, position: Int) {
        val item = getItem(position)
        val b = holder.binding

        b.title.text = item.title
        val metaParts = listOf(item.uploader, item.viewsLabel, item.uploadDate).filter { it.isNotBlank() }
        b.meta.text = metaParts.joinToString(" • ")

        if (item.durationLabel.isEmpty()) {
            b.duration.visibility = android.view.View.GONE
        } else {
            b.duration.visibility = android.view.View.VISIBLE
            b.duration.text = item.durationLabel
        }

        Thumbs.load(b.thumbnail, item.thumbnailUrl)
        Thumbs.load(b.avatar, item.uploaderAvatarUrl)

        b.overflowButton.contentDescription = b.root.context.getString(R.string.video_more_options, item.title)
        b.overflowButton.setOnClickListener { anchor ->
            val context = anchor.context
            PopupMenu(context, anchor).apply {
                menu.add(0, 1, 0, R.string.cd_play)
                menu.add(0, 5, 1, R.string.action_download)
                // Library/playlist screens own removal and refresh of their lists.
                // Expose those existing callbacks only after a deliberate menu choice.
                if (onLongClick != null) {
                    menu.add(0, 4, 4, R.string.video_remove_from_list)
                } else {
                    menu.add(0, 2, 2, if (LocalStore.isFavorite(context, item.url))
                        R.string.video_remove_favorite else R.string.action_favorite)
                }
                menu.add(0, 3, 3, R.string.action_share)
                setOnMenuItemClickListener { action ->
                    when (action.itemId) {
                        1 -> onClick(item)
                        5 -> if (onDownload != null) onDownload.invoke(item)
                            else VideoDownloadAction.start(context, item)
                        2 -> {
                            val added = LocalStore.toggleFavorite(context, item.toEntry())
                            Toast.makeText(context, if (added) R.string.added_to_favorites
                                else R.string.removed_from_favorites, Toast.LENGTH_SHORT).show()
                        }
                        3 -> context.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply {
                            type = "text/plain"
                            putExtra(Intent.EXTRA_TEXT, item.url)
                        }, context.getString(R.string.share_via)))
                        4 -> onLongClick?.invoke(item)
                        else -> return@setOnMenuItemClickListener false
                    }
                    true
                }
                show()
            }
        }
        b.root.setOnClickListener { onClick(item) }
        b.root.setOnLongClickListener {
            onLongClick?.invoke(item) ?: false
        }
    }
}
