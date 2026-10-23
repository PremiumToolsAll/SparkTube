#!/usr/bin/env python3
"""Source-structure checks only, NOT Android rendering or touch tests."""
from pathlib import Path
import unittest
import zipfile
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
RES = ROOT/'app/src/main/res'
SRC = ROOT/'app/src/main/java/com/sparktube/app'
A = '{http://schemas.android.com/apk/res/android}'
APP = '{http://schemas.android.com/apk/res-auto}'
BASE = ROOT.parent/'SparkTube-1.4.1-player-fixed-source.zip'
def by_id(tree, name):
    return next((e for e in tree.iter() if e.get(A+'id', '').split('/')[-1] == name), None)
class PlayerStructureTest(unittest.TestCase):
    def test_all_xml_parses(self):
        for p in RES.rglob('*.xml'):
            ET.parse(p)
    def test_activity_owns_transport(self):
        tree = ET.parse(RES/'layout/activity_player.xml')
        group = by_id(tree, 'transportControls')
        self.assertIn(group, list(tree.getroot()))
        self.assertEqual([e.get(A+'id') for e in group], ['@+id/queuePrevious', '@+id/queuePlayPause', '@+id/queueNext'])
        self.assertEqual([e.get(A+'layout_width') for e in group], ['52dp', '76dp', '52dp'])
        for button in group:
            self.assertEqual(button.get(APP+'tint'), '@color/white')
        controller = ET.parse(RES/'layout/player_queue_controller.xml')
        for name in ['exo_play_pause', 'exo_prev', 'exo_next']:
            self.assertIsNone(by_id(controller, name))
        for name in ['exo_progress_placeholder', 'exo_position', 'exo_duration', 'exo_settings']:
            self.assertIsNotNone(by_id(controller, name))
    def test_texture_output_and_direct_player(self):
        for layout, name in [('activity_player.xml', 'playerView'), ('activity_main.xml', 'miniVideo')]:
            self.assertEqual(by_id(ET.parse(RES/'layout'/layout), name).get(APP+'surface_type'), 'texture_view')
        source = (SRC/'playback/PlaybackCenter.kt').read_text()
        self.assertIn('PlayerView.switchTargetView(outputPlayer, activePlayerView, view)', source)
        self.assertIn('if (activePlayerView !== view) return', source)
        self.assertIn('.setEnableDecoderFallback(true)', source)
        self.assertIn('object : PlayerListenerBridge(listener)', source)
        self.assertNotIn('object : Player.Listener by listener', source)
    def test_queue_actions_and_gestures(self):
        source = (SRC/'ui/player/PlayerActivity.kt').read_text()
        for button, command in [('queuePrevious', 'previous'), ('queueNext', 'next'), ('queuePlayPause', 'togglePlayPause')]:
            self.assertIn(f'binding.{button}.setOnClickListener {{\n            PlaybackCenter.{command}()', source)
        self.assertIn('binding.queueNext to Player.COMMAND_SEEK_TO_NEXT_MEDIA_ITEM', source)
        self.assertIn('binding.transportControls.isVisible = visible', source)
        self.assertIn('binding.transportControls.isVisible = false', source)
        for math in ['seekTarget', 'volume', 'brightness']:
            self.assertIn('PlayerGestureMath.'+math, source)
        self.assertIn('setShowRewindButton(false)', source)
        self.assertIn('setShowFastForwardButton(false)', source)
    def test_first_frame_monitor(self):
        source = (SRC/'playback/PlaybackCenter.kt').read_text()
        for text in ['if (p.isPlaying && videoFrameSeen)', 'videoFrameSeen = true\n            frameWatchJob?.cancel()',
                     '!p.playWhenReady || p.playbackState != Player.STATE_READY', '!view.isShown || !view.isAttachedToWindow',
                     'VideoFramePolicy.Action.SHOW_ERROR', 'usedFallback = c.muxed.isNotEmpty()',
                     'playWhenReady = wasPlaying || !keepPosition']:
            self.assertIn(text, source)
    def test_compact_mode_pills(self):
        for layout, active in [('activity_player.xml', 1), ('activity_now_playing.xml', 0)]:
            switch = by_id(ET.parse(RES/'layout'/layout), 'modeSwitch')
            self.assertEqual(switch.get(A+'layout_width'), '76dp')
            self.assertEqual(switch.get(A+'layout_height'), '48dp')
            self.assertEqual(switch.get(A+'background'), '@drawable/bg_mode_switch_hit_area')
            self.assertEqual(switch.get(A+'clickable'), 'true')
            self.assertEqual(switch.get(A+'focusable'), 'true')
            for child in switch:
                self.assertEqual(child.get(A+'layout_width'), '30dp')
                self.assertEqual(child.get(A+'layout_height'), '24dp')
                self.assertEqual(child[0].get(A+'layout_width'), '17dp')
                self.assertEqual(child[0].get(A+'layout_height'), '17dp')
            self.assertEqual(list(switch)[active].get(A+'background'), '@drawable/bg_mode_switch_active')
    def test_retry_visible(self):
        self.assertNotEqual(by_id(ET.parse(RES/'layout/activity_player.xml'), 'retryButton').get(A+'visibility'), 'gone')
    def test_download_metrics_and_actions(self):
        self.assertEqual(by_id(ET.parse(RES/'layout/item_download.xml'), 'overflowButton').get(A+'layout_height'), '48dp')
        source = (SRC/'ui/common/DownloadAdapter.kt').read_text()
        self.assertIn('DownloadCenter.metrics(item)', source)
        for name in ['download_open', 'download_share', 'download_delete']:
            self.assertIn('R.string.'+name, source)
        self.assertIn('metrics.remainingSeconds', source)
    def test_version_and_build_settings_unchanged(self):
        source = (ROOT/'app/build.gradle.kts').read_text()
        self.assertIn('versionCode = 10', source)
        self.assertIn('versionName = "1.4.1"', source)
        if BASE.exists():
            with zipfile.ZipFile(BASE) as archive:
                self.assertEqual(source, archive.read('SparkTube-main/app/build.gradle.kts').decode())
    @unittest.skipUnless(BASE.exists(), 'Previous source ZIP unavailable for byte-for-byte comparison')
    def test_features_and_libraries_unchanged(self):
        paths = ['playback/PlaybackService.kt', 'playback/QueueNavigationPolicy.kt', 'ui/library/LibraryFragment.kt',
                 'ui/player/PlayerGestureMath.kt', 'ui/player/DownloadSheet.kt', 'ui/music/NowPlayingActivity.kt',
                 'download/DownloadCenter.kt', 'download/DownloadSharing.kt', 'download/DownloadMetrics.kt',
                 'ui/common/DownloadMetricFormat.kt']
        with zipfile.ZipFile(BASE) as archive:
            files = [SRC/p for p in paths] + [p for p in (ROOT/'app/libs').rglob('*') if p.is_file()]
            for p in files:
                with self.subTest(path=p):
                    self.assertEqual(p.read_bytes(), archive.read('SparkTube-main/'+str(p.relative_to(ROOT))))
if __name__ == '__main__':
    unittest.main(verbosity=2)
