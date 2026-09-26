"""Кеш страниц Dotabuff на диске. Сеть не нужна: вместо неё заглушка.

Запуск:  python -m unittest discover -s tests -v
"""

import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotacounters.dotabuff import fetch_counters, parse_counters  # noqa: E402
from dotacounters.pagecache import MAX_AGE, PageCache  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "fixtures", "dotabuff_counters_drow_ranger.html")


def load_fixture() -> str:
    with io.open(FIXTURE, encoding="utf-8") as f:
        return f.read()


class Clock:
    def __init__(self, now=1_000_000.0):
        self.now = now

    def __call__(self):
        return self.now


class Scraper:
    def __init__(self, body):
        self.body, self.calls = body, 0

    def get(self, url, **kwargs):
        self.calls += 1
        return type("R", (), {"status_code": 200, "text": self.body})()


class PageCacheTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.clock = Clock()
        self.cache = PageCache(os.path.join(self.dir, "pages"), clock=self.clock)
        self.report = parse_counters(load_fixture(), "drow-ranger")

    def test_round_trip(self):
        self.cache.save("drow-ranger", self.report)
        self.clock.now += 3600
        hit = self.cache.load("drow-ranger")
        self.assertEqual([m.hero for m in hit.matchups], [m.hero for m in self.report.matchups])
        self.assertEqual(hit.matchups[0].matches, 48459)
        self.assertAlmostEqual(hit.cached_age, 3600)

    def test_expires_after_a_day(self):
        self.cache.save("drow-ranger", self.report)
        self.clock.now += MAX_AGE - 1
        self.assertIsNotNone(self.cache.load("drow-ranger"))
        self.clock.now += 2
        self.assertIsNone(self.cache.load("drow-ranger"))

    def test_clock_moved_back_is_a_miss(self):
        self.cache.save("drow-ranger", self.report)
        self.clock.now -= 60
        self.assertIsNone(self.cache.load("drow-ranger"))

    def test_new_patch_makes_it_stale(self):
        self.cache.patch = "7.41f"
        self.cache.save("drow-ranger", self.report)
        self.assertIsNotNone(self.cache.load("drow-ranger"))
        self.cache.patch = "7.42"
        self.assertIsNone(self.cache.load("drow-ranger"))

    def test_unknown_patch_does_not_invalidate(self):
        """Патч ещё не узнали (или сеть легла) — сохранённое всё равно годно."""
        self.cache.patch = "7.41f"
        self.cache.save("drow-ranger", self.report)
        self.cache.patch = None
        self.assertIsNotNone(self.cache.load("drow-ranger"))

    def test_broken_file_is_a_miss(self):
        os.makedirs(self.cache.folder)
        with open(os.path.join(self.cache.folder, "drow-ranger.json"), "w") as f:
            f.write("{not json")
        self.assertIsNone(self.cache.load("drow-ranger"))

    def test_unsafe_name_is_never_a_path(self):
        self.cache.save("../evil", self.report)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "evil.json")))
        self.assertIsNone(self.cache.load("../evil"))

    def test_disabled_cache_does_nothing(self):
        cache = PageCache(None)
        cache.save("drow-ranger", self.report)
        self.assertIsNone(cache.load("drow-ranger"))
        self.assertEqual(cache.count(), 0)
        self.assertEqual(cache.clear(), 0)

    def test_count_and_clear(self):
        self.cache.save("drow-ranger", self.report)
        self.cache.save("pudge", self.report)
        self.assertEqual(self.cache.count(), 2)
        self.assertEqual(self.cache.clear(), 2)
        self.assertEqual(self.cache.count(), 0)


class FetchWithCacheTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.cache = PageCache(self.dir, clock=Clock())

    def test_second_fetch_does_not_touch_the_network(self):
        scraper = Scraper(load_fixture())
        first = fetch_counters("Drow Ranger", scraper=scraper, limit=5, cache=self.cache)
        self.assertEqual(scraper.calls, 1)
        self.assertIsNone(first.cached_age)
        again = fetch_counters("Drow Ranger", scraper=scraper, limit=12, cache=self.cache)
        self.assertEqual(scraper.calls, 1, "вторая страница — из кеша")
        self.assertEqual(len(again.countered_by), 12, "разделы собраны под новый limit")
        self.assertEqual(again.countered_by[0].hero, "Mars")
        self.assertIsNotNone(again.cached_age)


if __name__ == "__main__":
    unittest.main(verbosity=2)
