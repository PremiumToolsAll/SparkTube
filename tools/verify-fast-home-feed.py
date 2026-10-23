#!/usr/bin/env python3
"""Source guardrails only: these do not measure Android startup or network latency."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
home = (ROOT / 'app/src/main/java/com/sparktube/app/ui/home/HomeFragment.kt').read_text()
cache = (ROOT / 'app/src/main/java/com/sparktube/app/ui/home/HomeFeedCache.kt').read_text()
repo = (ROOT / 'app/src/main/java/com/sparktube/app/data/YtRepository.kt').read_text()
loader = (ROOT / 'app/src/main/java/com/sparktube/app/data/ProgressiveFeedLoader.kt').read_text()
tests = (ROOT / 'app/src/test/java/com/sparktube/app/ui/home/HomeFeedCachePolicyTest.kt').read_text()
checks = {
    'cache_read_precedes_network': home.index('HomeFeedCache.read(ctx, country)') < home.index('YtRepository.personalizedFeed(country, snap'),
    'preview_returns_on_main': 'onInitialItems = { initial ->' in home and 'withContext(Dispatchers.Main)' in home,
    'binding_country_generation_guard': 'isCurrent(b, country, generation)' in home and '@Volatile private var feedGeneration' in home,
    'network_errors_retain_cards': 'adapter.submitList(emptyList())' not in home[home.index('} catch (e: Exception)'):home.index('} finally')],
    'disk_cache_uses_io': 'HomeFeedCache.write(ctx, country, models, shouldWrite' in home and 'withContext(Dispatchers.IO)' in home,
    'country_version_ttl_and_bounds': all(x in cache for x in ['MAX_ENTRIES = 60', 'TTL_MILLIS', '"country"', '"version"']),
    'display_only_cache': all(x in cache for x in ['model.url', 'model.title', 'model.thumbnailUrl']) and 'streamUrl' not in cache,
    'cache_policy_tests_present': 'cacheExpiresAfterPolicyTtl' in tests and 'cacheIsDeduplicatedAndHardBounded' in tests,
    'kiosks_run_concurrently_and_publish_once': 'async(Dispatchers.IO)' in loader and 'published.compareAndSet(false, true)' in loader and '.awaitAll()' in loader,
    'cancellation_not_swallowed': 'catch (e: CancellationException)' in loader and 'throw e' in loader,
    'repository_retains_final_blend_and_rank': 'ProgressiveFeedLoader.load(loaders, onInitialItems)' in repo and 'RecommendEngine.score(it, snap)' in repo and 'head + tail' in repo,
    'visible_cards_survive_empty_cache': 'else if (visibleCountry != country || adapter.currentList.isEmpty())' in home,
    'view_recreation_invalidates_old_load': 'feedGeneration++\n        loadJob?.cancel()' in home and 'loadedCountry = null\n        visibleCountry = null\n        lastLoadedAt = 0L' in home,
    'obsolete_writes_checked_inside_lock': '@Synchronized\n    fun write(' in cache and 'if (!shouldWrite()) return' in cache,
}

class FastHomeFeedChecks(unittest.TestCase):
    pass

for name, passed in checks.items():
    def check(self, value=passed, label=name):
        self.assertTrue(value, label)
    setattr(FastHomeFeedChecks, 'test_' + name, check)

if __name__ == '__main__':
    unittest.main(verbosity=2)
