#!/usr/bin/env python3
"""Source/XML checks only, not Android execution."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import zipfile
R=Path(__file__).resolve().parents[1]
S=R/'app/src/main'
P=(S/'java/com/sparktube/app/playback/PlaybackCenter.kt').read_text()
A=(S/'java/com/sparktube/app/ui/music/NowPlayingActivity.kt').read_text()
V=(S/'java/com/sparktube/app/ui/player/PlayerActivity.kt').read_text()
T=(S/'java/com/sparktube/app/ui/music/SleepTimerSheet.kt').read_text()
class SleepTimerChecks(unittest.TestCase):
    def test_instant_video_to_audio_retains_source(self):
        body=P.split('fun switchToAudioOnly() {',1)[1].split('fun switchBackToVideo()',1)[0]
        for call in ['rebuildSource(', 'setMediaSource(', 'prepare()', 'seekTo(', 'stop()']:
            self.assertNotIn(call,body)
        self.assertIn('retainedVideoSourceForAudio = true',body)
        self.assertIn('NowPlayingActivity.start(this)',V)
    def test_xml_parses(self):
        for p in (S/'res').rglob('*.xml'): ET.parse(p)
    def test_both_entry_points_share_selector(self):
        for text in (A,V): self.assertIn('SleepTimerSheet(this).show()',text)
    def test_video_background_action_replaced(self):
        text=(S/'res/layout/activity_player.xml').read_text()
        self.assertIn('@+id/actionTimer',text)
        self.assertNotIn('@+id/actionBackground',text)
        self.assertNotIn('binding.actionBackground',V)
        self.assertIn('binding.modeSwitch.setOnClickListener { openAudioView() }',V)
    def test_exact_choices(self):
        self.assertIn('listOf(10, 15, 20, 30, 45, 60)',T)
        self.assertIn('sleep_timer_off',T)
        self.assertIn('setSleepTimerEndOfItem()',T)
    def test_countdown_both_screens(self):
        self.assertIn('bindTimer()',A)
        self.assertIn('SleepTimerSheet.buttonLabel(this@PlayerActivity)',V)
        self.assertIn('postDelayed(this, 1000)',V)
        self.assertIn('postDelayed(this, 500)',A)
    def test_monotonic_shared_countdown_and_wake_alarm(self):
        self.assertIn('SystemClock.elapsedRealtime()',P)
        self.assertIn('ELAPSED_REALTIME_WAKEUP',P)
        self.assertIn('private var sleepTimerJob: Job?',P)
    def test_stop_cancels_pending_work(self):
        stop=P.split('fun stopPlayback() {',1)[1].split('// ----- Quality',1)[0]
        for token in ('clearSleepTimer()', 'pendingVideo.cancel()', 'resolveJob?.cancel()', 'watchdogJob?.cancel()', 'prefetchJob?.cancel()', 'clearMediaItems()', 'mode = Mode.NONE'):
            self.assertIn(token,stop)
    def test_end_prevents_playlist_continuation(self):
        self.assertIn('PLAY_WHEN_READY_CHANGE_REASON_END_OF_MEDIA_ITEM',P)
        self.assertIn('sleepTimer.shouldStopAtEnd(currentEntry?.url)',P)
        self.assertIn('setPauseAtEndOfMediaItems(sleepTimer.mode == SleepTimerState.Mode.END_OF_ITEM',P)
    def test_no_new_permission_dependency_version_change(self):
        with zipfile.ZipFile(R.parent/'SparkTube-1.4.1-video-collapse-source.zip') as old:
            for rel in ['app/build.gradle.kts','build.gradle.kts','gradle.properties','app/src/main/AndroidManifest.xml']:
                self.assertEqual((R/rel).read_bytes(),old.read('SparkTube-main/'+rel))
    def test_scope_of_previous_file_changes(self):
        allowed={
            'app/src/main/java/com/sparktube/app/playback/PlaybackCenter.kt',
            'app/src/main/java/com/sparktube/app/ui/music/NowPlayingActivity.kt',
            'app/src/main/java/com/sparktube/app/ui/player/PlayerActivity.kt',
            'app/src/main/res/layout/activity_now_playing.xml',
            'app/src/main/res/layout/activity_player.xml',
        }
        with zipfile.ZipFile(R.parent/'SparkTube-1.4.1-video-collapse-source.zip') as old:
            changed={name.removeprefix('SparkTube-main/') for name in old.namelist() if name.startswith('SparkTube-main/app/src/') and (R/name.removeprefix('SparkTube-main/')).read_bytes()!=old.read(name)}
        self.assertEqual(changed,allowed)
if __name__=='__main__': unittest.main(verbosity=2)
