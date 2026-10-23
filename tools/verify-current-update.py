#!/usr/bin/env python3
"""Run feature/structure checks; historical whole-file baselines are replaced by latest-scope audit."""
from pathlib import Path
import importlib.util
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
suite = unittest.TestSuite()
checks = [
    # VideoCollapseChecks compares app files against the latest notification/audio baseline.
    ('verify-notification-response.py', 'NotificationResponseChecks', {'test_existing_feature_files_unchanged_except_explicit_scope'}),
    ('verify-first-tap.py', 'FirstTapChecks', {'test_latest_baseline_scope_preserves_all_other_app_files'}),
    ('verify-video-collapse.py', 'VideoCollapseChecks', {'test_latest_scope_preserves_other_features_build_and_libraries'}),
    ('verify-sleep-timer.py', 'SleepTimerChecks', set()),
    ('verify-download-progress-navigation.py', 'DownloadProgressNavigationTest', set()),
    ('verify-horizontal-player-gestures.py', 'HorizontalPlayerGestureTest', set()),
    ('verify-fast-home-feed.py', 'FastHomeFeedChecks', set()),
    ('verify-player-correction.py', 'PlayerStructureTest', {'test_features_and_libraries_unchanged'}),
    ('verify-pip-fix.py', 'PipFixChecks', {'test_only_player_activity_changed_since_latest_source'}),
    ('verify-audio-downloads.py', 'AudioDownloadStructureTest', {'test_existing_app_changes_are_limited_to_two_classes'}),
]
for index, (filename, classname, skip) in enumerate(checks):
    spec = importlib.util.spec_from_file_location(f'feature_checks_{index}', ROOT / 'tools' / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cls = getattr(mod, classname)
    suite.addTests(cls(name) for name in unittest.defaultTestLoader.getTestCaseNames(cls) if name not in skip)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
