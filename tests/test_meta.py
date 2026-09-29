"""Мета и баны Captains Mode: разбор страницы, выбор банов, кеш. Сеть не нужна."""

import io
import os
import tempfile
import unittest

from dotacounters.dotabuff import FetchError, Matchup, ParseError
from dotacounters.draft import CaptainsDraft
from dotacounters.heroes import ALL_HEROES
from dotacounters.meta import BRACKETS, MIN_PICK, fetch_meta, in_rank, parse_meta, strongest
from dotacounters.pagecache import PageCache

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "dotabuff_meta_table.html")


def load_fixture():
    with io.open(FIXTURE, encoding="utf-8") as f:
        return f.read()


class ParseMetaTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.meta = parse_meta(load_fixture())

    def test_every_hero_with_five_brackets(self):
        self.assertEqual(set(self.meta), set(ALL_HEROES))
        self.assertEqual(len(self.meta["Axe"]), len(BRACKETS))

    def test_numbers_from_data_value(self):
        # (частота, винрейт) — сначала до 2K, последним Divine и Immortal
        self.assertEqual(self.meta["Anti-Mage"][0], (14.45, 50.41))
        self.assertEqual(self.meta["Anti-Mage"][-1], (7.51, 50.62))

    def test_pick_rates_sum_to_ten_heroes_per_match(self):
        for i, _ in enumerate(BRACKETS):
            self.assertAlmostEqual(sum(v[i][0] for v in self.meta.values()), 1000, delta=1)

    def test_wrong_page_fails_loudly(self):
        with self.assertRaises(ParseError):
            parse_meta("<html><body>Cloudflare</body></html>")
        with self.assertRaises(ParseError):
            parse_meta("<table><thead><tr><th colspan='2'>Hero</th><th>Pick %</th></tr></thead>"
                       "<tbody></tbody></table>")


class StrongestTest(unittest.TestCase):
    META = {
        "Strong": ((10.0, 55.0),) * 5,
        "Niche": ((MIN_PICK - 1, 60.0),) * 5,     # винрейт выше всех, но берут редко
        "Middle": ((20.0, 52.0),) * 5,
        "Weak": ((30.0, 47.0),) * 5,
        "Ranked": ((10.0, 45.0), (10.0, 45.0), (10.0, 45.0), (10.0, 45.0), (10.0, 58.0)),
    }

    def test_rare_heroes_are_skipped(self):
        self.assertNotIn("Niche", [m.hero for m in strongest(self.META, limit=10)])

    def test_order_by_win_rate(self):
        self.assertEqual([m.hero for m in strongest(self.META, "herald", limit=3)],
                         ["Strong", "Middle", "Weak"])

    def test_rank_changes_the_list(self):
        self.assertEqual(strongest(self.META, "divine", limit=1)[0].hero, "Ranked")
        self.assertAlmostEqual(in_rank(self.META, "all")["Ranked"][1], (45 * 4 + 58) / 5)

    def test_allowed(self):
        rows = strongest(self.META, allowed=lambda h: h != "Strong", limit=1)
        self.assertEqual(rows[0].hero, "Middle")


class FetchMetaTest(unittest.TestCase):

    class Response:
        def __init__(self, status, text=""):
            self.status_code, self.text = status, text

    class Scraper:
        def __init__(self, *responses):
            self.responses, self.calls = list(responses), 0

        def get(self, url, timeout=None):
            self.calls += 1
            return self.responses.pop(0)

    def test_downloads_saves_and_reuses(self):
        with tempfile.TemporaryDirectory() as folder:
            cache = PageCache(folder)
            scraper = self.Scraper(self.Response(200, load_fixture()))
            meta = fetch_meta(scraper, cache=cache)
            again = fetch_meta(self.Scraper(), cache=cache)       # без сети
            self.assertEqual(again, meta)
            self.assertEqual(cache.count(), 0, "мета — не страница героя")

    def test_http_error(self):
        with self.assertRaises(FetchError):
            fetch_meta(self.Scraper(self.Response(500)))


def _report(heroes):
    report = type("Report", (), {})()
    report.matchups = [Matchup(hero=h, win_rate="50.00%", advantage_value=1.0, matches=50000)
                       for h in heroes]
    return report


class CaptainsBansTest(unittest.TestCase):
    META = {"Spectre": ((10.0, 56.0),) * 5,              # только керри
            "Storm Spirit": ((10.0, 55.0),) * 5,         # мид
            "Crystal Maiden": ((10.0, 54.0),) * 5}       # пятёрка

    def cm(self, *moves):
        cm = CaptainsDraft()
        cm.meta = self.META
        for hero in moves:
            cm.play(hero)
        return cm

    def test_first_phase_bans_by_meta(self):
        cm = self.cm("B1")
        self.assertTrue(cm.bans_by_meta)
        self.assertEqual([m.hero for m in cm.meta_bans()],
                         ["Spectre", "Storm Spirit", "Crystal Maiden"])

    def test_taken_and_filtered_heroes_are_skipped(self):
        cm = self.cm("Spectre")                           # забанен на первом ходу
        cm.role = "pos5"
        self.assertEqual([m.hero for m in cm.meta_bans()], ["Crystal Maiden"])

    def test_no_meta_yet(self):
        cm = CaptainsDraft()
        self.assertIsNone(cm.meta_bans())

    def test_bans_after_picks_follow_enemy_open_positions(self):
        # Radiant — мы, ходим первыми: 8 — наш пик, 9 — их пик
        cm = self.cm("B1", "B2", "B3", "B4", "B5", "B6", "B7", "Axe", "Anti-Mage")
        self.assertFalse(cm.bans_by_meta)
        cm.store("Axe", report=_report(["Spectre", "Storm Spirit", "Crystal Maiden"]))
        self.assertNotIn("pos1", cm.their_needed(), "керри у них уже есть")
        self.assertEqual(sorted(p.hero for p in cm.ban_suggestions().picks),
                         ["Crystal Maiden", "Storm Spirit"])
        cm.fill = False
        self.assertEqual(len(cm.ban_suggestions().picks), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
