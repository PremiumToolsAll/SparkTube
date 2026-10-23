#!/usr/bin/env python3
"""Source checks only: no Android notification rendering/latency is measured here."""
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'app/src/main/java/com/sparktube/app'
CENTER = (SRC / 'playback/PlaybackCenter.kt').read_text()

def section(start, end):
    return CENTER.split(start, 1)[1].split(end, 1)[0]

class NotificationResponseChecks(unittest.TestCase):
    def test_toggle_uses_play_intent_not_decoded_frame_state(self):
        body = section('fun togglePlayPause()', 'fun seekTo(positionMs: Long)')
        self.assertIn('val p = sessionPlayer', body)
        self.assertIn('if (p.playWhenReady) p.pause() else p.play()', body)
        self.assertNotIn('if (p.isPlaying)', body)

    def test_queue_selection_stops_old_sound_before_async_resolve(self):
        body = section('private fun resolveCurrent()', '/** Tracks + broadcasts')
        self.assertLess(body.index('pendingVideo.begin()'), body.index('playerRef?.pause()'))
        self.assertLess(body.index('playerRef?.pause()'), body.index('scope.launch'))
        self.assertIn('pendingVideo.complete(requestToken)', body)

    def test_session_reports_pending_buffering_not_fake_playing(self):
        body = section('private class QueueForwardingPlayer', 'override fun addListener')
        self.assertIn('if (videoRequestPending) Player.STATE_BUFFERING', body)
        self.assertIn('!videoRequestPending && super.isPlaying()', body)
        self.assertIn('pendingVideo.playWhenReady', body)
        self.assertIn('PlaybackCenter.currentEntry', body)
        self.assertIn('.setTitle(entry.title)', body)

    def test_pending_pause_survives_both_online_and_local_source_application(self):
        self.assertEqual(CENTER.count('playWhenReady = if (videoRequestPending) pendingVideo.playWhenReady else true'), 2)

    def test_state_changes_emit_individual_and_aggregate_session_callbacks(self):
        body = section('fun refreshSessionState()', 'override fun addListener')
        for name in ['onPlayWhenReadyChanged', 'onPlaybackStateChanged', 'onIsPlayingChanged', 'onMediaMetadataChanged', 'onEvents']:
            self.assertIn(name, body)
        for event in ['EVENT_PLAY_WHEN_READY_CHANGED', 'EVENT_PLAYBACK_STATE_CHANGED', 'EVENT_IS_PLAYING_CHANGED', 'EVENT_MEDIA_METADATA_CHANGED']:
            self.assertIn(event, body)
        self.assertIn('forwardingPlayer?.refreshSessionState()', CENTER)
        self.assertNotIn('postDelayed', body)

    def test_native_queue_transport_is_preserved(self):
        body = section('private class QueueForwardingPlayer', '/** The wrapper for')
        for method in ['seekToNext()', 'seekToNextMediaItem()', 'seekToPrevious()', 'seekToPreviousMediaItem()']:
            self.assertIn('override fun ' + method, body)
        self.assertIn('PlaybackCenter.next()', body)
        self.assertIn('PlaybackCenter.previous()', body)
        service = (SRC / 'playback/PlaybackService.kt').read_text()
        self.assertIn('PlaybackCenter.sessionPlayer', service)
        self.assertIn('.setCustomLayout(emptyList())', service)

    def test_mode_exit_and_stop_invalidate_pending_request(self):
        self.assertIn('private fun stopPlayerNow() {\n        pendingVideo.cancel()', CENTER)
        self.assertIn('fun stopPlayback() {\n        pendingVideo.cancel()', CENTER)
        self.assertIn('!videoRequestPending && playbackState == Player.STATE_ENDED', CENTER)

    def test_existing_feature_files_unchanged_except_explicit_scope(self):
        allowed = {
            'app/src/main/java/com/sparktube/app/playback/PlaybackCenter.kt',
            'app/src/main/java/com/sparktube/app/data/YtRepository.kt',
            'app/src/main/java/com/sparktube/app/ui/home/HomeFragment.kt',
            'app/src/main/java/com/sparktube/app/ui/MainActivity.kt',
            'app/src/main/java/com/sparktube/app/ui/library/LibraryFragment.kt',
            'app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt',
            'app/src/main/java/com/sparktube/app/ui/player/PlayerGestureMath.kt',
            'app/src/test/java/com/sparktube/app/ui/player/PlayerGestureMathTest.kt',
        }
        with zipfile.ZipFile(ROOT.parent / 'SparkTube-1.4.1-pip-fixed-source.zip') as old:
            changed = []
            for name in old.namelist():
                rel = name.removeprefix('SparkTube-main/')
                if not (rel.startswith('app/') or rel.endswith('.gradle.kts') or rel == 'gradle.properties'):
                    continue
                path = ROOT / rel
                if not path.is_file() or path.read_bytes() != old.read(name):
                    changed.append(rel)
            self.assertFalse(set(changed) - allowed, changed)
            self.assertIn('app/src/main/java/com/sparktube/app/playback/PlaybackCenter.kt', changed)

if __name__ == '__main__':
    unittest.main(verbosity=2)
