"""Проверка разбора страницы контрпиков на сохранённой странице Dotabuff.

Фикстура — реальная страница Drow Ranger со всеми тремя таблицами, включая
«Matchups», которую разбирать не нужно.

Запуск:  python -m unittest discover -s tests -v
"""

import io
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotacounters.dotabuff import (  # noqa: E402
    CounterReport, ParseError, hero_slug, parse_counters,
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

    def test_picks_the_two_short_tables_not_matchups(self):
        # На странице три таблицы; «Matchups» на 126 строк браться не должна.
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
        # Выкидываем колонку винрейта: на её месте окажется не процент.
        html = load_fixture().replace("Hero Win Rate", "Matches Played")
        with self.assertRaises(ParseError):
            parse_counters(html)

    def test_garbage_in_win_rate_cell(self):
        html = re.sub(r">45\.99%<", ">n/a<", load_fixture())
        with self.assertRaises(ParseError) as ctx:
            parse_counters(html)
        self.assertIn("винрейт", str(ctx.exception))


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
