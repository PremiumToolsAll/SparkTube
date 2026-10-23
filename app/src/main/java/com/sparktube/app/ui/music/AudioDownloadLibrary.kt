package com.sparktube.app.ui.music

import com.sparktube.app.data.DownloadRecord
import com.sparktube.app.download.DownloadCenter
import java.io.File

/** All audio transfers stay visible; only completed, present files enter the music queue. */
internal object AudioDownloadLibrary {
    fun rows(downloads: List<DownloadRecord>): List<DownloadRecord> =
        downloads.filter { it.type == DownloadCenter.TYPE_AUDIO }

    fun playable(
        downloads: List<DownloadRecord>,
        fileExists: (String) -> Boolean = { File(it).isFile }
    ): List<Pair<DownloadRecord, String>> = rows(downloads).mapNotNull { record ->
        if (record.status != DownloadCenter.STATUS_DONE) return@mapNotNull null
        val path = record.filePaths.firstOrNull(fileExists) ?: return@mapNotNull null
        record to path
    }
}
