package com.sparktube.app.download

import android.content.ClipData
import android.content.Context
import android.content.Intent
import android.widget.Toast
import androidx.core.content.FileProvider
import com.sparktube.app.R
import com.sparktube.app.data.DownloadRecord
import java.io.File

object DownloadSharing {
    fun share(context: Context, record: DownloadRecord) {
        val files = record.filePaths.map(::File).filter { it.isFile && it.canRead() }
        if (files.isEmpty()) {
            Toast.makeText(context, R.string.download_file_missing, Toast.LENGTH_SHORT).show()
            return
        }
        try {
            val uris = ArrayList(files.map {
                FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", it)
            })
            val intent = if (uris.size == 1) Intent(Intent.ACTION_SEND).apply {
                type = mime(files.first())
                putExtra(Intent.EXTRA_STREAM, uris.first())
            } else Intent(Intent.ACTION_SEND_MULTIPLE).apply {
                // AV downloads are two separate tracks, not a muxed movie.
                type = "*/*"
                putParcelableArrayListExtra(Intent.EXTRA_STREAM, uris)
            }
            intent.clipData = ClipData.newUri(context.contentResolver, record.title, uris.first()).apply {
                uris.drop(1).forEach { addItem(ClipData.Item(it)) }
            }
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            context.startActivity(Intent.createChooser(intent, context.getString(R.string.download_share)))
        } catch (_: Exception) {
            Toast.makeText(context, R.string.download_share_unavailable, Toast.LENGTH_SHORT).show()
        }
    }

    private fun mime(file: File): String = when (file.extension.lowercase()) {
        "mp4", "m4v" -> "video/mp4"
        "m4a" -> "audio/mp4"
        "mp3" -> "audio/mpeg"
        "aac" -> "audio/aac"
        "ogg", "opus" -> "audio/ogg"
        "wav" -> "audio/wav"
        else -> "application/octet-stream"
    }
}
