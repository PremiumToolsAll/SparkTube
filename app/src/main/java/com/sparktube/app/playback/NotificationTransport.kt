package com.sparktube.app.playback

import androidx.media3.common.Player

/** Notification taps are discrete commands, not headset single/double-tap gestures. */
internal object NotificationTransport {
    // Android KeyEvent constants; kept numeric here so the dispatch policy is JVM-testable.
    private const val ACTION_DOWN = 0
    private const val KEYCODE_MEDIA_PLAY_PAUSE = 85

    fun handle(
        player: Player,
        notificationController: Boolean,
        action: Int,
        keyCode: Int,
        repeatCount: Int
    ): Boolean {
        if (!notificationController || action != ACTION_DOWN || keyCode != KEYCODE_MEDIA_PLAY_PAUSE) {
            return false
        }
        // Do not turn held-key repeats into more toggles or let them enter Media3's timer.
        if (repeatCount != 0 || !player.isCommandAvailable(Player.COMMAND_PLAY_PAUSE)) return true
        val state = player.playbackState
        if (player.playWhenReady && state != Player.STATE_IDLE && state != Player.STATE_ENDED) {
            player.pause()
        } else {
            // Preserve native Play behavior for an idle or completed source.
            if (state == Player.STATE_IDLE && player.isCommandAvailable(Player.COMMAND_PREPARE)) {
                player.prepare()
            } else if (state == Player.STATE_ENDED && player.isCommandAvailable(Player.COMMAND_SEEK_TO_DEFAULT_POSITION)) {
                player.seekToDefaultPosition()
            }
            player.play()
        }
        return true // Consumed: Media3 must not delay or execute this tap a second time.
    }
}
