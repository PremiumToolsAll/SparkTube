package com.sparktube.app.playback;

/**
 * Explicit forwarding is essential: Kotlin `Player.Listener by delegate` inherits
 * Java default no-ops instead of forwarding them with our current Kotlin compiler.
 * That swallowed onRenderedFirstFrame/onTracksChanged and left PlayerView's shutter black.
 * Keep every Player.Listener callback here; PlayerListenerBridgeTest checks API coverage.
 */
@SuppressWarnings("deprecation")
class PlayerListenerBridge implements androidx.media3.common.Player.Listener {
    private final androidx.media3.common.Player.Listener delegate;

    PlayerListenerBridge(androidx.media3.common.Player.Listener delegate) {
        this.delegate = delegate;
    }

    @Override public void onEvents(androidx.media3.common.Player arg0, androidx.media3.common.Player.Events arg1) {
        delegate.onEvents(arg0, arg1);
    }

    @Override public void onTimelineChanged(androidx.media3.common.Timeline arg0, int arg1) {
        delegate.onTimelineChanged(arg0, arg1);
    }

    @Override public void onMediaItemTransition(androidx.media3.common.MediaItem arg0, int arg1) {
        delegate.onMediaItemTransition(arg0, arg1);
    }

    @Override public void onTracksChanged(androidx.media3.common.Tracks arg0) {
        delegate.onTracksChanged(arg0);
    }

    @Override public void onMediaMetadataChanged(androidx.media3.common.MediaMetadata arg0) {
        delegate.onMediaMetadataChanged(arg0);
    }

    @Override public void onPlaylistMetadataChanged(androidx.media3.common.MediaMetadata arg0) {
        delegate.onPlaylistMetadataChanged(arg0);
    }

    @Override public void onIsLoadingChanged(boolean arg0) {
        delegate.onIsLoadingChanged(arg0);
    }

    @Override public void onLoadingChanged(boolean arg0) {
        delegate.onLoadingChanged(arg0);
    }

    @Override public void onAvailableCommandsChanged(androidx.media3.common.Player.Commands arg0) {
        delegate.onAvailableCommandsChanged(arg0);
    }

    @Override public void onTrackSelectionParametersChanged(androidx.media3.common.TrackSelectionParameters arg0) {
        delegate.onTrackSelectionParametersChanged(arg0);
    }

    @Override public void onPlayerStateChanged(boolean arg0, int arg1) {
        delegate.onPlayerStateChanged(arg0, arg1);
    }

    @Override public void onPlaybackStateChanged(int arg0) {
        delegate.onPlaybackStateChanged(arg0);
    }

    @Override public void onPlayWhenReadyChanged(boolean arg0, int arg1) {
        delegate.onPlayWhenReadyChanged(arg0, arg1);
    }

    @Override public void onPlaybackSuppressionReasonChanged(int arg0) {
        delegate.onPlaybackSuppressionReasonChanged(arg0);
    }

    @Override public void onIsPlayingChanged(boolean arg0) {
        delegate.onIsPlayingChanged(arg0);
    }

    @Override public void onRepeatModeChanged(int arg0) {
        delegate.onRepeatModeChanged(arg0);
    }

    @Override public void onShuffleModeEnabledChanged(boolean arg0) {
        delegate.onShuffleModeEnabledChanged(arg0);
    }

    @Override public void onPlayerError(androidx.media3.common.PlaybackException arg0) {
        delegate.onPlayerError(arg0);
    }

    @Override public void onPlayerErrorChanged(androidx.media3.common.PlaybackException arg0) {
        delegate.onPlayerErrorChanged(arg0);
    }

    @Override public void onPositionDiscontinuity(int arg0) {
        delegate.onPositionDiscontinuity(arg0);
    }

    @Override public void onPositionDiscontinuity(androidx.media3.common.Player.PositionInfo arg0, androidx.media3.common.Player.PositionInfo arg1, int arg2) {
        delegate.onPositionDiscontinuity(arg0, arg1, arg2);
    }

    @Override public void onPlaybackParametersChanged(androidx.media3.common.PlaybackParameters arg0) {
        delegate.onPlaybackParametersChanged(arg0);
    }

    @Override public void onSeekBackIncrementChanged(long arg0) {
        delegate.onSeekBackIncrementChanged(arg0);
    }

    @Override public void onSeekForwardIncrementChanged(long arg0) {
        delegate.onSeekForwardIncrementChanged(arg0);
    }

    @Override public void onMaxSeekToPreviousPositionChanged(long arg0) {
        delegate.onMaxSeekToPreviousPositionChanged(arg0);
    }

    @Override public void onAudioSessionIdChanged(int arg0) {
        delegate.onAudioSessionIdChanged(arg0);
    }

    @Override public void onAudioAttributesChanged(androidx.media3.common.AudioAttributes arg0) {
        delegate.onAudioAttributesChanged(arg0);
    }

    @Override public void onVolumeChanged(float arg0) {
        delegate.onVolumeChanged(arg0);
    }

    @Override public void onSkipSilenceEnabledChanged(boolean arg0) {
        delegate.onSkipSilenceEnabledChanged(arg0);
    }

    @Override public void onDeviceInfoChanged(androidx.media3.common.DeviceInfo arg0) {
        delegate.onDeviceInfoChanged(arg0);
    }

    @Override public void onDeviceVolumeChanged(int arg0, boolean arg1) {
        delegate.onDeviceVolumeChanged(arg0, arg1);
    }

    @Override public void onVideoSizeChanged(androidx.media3.common.VideoSize arg0) {
        delegate.onVideoSizeChanged(arg0);
    }

    @Override public void onSurfaceSizeChanged(int arg0, int arg1) {
        delegate.onSurfaceSizeChanged(arg0, arg1);
    }

    @Override public void onRenderedFirstFrame() {
        delegate.onRenderedFirstFrame();
    }

    @Override public void onCues(java.util.List<androidx.media3.common.text.Cue> arg0) {
        delegate.onCues(arg0);
    }

    @Override public void onCues(androidx.media3.common.text.CueGroup arg0) {
        delegate.onCues(arg0);
    }

    @Override public void onMetadata(androidx.media3.common.Metadata arg0) {
        delegate.onMetadata(arg0);
    }
}
