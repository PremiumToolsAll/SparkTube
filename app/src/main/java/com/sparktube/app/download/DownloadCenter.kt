package com.sparktube.app.download

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.widget.Toast
import com.sparktube.app.R
import com.sparktube.app.data.DownloadRecord
import com.sparktube.app.data.LocalStore
import com.sparktube.app.net.OkHttpDownloader
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.launch
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.IOException
import java.io.RandomAccessFile
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicLong

/**
 * Built-in download engine — no system DownloadManager.
 *
 * Every file is fetched with several parallel HTTP range connections (like
 * classic desktop accelerators), which makes full use of the available
 * bandwidth and finishes downloads several times faster than a single
 * stream, especially on high-latency links.
 *
 * Modes:
 *  - AUDIO  : a single audio stream file (m4a)
 *  - VIDEO  : a single video file (muxed mp4 when available, otherwise a
 *             higher-quality video-only mp4)
 *  - AV     : a video-only file + an audio file downloaded as a pair (both
 *             in parallel); they are played back together inside SparkTube
 */
object DownloadCenter {

    private const val TAG = "DownloadCenter"

    const val TYPE_AUDIO = "AUDIO"
    const val TYPE_VIDEO = "VIDEO"
    const val TYPE_AV = "AV"

    const val STATUS_PENDING = "PENDING"
    const val STATUS_RUNNING = "RUNNING"
    const val STATUS_PAUSED = "PAUSED"
    const val STATUS_DONE = "DONE"
    const val STATUS_FAILED = "FAILED"

    /** Parallel connections per file (acceleration factor). */
    private const val THREADS_PER_FILE = 6

    /** Minimum file size (bytes) below which parallel splitting is pointless. */
    private const val MIN_SIZE_FOR_SPLIT = 2L * 1024L * 1024L

    /** Chunk retry attempts before a download fails. */
    private const val CHUNK_RETRIES = 3

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    /** Shared engine client: generous dispatcher + connection pool for parallel range requests. */
    private val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(20, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .dispatcher(
            okhttp3.Dispatcher().apply {
                maxRequests = 32
                maxRequestsPerHost = 24
            }
        )
        .connectionPool(okhttp3.ConnectionPool(16, 5, TimeUnit.MINUTES))
        .build()

    /** All registry mutations run under this lock so the UI poller (main
     * thread) and job completion callbacks (IO threads) can never observe
     * half-synced state — e.g. flip a record back to FAILED after another
     * thread already marked it DONE. */
    private val syncLock = Any()

    private val mainHandler = Handler(Looper.getMainLooper())

    private val jobIdSeq = AtomicLong(System.currentTimeMillis())

    /** Live jobs by internal job id — the replacement for DownloadManager ids. */
    private val jobs = ConcurrentHashMap<Long, DownloadJob>()

    private var appCtx: Context? = null

    /** All registry records belonging to one video page. */
    fun recordsFor(context: Context, videoUrl: String): List<DownloadRecord> {
        val id = videoIdOf(videoUrl)
        return LocalStore.downloads(context).filter { it.videoId == id }
    }

    /** Whether the video page should show "Downloaded" instead of the option. */
    fun isDownloaded(context: Context, videoUrl: String): Boolean =
        recordsFor(context, videoUrl).any { it.status == STATUS_DONE }

    fun hasActiveDownload(context: Context, videoUrl: String): Boolean =
        recordsFor(context, videoUrl).any {
            it.status == STATUS_PENDING || it.status == STATUS_RUNNING || it.status == STATUS_PAUSED
        }

    /**
     * Aggregate progress (0..100) across all active records of one video.
     * Returns -1 when nothing is downloading.
     */
    fun downloadProgress(context: Context, videoUrl: String): Int {
        val active = recordsFor(context, videoUrl)
            .filter { it.status == STATUS_PENDING || it.status == STATUS_RUNNING || it.status == STATUS_PAUSED }
        if (active.isEmpty()) return -1
        val snapshots = active.map(::metrics)
        return calculateDownloadMetrics(
            snapshots.sumOf { it.downloadedBytes }, snapshots.map { it.totalBytes }, 0.0
        ).progressPercent
    }

    /** Progress for the live jobs belonging to one record, or zero if unknown. */
    fun progressPercent(record: DownloadRecord): Int {
        return metrics(record).progressPercent
    }

    /** Aggregate byte/rate/ETA metrics for a record, including paired AV jobs. */
    fun metrics(record: DownloadRecord): DownloadMetrics {
        val live = record.downloadIds.mapNotNull { jobs[it] }
        if (live.isEmpty()) {
            val lengths = record.filePaths.map { path -> File(path).takeIf { it.isFile }?.length() }
            val downloaded = lengths.filterNotNull().sum()
            val total = if (lengths.isNotEmpty() && lengths.all { it != null }) lengths.filterNotNull().sum() else null
            return calculateDownloadMetrics(downloaded, listOf(total), 0.0)
        }
        val downloaded = live.sumOf { it.progress.get() }
        val totals = record.downloadIds.map { id -> jobs[id]?.size?.takeIf { size -> size > 0L } }
        val rate = live.filterNot { it.finished.get() || it.paused.get() }.sumOf { it.bytesPerSecond() }
        return calculateDownloadMetrics(downloaded, totals, rate)
    }

    /** Deletes every download (files + registry). */
    fun clearAll(context: Context) = synchronized(syncLock) {
        jobs.values.forEach { it.cancel() }
        jobs.clear()
        LocalStore.downloads(context).forEach { record ->
            record.filePaths.forEach { path ->
                runCatching { File(path).delete() }
            }
        }
        LocalStore.clearDownloads(context)
    }

    /** Extracts a safe file-system friendly video id from a video URL. */
    fun videoIdOf(url: String): String {
        val fallback = url.replace(Regex("[^A-Za-z0-9_-]"), "").takeLast(20)
        val vParam = Regex("[?&]v=([A-Za-z0-9_-]{6,})").find(url)?.groupValues?.get(1)
        val shortLink = Regex("youtu\\.be/([A-Za-z0-9_-]{6,})").find(url)?.groupValues?.get(1)
        return (vParam ?: shortLink ?: fallback).take(20)
    }

    private fun dirOf(type: String): String = when (type) {
        TYPE_AUDIO -> android.os.Environment.DIRECTORY_MUSIC
        else -> android.os.Environment.DIRECTORY_MOVIES
    }

    /** @return the local file path of the destination. */
    private fun destinationPath(context: Context, fileName: String, type: String): String {
        val base = context.getExternalFilesDir(dirOf(type)) ?: context.filesDir
        return File(File(base, "SparkTube"), fileName).absolutePath
    }

    /** Starts a single-file download (AUDIO or VIDEO). */
    fun startSingle(
        context: Context,
        videoUrl: String,
        title: String,
        uploader: String,
        thumbUrl: String,
        type: String,
        quality: String,
        streamUrl: String,
        fileExt: String
    ) {
        appCtx = context.applicationContext
        val videoId = videoIdOf(videoUrl)
        val fileName = "${videoId}_${type}_${quality.replace(" ", "")}.$fileExt"
        val path = destinationPath(context, fileName, type)
        val job = DownloadJob(streamUrl, File(path))
        jobs[job.id] = job
        // Registry entry first, THEN the engine: a job that dies within
        // milliseconds is guaranteed to find its record when it reports back.
        LocalStore.addDownload(
            context,
            DownloadRecord(
                videoId = videoId,
                title = title,
                uploader = uploader,
                thumbnailUrl = thumbUrl,
                type = type,
                quality = quality,
                status = STATUS_PENDING,
                filePaths = listOf(path),
                downloadIds = listOf(job.id)
            )
        )
        job.start()
    }

    /** Starts a video+audio pair download (AV) — both files download in parallel. */
    fun startPair(
        context: Context,
        videoUrl: String,
        title: String,
        uploader: String,
        thumbUrl: String,
        quality: String,
        videoStreamUrl: String,
        audioStreamUrl: String
    ) {
        appCtx = context.applicationContext
        val videoId = videoIdOf(videoUrl)
        val videoJob = DownloadJob(videoStreamUrl, File(destinationPath(context, "${videoId}_AV_${quality.replace(" ", "")}_v.mp4", TYPE_AV)))
        val audioJob = DownloadJob(audioStreamUrl, File(destinationPath(context, "${videoId}_AV_${quality.replace(" ", "")}_a.m4a", TYPE_AV)))
        jobs[videoJob.id] = videoJob
        jobs[audioJob.id] = audioJob
        LocalStore.addDownload(
            context,
            DownloadRecord(
                videoId = videoId,
                title = title,
                uploader = uploader,
                thumbnailUrl = thumbUrl,
                type = TYPE_AV,
                quality = quality,
                status = STATUS_PENDING,
                filePaths = listOf(videoJob.file.absolutePath, audioJob.file.absolutePath),
                downloadIds = listOf(videoJob.id, audioJob.id)
            )
        )
        videoJob.start()
        audioJob.start()
    }

    /** Pause/resume live transfers; partial files and byte counters are kept in memory/on disk. */
    fun togglePause(context: Context, record: DownloadRecord) = synchronized(syncLock) {
        val active = record.downloadIds.mapNotNull { jobs[it] }
        if (active.isEmpty() || active.all { it.finished.get() } || active.any { it.failed.get() }) {
            syncLocked(context)
            return@synchronized
        }
        val pause = !active.filterNot { it.finished.get() }.all { it.paused.get() }
        active.forEach {
            it.resetSpeedSample()
            it.paused.set(pause)
        }
        LocalStore.updateDownloadStatus(context, record.downloadIds.first(), if (pause) STATUS_PAUSED else STATUS_RUNNING)
    }

    /** Legacy compatibility: decimal megabits/sec as before. */
    fun speedMbps(record: DownloadRecord): Double = metrics(record).bytesPerSecond * 8.0 / 1_000_000.0

    /** Deletes the files of a record and removes it from the registry. */
    fun delete(context: Context, record: DownloadRecord) = synchronized(syncLock) {
        record.downloadIds.forEach { id ->
            jobs.remove(id)?.cancel()
        }
        record.filePaths.forEach { path ->
            runCatching { File(path).delete() }
        }
        LocalStore.removeDownload(context, record)
    }

    /**
     * Re-syncs statuses of unfinished downloads with the live jobs. A record
     * turns DONE when every job finished and FAILED when any job failed (or
     * when its jobs vanished — e.g. the process was killed mid-download).
     *
     * Live jobs are only dropped from the map once a record reaches a
     * terminal state (DONE / FAILED). A mere PENDING → RUNNING transition
     * must keep them, otherwise the next poll would see an empty job list
     * and wrongly mark a still-running download as failed.
     */
    fun refreshStatuses(context: Context) = synchronized(syncLock) {
        syncLocked(context)
    }

    /**
     * Called from a job's own coroutine when it terminates (success, failure
     * or cancellation) so the registry flips to DONE / FAILED even when no
     * screen is currently polling.
     */
    private fun onJobTerminated(jobId: Long) {
        val ctx = appCtx ?: return
        synchronized(syncLock) {
            // Only records that actually reference this job need a re-sync.
            val affected = LocalStore.downloads(ctx)
                .filter { it.downloadIds.contains(jobId) }
            if (affected.isEmpty()) return
            syncLocked(ctx)
        }
    }

    /** The actual status sync — callers must hold [syncLock]. */
    private fun syncLocked(context: Context) {
        LocalStore.downloads(context).filter { it.status != STATUS_DONE && it.status != STATUS_FAILED }
            .forEach { record ->
                val recordJobs = record.downloadIds.mapNotNull { jobs[it] }
                val newStatus = when {
                    recordJobs.isEmpty() -> STATUS_FAILED
                    recordJobs.any { it.failed.get() } -> STATUS_FAILED
                    recordJobs.all { it.finished.get() } -> STATUS_DONE
                    recordJobs.filterNot { it.finished.get() }.all { it.paused.get() } -> STATUS_PAUSED
                    else -> STATUS_RUNNING
                }
                if (newStatus != record.status) {
                    LocalStore.updateDownloadStatus(context, record.downloadIds.first(), newStatus)
                    if (newStatus == STATUS_DONE || newStatus == STATUS_FAILED) {
                        // Terminal state: now the live jobs can go.
                        recordJobs.forEach {
                            jobs.remove(it.id)
                            if (newStatus == STATUS_FAILED) it.cancel()
                        }
                        if (newStatus == STATUS_DONE) {
                            announceDone(context)
                        }
                    }
                }
            }
    }

    private fun announceDone(context: Context) {
        val ctx = appCtx ?: context.applicationContext
        // May be reached from an IO thread: Toast needs a looper, so post it.
        mainHandler.post {
            Toast.makeText(ctx, R.string.download_status_done, Toast.LENGTH_SHORT).show()
        }
    }

    /**
     * One parallel-accelerated file download. Small files (or servers without
     * range support) gracefully fall back to a single connection.
     */
    private class DownloadJob(val url: String, val file: File) {
        val id = DownloadCenter.jobIdSeq.incrementAndGet()

        val progress = AtomicLong(0L)
        /** Total size, filled in once the first probe response arrives. */
        @Volatile
        var size: Long = 0L

        val finished = AtomicBoolean(false)
        val failed = AtomicBoolean(false)

        private var job: Job? = null
        private val cancelled = AtomicBoolean(false)
        val paused = AtomicBoolean(false)
        private val speedSampler = DownloadSpeedSampler()
        fun bytesPerSecond(): Double = speedSampler.bytesPerSecond(System.nanoTime())
        fun resetSpeedSample() {
            speedSampler.reset(System.nanoTime(), progress.get())
        }
        private suspend fun awaitActive() {
            while (paused.get() && !cancelled.get()) kotlinx.coroutines.delay(100)
            kotlinx.coroutines.currentCoroutineContext().ensureActive()
        }
        private fun countBytes(n: Int) {
            val cumulative = progress.addAndGet(n.toLong())
            speedSampler.onBytes(cumulative, System.nanoTime())
        }

        fun start() {
            file.parentFile?.mkdirs()
            // Never resume a stale partial file: start clean.
            runCatching { if (file.exists()) file.delete() }
            job = DownloadCenter.scope.launch {
                val ok = runCatching { downloadInternal() }
                    .onFailure { Log.w(TAG, "Download job #$id failed for $url", it) }
                    .getOrElse { false }
                if (ok && !cancelled.get()) {
                    // An unknown-length component now has an exact final size;
                    // keep it in a paired record's aggregate while its peer runs.
                    if (size <= 0L) size = progress.get()
                    finished.set(true)
                } else {
                    failed.set(true)
                    runCatching { file.delete() }
                }
                // Self-report termination so the record flips even without
                // a screen polling refreshStatuses().
                DownloadCenter.onJobTerminated(id)
            }
        }

        fun cancel() {
            cancelled.set(true)
            job?.cancel()
            runCatching { file.delete() }
        }

        private suspend fun downloadInternal(): Boolean = withContext(Dispatchers.IO) {
            // 1. Probe: total size + range support with a 1-byte range request.
            val probe = newRequest()
                .header("Range", "bytes=0-0")
                .build()
            val totalSize: Long
            val rangesSupported: Boolean
            DownloadCenter.client.newCall(probe).execute().use { resp ->
                if (!resp.isSuccessful) {
                    Log.w(TAG, "Probe failed: HTTP ${resp.code} for $url")
                    return@withContext false
                }
                val contentRange = resp.header("Content-Range")
                val acceptRanges = resp.header("Accept-Ranges")
                totalSize = contentRange
                    ?.substringAfterLast('/')
                    ?.toLongOrNull()
                    ?: if (resp.code == 200) resp.body?.contentLength()?.takeIf { it > 0L } ?: -1L else -1L
                // Accept-Ranges is only an advertisement; a 200 response to
                // our Range probe means ranges were not actually honored.
                rangesSupported = resp.code == 206 && contentRange != null
            }

            if (totalSize <= 0L) {
                // Unknown length: single plain stream copy.
                size = 0L
                return@withContext plainDownload()
            }

            size = totalSize
            if (!rangesSupported) {
                size = totalSize
                return@withContext plainDownload()
            }
            if (totalSize < MIN_SIZE_FOR_SPLIT) {
                return@withContext segmentedDownload(0L, totalSize - 1L)
            }

            // 2. Parallel range downloads.
            val chunkCount = THREADS_PER_FILE
            val bounds = (0 until chunkCount).map { i ->
                val start = totalSize * i / chunkCount
                val end = totalSize * (i + 1) / chunkCount - 1
                start to end
            }
            RandomAccessFile(file, "rw").use { raf ->
                raf.setLength(totalSize)
            }
            return@withContext coroutineScope {
                val results = bounds.map { (start, end) -> launchSegment(start, end) }
                results.map { segJob ->
                    segJob.job.join()
                    segJob.completed.get()
                }.all { it }
            }
        }

        private fun newRequest(): Request.Builder =
            Request.Builder()
                .url(url)
                .header("User-Agent", OkHttpDownloader.USER_AGENT)

        /** Plain single-connection download (no size known / no ranges). */
        private suspend fun plainDownload(): Boolean = withContext(Dispatchers.IO) {
            try {
                val request = newRequest().build()
                DownloadCenter.client.newCall(request).execute().use { resp ->
                    if (!resp.isSuccessful) {
                        Log.w(TAG, "Plain download failed: HTTP ${resp.code} for $url")
                        return@withContext false
                    }
                    val body = resp.body ?: return@withContext false
                    // Full GET length can be known even when the probe omitted
                    // Content-Range. Never use a one-byte 206 probe's length.
                    size = body.contentLength().takeIf { it > 0L } ?: 0L
                    file.outputStream().use { out ->
                        body.byteStream().use { input ->
                            val buf = ByteArray(64 * 1024)
                            while (true) {
                                if (cancelled.get()) return@withContext false
                                awaitActive()
                                val read = input.read(buf)
                                if (read < 0) break
                                out.write(buf, 0, read)
                                countBytes(read)
                            }
                            out.flush()
                        }
                    }
                }
                true
            } catch (e: kotlinx.coroutines.CancellationException) {
                throw e
            } catch (e: Exception) {
                Log.w(TAG, "Plain download error for $url", e)
                false
            }
        }

        /** One contiguous byte range, written at its offset. Retries a few times. */
        private fun kotlinx.coroutines.CoroutineScope.launchSegment(start: Long, end: Long): SegmentJob {
            val completedFlag = AtomicBoolean(false)
            val segJob = launch(Dispatchers.IO) {
                var attempt = 0
                var written = 0L
                while (attempt <= CHUNK_RETRIES && !cancelled.get()) {
                    try {
                        awaitActive()
                        currentCoroutineContext().ensureActive()
                        val request = newRequest()
                            .header("Range", "bytes=${start + written}-$end")
                            .build()
                        DownloadCenter.client.newCall(request).execute().use { resp ->
                            val range = resp.header("Content-Range")
                            val match = range?.let { Regex("bytes (\\d+)-(\\d+)/(\\d+|\\*)").matchEntire(it) }
                            if (resp.code != 206 || match == null ||
                                match.groupValues[1].toLongOrNull() != start + written ||
                                match.groupValues[2].toLongOrNull() != end ||
                                (match.groupValues[3] != "*" && match.groupValues[3].toLongOrNull() != size)) {
                                throw IOException("Invalid range response HTTP ${resp.code}: $range")
                            }
                            val body = resp.body ?: throw IOException("Empty body")
                            RandomAccessFile(file, "rw").use { raf ->
                                raf.seek(start + written)
                                val input = body.byteStream()
                                val buf = ByteArray(64 * 1024)
                                val expected = end - start + 1L
                                while (written < expected) {
                                    if (cancelled.get()) throw kotlinx.coroutines.CancellationException("Download cancelled")
                                    awaitActive()
                                    val read = input.read(buf, 0, minOf(buf.size.toLong(), expected - written).toInt())
                                    if (read < 0) throw IOException("Unexpected end of stream")
                                    raf.write(buf, 0, read)
                                    written += read.toLong()
                                    countBytes(read)
                                }
                            }
                            completedFlag.set(true)
                            return@launch
                        }
                    } catch (e: kotlinx.coroutines.CancellationException) {
                        throw e
                    } catch (e: Exception) {
                        attempt++
                        if (attempt > CHUNK_RETRIES) break
                        kotlinx.coroutines.delay(300L * attempt)
                    }
                }
            }
            return SegmentJob(segJob, completedFlag)
        }

        /** Single-range convenience wrapper (small files). */
        private suspend fun segmentedDownload(start: Long, end: Long): Boolean {
            RandomAccessFile(file, "rw").use { raf -> raf.setLength(end + 1) }
            return coroutineScope {
                val seg = launchSegment(start, end)
                seg.job.join()
                seg.completed.get()
            }
        }
    }

    /** Small holder: a segment coroutine + its success flag. */
    private class SegmentJob(val job: Job, val completed: AtomicBoolean)
}
