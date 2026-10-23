#!/usr/bin/env python3
"""Source wiring/scope checks only; these do not measure Android tap latency."""
from pathlib import Path
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'app/src/main/java/com/sparktube/app'

class FirstTapChecks(unittest.TestCase):
    def test_service_consumes_notification_toggle_in_callback(self):
        text = (SRC / 'playback/PlaybackService.kt').read_text()
        body = text.split('override fun onMediaButtonEvent(', 1)[1].split('override fun onConnect(', 1)[0]
        for part in ['Intent.ACTION_MEDIA_BUTTON', 'Intent.EXTRA_KEY_EVENT', 'IntentCompat.getParcelableExtra',
                     'return NotificationTransport.handle(', 'session.player',
                     'session.isMediaNotificationController(controllerInfo)', 'event.action', 'event.keyCode', 'event.repeatCount']:
            self.assertIn(part, body)
        self.assertNotIn('postDelayed', body)

    def test_direct_handler_has_no_async_or_network_work(self):
        text = (SRC / 'playback/NotificationTransport.kt').read_text()
        for part in ['!notificationController', 'action != ACTION_DOWN', 'keyCode != KEYCODE_MEDIA_PLAY_PAUSE',
                     'repeatCount != 0', 'Player.COMMAND_PLAY_PAUSE', 'player.playWhenReady', 'player.pause()', 'player.play()']:
            self.assertIn(part, text)
        for part in ['postDelayed', 'launch(', 'Thread.sleep', 'YtRepository', 'isPlaying']:
            self.assertNotIn(part, text)

    def test_downloads_audio_opens_exact_existing_local_file(self):
        text = (SRC / 'ui/library/LibraryFragment.kt').read_text()
        self.assertIn('onClick = { record -> openDownload(record) }', text)
        body = text.split('private fun openDownload(', 1)[1].split('private fun bindPlaylists()', 1)[0]
        for part in ['record.type != DownloadCenter.TYPE_AUDIO', 'PlaybackCenter.playDownload(record)',
                     'AudioDownloadLibrary.playable(listOf(record))', 'url = "file://$path"',
                     'PlaybackCenter.playMusicQueue(', 'NowPlayingActivity.start(requireContext())', 'download_file_missing']:
            self.assertIn(part, body)

    def test_audio_downloads_list_still_selects_tapped_file(self):
        text = (SRC / 'ui/music/MusicListActivity.kt').read_text()
        for part in ['AudioDownloadLibrary.playable(listOf(record))', 'entries.indexOfFirst { it.url == "file://$path" }',
                     'if (path != null && index >= 0) playQueue(index)']:
            self.assertIn(part, text)

    def test_latest_baseline_scope_preserves_all_other_app_files(self):
        allowed_changes = {
            'app/src/main/java/com/sparktube/app/playback/PlaybackService.kt',
            'app/src/main/java/com/sparktube/app/ui/library/LibraryFragment.kt',
        }
        allowed_new = {
            'app/src/main/java/com/sparktube/app/playback/NotificationTransport.kt',
            'app/src/test/java/com/sparktube/app/playback/NotificationTransportTest.kt',
        }
        baseline = ROOT.parent / 'SparkTube-1.4.1-fast-home-source.zip'
        if not baseline.exists():
            self.skipTest('Historical source ZIP needed only for scope comparison')
        with zipfile.ZipFile(baseline) as old:
            names = {n.removeprefix('SparkTube-main/'): n for n in old.namelist()}
            changed = set()
            for rel, name in names.items():
                if not (rel.startswith('app/src/') or rel.startswith('app/libs/') or rel.endswith('.gradle.kts') or rel == 'gradle.properties'):
                    continue
                path = ROOT / rel
                if not path.is_file() or path.read_bytes() != old.read(name):
                    changed.add(rel)
            self.assertEqual(changed, allowed_changes)
            added = {str(p.relative_to(ROOT)) for p in (ROOT / 'app/src').rglob('*') if p.is_file()} - set(names)
            self.assertEqual(added, allowed_new)

if __name__ == '__main__':
    unittest.main(verbosity=2)
