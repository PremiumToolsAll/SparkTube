#!/usr/bin/env python3
"""Focused structural regression checks for Player → Library Downloads routing."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "app/src/main/java/com/sparktube/app/ui"


class DownloadProgressNavigationTest(unittest.TestCase):
    def test_active_download_control_routes_to_downloads(self):
        player = (SRC / "player/PlayerActivity.kt").read_text()
        main = (SRC / "MainActivity.kt").read_text()
        handler = player.split("private fun onDownloadClicked()", 1)[1].split(
            "/** Deletes every finished download record", 1
        )[0]
        self.assertIn("DownloadCenter.hasActiveDownload(this, entry.url)", handler)
        self.assertIn("MainActivity.openDownloads(this)", handler)
        self.assertIn('putExtra(EXTRA_OPEN_DOWNLOADS, true)', main)
        self.assertIn('addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP)', main)
        self.assertIn("showDownloadsTab()", main)

    def test_library_selects_and_keeps_refreshing_downloads(self):
        library = (SRC / "library/LibraryFragment.kt").read_text()
        self.assertIn("binding.tabs.getTabAt(TAB_DOWNLOADS)?.select()", library)
        self.assertIn("uiHandler.post(refreshDownloads)", library)
        self.assertIn("DownloadCenter.refreshStatuses(context)", library)
        self.assertIn("LocalStore.downloads(context)", library)

    def test_idle_and_completed_download_controls_remain_unchanged(self):
        player = (SRC / "player/PlayerActivity.kt").read_text()
        handler = player.split("private fun onDownloadClicked()", 1)[1].split(
            "/** Deletes every finished download record", 1
        )[0]
        self.assertIn("DownloadCenter.isDownloaded(this, entry.url)", handler)
        self.assertIn("confirmDeleteDownload()", handler)
        self.assertIn("else -> showDownloadSheet()", handler)
        self.assertIn("private fun showDownloadSheet()", player)


if __name__ == "__main__":
    unittest.main(verbosity=2)
