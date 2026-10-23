package com.sparktube.app.ui.music

import com.sparktube.app.data.DownloadRecord
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class AudioDownloadLibraryTest {
    private fun record(id: String = "song", type: String = "AUDIO", status: String = "DONE", paths: List<String> = listOf("/music/$id.m4a")) =
        DownloadRecord(id, "Title $id", "Artist", "", type, "128 kbps", status, paths, listOf(id.hashCode().toLong()))

    @Test fun rowsKeepEveryAudioStatusAndExcludeVideoAndAv() {
        val audio = listOf("PENDING", "RUNNING", "PAUSED", "DONE", "FAILED").map { record(it, status = it) }
        assertEquals(audio, AudioDownloadLibrary.rows(audio + record(type = "VIDEO") + record(type = "AV")))
    }

    @Test fun partialFilesAreNeverPlayableOrCountedAsSongs() {
        val partials = listOf("PENDING", "RUNNING", "PAUSED", "FAILED").map { record(it, status = it) }
        assertTrue(AudioDownloadLibrary.playable(partials) { true }.isEmpty())
    }

    @Test fun onlyCompletedPresentAudioEntersPlayAll() {
        val done = record("present")
        val mixed = listOf(record("partial", status = "RUNNING"), record("missing"), done,
            record("video", type = "VIDEO"), record("pair", type = "AV"))
        assertEquals(listOf(done to "/music/present.m4a"), AudioDownloadLibrary.playable(mixed) { it.contains("present") })
    }

    @Test fun playableQueuePreservesVisibleOrderAndQualityVariants() {
        val newer = record("new")
        val older = record("old")
        val variant = older.copy(quality = "256 kbps", filePaths = listOf("/music/old-high.m4a"))
        assertEquals(listOf(newer, older, variant), AudioDownloadLibrary.playable(listOf(newer, older, variant)) { true }.map { it.first })
    }

    @Test fun selectsFirstExistingPathRatherThanFirstMissingPath() {
        val item = record(paths = listOf("/missing.m4a", "/present.m4a"))
        assertEquals(listOf(item to "/present.m4a"), AudioDownloadLibrary.playable(listOf(item)) { it == "/present.m4a" })
    }

    @Test fun emptyAndPathlessRecordsAreSafe() {
        assertTrue(AudioDownloadLibrary.rows(emptyList()).isEmpty())
        assertTrue(AudioDownloadLibrary.playable(emptyList()) { true }.isEmpty())
        assertTrue(AudioDownloadLibrary.playable(listOf(record(paths = emptyList()))) { true }.isEmpty())
    }

    @Test fun missingCompletedFileStaysVisibleForDeleteButIsNotQueued() {
        val missing = record()
        assertEquals(listOf(missing), AudioDownloadLibrary.rows(listOf(missing)))
        assertTrue(AudioDownloadLibrary.playable(listOf(missing)) { false }.isEmpty())
    }

    @Test fun finishingTransferEntersQueueAndDeletingRemovesIt() {
        val active = record(status = "RUNNING")
        assertTrue(AudioDownloadLibrary.playable(listOf(active)) { true }.isEmpty())
        val done = active.copy(status = "DONE")
        assertEquals(listOf(done), AudioDownloadLibrary.playable(listOf(done)) { true }.map { it.first })
        assertTrue(AudioDownloadLibrary.playable(emptyList()) { true }.isEmpty())
    }
}
