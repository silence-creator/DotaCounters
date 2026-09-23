"""Проверка разбора страницы контрпиков на сохранённой странице Dotabuff.

Фикстура — реальная страница Drow Ranger со всеми тремя таблицами, включая
«Matchups» — из неё берутся разделы, когда нужно больше пяти строк.

Запуск:  python -m unittest discover -s tests -v
"""

import io
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotacounters import dotabuff  # noqa: E402
from dotacounters.dotabuff import (  # noqa: E402
    MAX_LIMIT, CounterReport, ParseError, hero_slug, parse_counters,
)

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "fixtures", "dotabuff_counters_drow_ranger.html")


def load_fixture() -> str:
    with io.open(FIXTURE, encoding="utf-8") as f:
        return f.read()


class HeroSlugTest(unittest.TestCase):
    def test_slugs(self):
        self.assertEqual(hero_slug("Anti-Mage"), "anti-mage")
        self.assertEqual(hero_slug("Drow Ranger"), "drow-ranger")
        self.assertEqual(hero_slug("Nature's Prophet"), "natures-prophet")
        self.assertEqual(hero_slug("  pudge  "), "pudge")


class ParseCountersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = parse_counters(load_fixture(), "drow-ranger")

    def test_returns_report(self):
        self.assertIsInstance(self.report, CounterReport)
        self.assertFalse(self.report.degraded,
                         "заголовки должны опознаваться, откат не нужен")

    def test_default_shows_five_rows(self):
        # По умолчанию — пять строк, как в коротких таблицах Dotabuff.
        self.assertEqual(len(self.report.countered_by), 5)
        self.assertEqual(len(self.report.counters), 5)

    def test_countered_by_content(self):
        first = self.report.countered_by[0]
        self.assertEqual(first.hero, "Mars")
        self.assertEqual(first.win_rate, "45.99%")

    def test_counters_content(self):
        first = self.report.counters[0]
        self.assertEqual(first.hero, "Necrophos")
        self.assertEqual(first.win_rate, "47.94%")

    def test_win_rate_column_not_confused_with_advantage(self):
        """Ключевая проверка сдвига колонок.

        У Mars преимущество 3.28%, а винрейт 45.99%. Если индексы съедут на
        единицу, сюда попадёт 3.28% — и цифры будут молча неверными.
        """
        first = self.report.countered_by[0]
        self.assertEqual(first.advantage, "3.28%")
        self.assertNotEqual(first.win_rate, first.advantage)

    def test_every_row_has_plausible_values(self):
        for section in (self.report.countered_by, self.report.counters):
            for m in section:
                self.assertTrue(m.hero, "имя героя не должно быть пустым")
                self.assertRegex(m.win_rate, r"^\d{1,3}\.\d+%$")

    def test_icon_urls_are_absolute(self):
        for m in self.report.countered_by:
            self.assertTrue(m.icon_url.startswith("https://www.dotabuff.com/"),
                            "иконка должна быть абсолютным адресом: %r" % m.icon_url)


class FailsLoudlyTest(unittest.TestCase):
    """Изменение вёрстки должно давать ошибку, а не неверные данные."""

    def test_no_tables(self):
        with self.assertRaises(ParseError):
            parse_counters("<html><body><p>ничего</p></body></html>")

    def test_shifted_columns_are_rejected(self):
        # Убираем подпись винрейта во ВСЕХ таблицах, включая «Matchups»:
        # опереться будет не на что, и колонку определить не выйдет.
        html = load_fixture().replace("Win Rate", "Matches Played")
        with self.assertRaises(ParseError):
            parse_counters(html)

    def test_garbage_in_win_rate_cell(self):
        html = re.sub(r">45\.99%<", ">n/a<", load_fixture())
        with self.assertRaises(ParseError) as ctx:
            parse_counters(html)
        self.assertIn("винрейт", str(ctx.exception))


class RetryTest(unittest.TestCase):
    """Cloudflare изредка отбивает первый запрос новой сессии."""

    class Scraper:
        def __init__(self, codes, body):
            self.codes, self.body, self.calls = list(codes), body, 0

        def get(self, url, **kwargs):
            self.calls += 1
            code = self.codes.pop(0) if self.codes else 200
            return type("R", (), {"status_code": code, "text": self.body})()

    def setUp(self):
        self._pauses = dotabuff.RETRY_PAUSES
        dotabuff.RETRY_PAUSES = (0, 0)    # тест не должен ждать
        self.addCleanup(setattr, dotabuff, "RETRY_PAUSES", self._pauses)

    def test_403_is_retried(self):
        scraper = self.Scraper([403, 200], load_fixture())
        report = dotabuff.fetch_counters("Drow Ranger", scraper=scraper)
        self.assertEqual(scraper.calls, 2)
        self.assertEqual(report.countered_by[0].hero, "Mars")

    def test_retries_twice_before_giving_up(self):
        scraper = self.Scraper([403, 403, 200], load_fixture())
        dotabuff.fetch_counters("Drow Ranger", scraper=scraper)
        self.assertEqual(scraper.calls, 3)

    def test_gives_up_after_the_last_retry(self):
        scraper = self.Scraper([403, 403, 403], "")
        with self.assertRaises(dotabuff.FetchError):
            dotabuff.fetch_counters("Drow Ranger", scraper=scraper)
        self.assertEqual(scraper.calls, 3, "всего три попытки")

    def test_success_is_not_retried(self):
        scraper = self.Scraper([200], load_fixture())
        dotabuff.fetch_counters("Drow Ranger", scraper=scraper)
        self.assertEqual(scraper.calls, 1)


class LimitTest(unittest.TestCase):
    """Выбор количества строк берёт данные из полной таблицы «Matchups»."""

    def test_default_matches_the_short_tables(self):
        """При пяти строках вывод обязан совпасть с короткими таблицами.

        Это защита от регрессии: раньше разделы читались именно из них.
        """
        report = parse_counters(load_fixture(), "drow-ranger", limit=5)
        self.assertEqual([m.hero for m in report.countered_by],
                         ["Mars", "Earth Spirit", "Lycan", "Zeus", "Spectre"])
        self.assertEqual([m.hero for m in report.counters],
                         ["Necrophos", "Meepo", "Riki", "Bristleback", "Slardar"])

    def test_twelve_rows(self):
        report = parse_counters(load_fixture(), "drow-ranger", limit=12)
        self.assertEqual(len(report.countered_by), 12)
        self.assertEqual(len(report.counters), 12)
        # Разделы не должны пересекаться.
        self.assertFalse({m.hero for m in report.countered_by} &
                         {m.hero for m in report.counters})

    def test_sections_stay_ordered_by_severity(self):
        report = parse_counters(load_fixture(), "drow-ranger", limit=12)
        self.assertEqual(report.countered_by[0].hero, "Mars")
        self.assertEqual(report.counters[0].hero, "Necrophos")

    def test_limit_is_clamped(self):
        for asked, expected in ((0, 1), (-5, 1), (99, MAX_LIMIT), (MAX_LIMIT, MAX_LIMIT)):
            report = parse_counters(load_fixture(), "drow-ranger", limit=asked)
            self.assertEqual(len(report.countered_by), expected,
                             "limit=%r должен дать %d строк" % (asked, expected))

    def test_matchups_table_is_parsed(self):
        report = parse_counters(load_fixture(), "drow-ranger")
        self.assertEqual(len(report.matchups), 126)

    def test_survives_when_only_matchups_is_readable(self):
        """Если короткие таблицы сломались, данные всё равно есть.

        Полная таблица независима от них, и разделы берутся из неё.
        """
        html = load_fixture().replace("Hero Win Rate", "Matches Played")
        report = parse_counters(html, "drow-ranger", limit=5)
        self.assertEqual(report.countered_by[0].hero, "Mars")
        self.assertEqual(report.counters[0].hero, "Necrophos")


class DegradedFallbackTest(unittest.TestCase):
    """Если заголовки исчезли, данные всё же показываются — но с пометкой."""

    def test_falls_back_to_position(self):
        html = load_fixture()
        html = re.sub(r"(?i)is countered by", "???", html)
        html = re.sub(r"(?i)counters", "???", html)
        report = parse_counters(html, "drow-ranger")
        self.assertTrue(report.degraded)
        self.assertEqual(len(report.countered_by), 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
