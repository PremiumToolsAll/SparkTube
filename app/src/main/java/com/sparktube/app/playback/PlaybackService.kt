package com.sparktube.app.playback

import android.app.PendingIntent
import android.content.Intent
import android.os.Bundle
import android.view.KeyEvent
import androidx.annotation.OptIn
import androidx.core.content.IntentCompat
import androidx.media3.common.util.UnstableApi
import androidx.media3.session.MediaConstants
import androidx.media3.session.MediaSession
import androidx.media3.session.MediaSessionService
import androidx.media3.session.SessionCommand
import androidx.media3.session.SessionResult
import com.google.common.util.concurrent.Futures
import com.google.common.util.concurrent.ListenableFuture
import com.sparktube.app.ui.MainActivity
import com.sparktube.app.ui.music.NowPlayingActivity

/**
 * Background playback with native previous / play-pause / next controls.
 * The session uses the app-queue-aware player, including for videos whose
 * raw ExoPlayer timeline contains only the current item. Next changes tracks;
 * it is not a ten-second seek. Favorites remain available inside the app.
 */
@OptIn(UnstableApi::class)
class PlaybackService : MediaSessionService() {

    private var mediaSession: MediaSession? = null
    private val playbackListener = object : PlaybackCenter.Listener {
        override fun onItemChanged(entry: QueueEntry?) {
            updateSessionActivity()
        }
    }

    override fun onCreate() {
        super.onCreate()
        PlaybackCenter.init(this)
        mediaSession = MediaSession.Builder(this, PlaybackCenter.sessionPlayer)
            .setCallback(SessionCallback())
            .setSessionActivity(sessionActivity())
            // Android 13+ keeps the transport slots instead of filling a
            // missing Next slot with a custom favorite/heart action.
            .setSessionExtras(Bundle().apply {
                putBoolean(MediaConstants.EXTRAS_KEY_SLOT_RESERVATION_SEEK_TO_PREV, true)
                putBoolean(MediaConstants.EXTRAS_KEY_SLOT_RESERVATION_SEEK_TO_NEXT, true)
            })
            .setCustomLayout(emptyList())
            .build()
        PlaybackCenter.addListener(playbackListener)
    }

    /** Opens the music view for audio, or the main app for video playback. */
    private fun sessionActivity(): PendingIntent {
        val target = if (PlaybackCenter.mode == PlaybackCenter.Mode.AUDIO) {
            NowPlayingActivity::class.java
        } else {
            MainActivity::class.java
        }
        val intent = Intent(this, target).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
        return PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )
    }

    private fun updateSessionActivity() {
        mediaSession?.setSessionActivity(sessionActivity())
    }

    override fun onGetSession(controllerInfo: MediaSession.ControllerInfo): MediaSession? =
        mediaSession

    override fun onDestroy() {
        PlaybackCenter.removeListener(playbackListener)
        mediaSession?.release()
        mediaSession = null
        super.onDestroy()
    }

    private inner class SessionCallback : MediaSession.Callback {
        override fun onMediaButtonEvent(
            session: MediaSession,
            controllerInfo: MediaSession.ControllerInfo,
            intent: Intent
        ): Boolean {
            if (intent.action != Intent.ACTION_MEDIA_BUTTON) return false
            val event = IntentCompat.getParcelableExtra(intent, Intent.EXTRA_KEY_EVENT, KeyEvent::class.java)
                ?: return false
            // Media3 1.3.1 otherwise waits for a possible double-tap, and a
            // second quick notification tap can become Next. Only bypass that
            // gesture recognizer for the notification controller, not headsets.
            return NotificationTransport.handle(
                session.player,
                session.isMediaNotificationController(controllerInfo),
                event.action,
                event.keyCode,
                event.repeatCount
            )
        }

        override fun onConnect(
            session: MediaSession,
            controller: MediaSession.ControllerInfo
        ): MediaSession.ConnectionResult {
            // Retain the existing custom command API for external controllers;
            // the visible notification uses only native transport controls.
            val sessionCommands = MediaSession.ConnectionResult.DEFAULT_SESSION_COMMANDS.buildUpon()
                .add(SessionCommand(ACTION_FAV, Bundle.EMPTY))
                .add(SessionCommand(ACTION_PREV, Bundle.EMPTY))
                .add(SessionCommand(ACTION_NEXT, Bundle.EMPTY))
                .build()
            return MediaSession.ConnectionResult.AcceptedResultBuilder(session)
                .setAvailableSessionCommands(sessionCommands)
                .build()
        }

        override fun onCustomCommand(
            session: MediaSession,
            controller: MediaSession.ControllerInfo,
            customCommand: SessionCommand,
            args: Bundle
        ): ListenableFuture<SessionResult> {
            return when (customCommand.customAction) {
                ACTION_FAV -> {
                    PlaybackCenter.toggleFavoriteCurrent()
                    Futures.immediateFuture(SessionResult(SessionResult.RESULT_SUCCESS))
                }
                ACTION_PREV -> {
                    PlaybackCenter.previous()
                    Futures.immediateFuture(SessionResult(SessionResult.RESULT_SUCCESS))
                }
                ACTION_NEXT -> {
                    PlaybackCenter.next()
                    Futures.immediateFuture(SessionResult(SessionResult.RESULT_SUCCESS))
                }
                else -> Futures.immediateFuture(
                    SessionResult(SessionResult.RESULT_ERROR_NOT_SUPPORTED)
                )
            }
        }
    }

    companion object {
        const val ACTION_FAV = "com.sparktube.app.action.FAVORITE"
        const val ACTION_PREV = "com.sparktube.app.action.PREVIOUS"
        const val ACTION_NEXT = "com.sparktube.app.action.NEXT"
    }
}
