#!/usr/bin/env python3
"""Source checks, not Android runtime/UI/network tests."""
from pathlib import Path
import unittest
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'app/src/main/java/com/sparktube/app'
BASE = ROOT.parent / 'SparkTube-1.4.1-compact-toggle-source.zip'
A = '{http://schemas.android.com/apk/res/android}'

class AudioDownloadStructureTest(unittest.TestCase):
    def test_existing_app_changes_are_limited_to_two_classes(self):
        changed = []
        with zipfile.ZipFile(BASE) as previous:
            for name in previous.namelist():
                relative = name.removeprefix('SparkTube-main/')
                if not (relative.startswith('app/src/main/') or relative.startswith('app/libs/') or relative.endswith('.gradle.kts')):
                    continue
                path = ROOT / relative
                if not path.is_file() or path.read_bytes() != previous.read(name):
                    changed.append(relative)
        self.assertEqual(sorted(changed), [
            'app/src/main/java/com/sparktube/app/ui/common/DownloadAdapter.kt',
            'app/src/main/java/com/sparktube/app/ui/music/MusicListActivity.kt'])

    def test_shared_controls_are_opt_in_and_keep_all_actions(self):
        source = (SRC / 'ui/common/DownloadAdapter.kt').read_text()
        self.assertIn('private val audioStyle: Boolean = false', source)
        self.assertIn('if (audioStyle)', source)
        self.assertEqual(source.count('DownloadCenter.metrics(item)'), 1)
        for text in ['onPause?.invoke(item)', 'metrics.remainingSeconds', 'metrics.progressPercent',
                     'DownloadMetricFormat.rate(metrics.bytesPerSecond)', 'DownloadSharing.share(context, item)',
                     'R.string.download_open', 'R.string.download_delete']:
            self.assertIn(text, source)

    def test_audio_page_uses_live_adapter_and_stops_polling_when_hidden(self):
        source = (SRC / 'ui/music/MusicListActivity.kt').read_text()
        for text in ['audioStyle = true', 'AudioDownloadLibrary.rows(LocalStore.downloads(this))',
                     'downloadAdapter.refreshLiveMetrics()', 'postDelayed(this, 1000L)',
                     'override fun onPause()', 'override fun onDestroy()',
                     'binding.playAllButton.isEnabled = entries.isNotEmpty()',
                     'PlaybackCenter.playMusicQueue(entries, index)', 'NowPlayingActivity.start(this)',
                     'DownloadCenter.togglePause(this, record)', 'DownloadCenter.delete(this, record)']:
            self.assertIn(text, source)
        self.assertGreaterEqual(source.count('uiHandler.removeCallbacks(refreshDownloads)'), 3)

    def test_song_header_and_play_all_remain(self):
        tree = ET.parse(ROOT / 'app/src/main/res/layout/activity_music_list.xml')
        ids = {e.get(A + 'id', '').split('/')[-1] for e in tree.iter()}
        self.assertTrue({'title', 'subtitle', 'summaryRow', 'playAllButton', 'list', 'emptyView'} <= ids)

    def test_only_done_existing_audio_is_playable(self):
        source = (SRC / 'ui/music/AudioDownloadLibrary.kt').read_text()
        for text in ['it.type == DownloadCenter.TYPE_AUDIO', 'record.status != DownloadCenter.STATUS_DONE',
                     'File(it).isFile', 'record.filePaths.firstOrNull(fileExists)']:
            self.assertIn(text, source)

if __name__ == '__main__':
    unittest.main(verbosity=2)
