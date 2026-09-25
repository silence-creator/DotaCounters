"""Подбор пика против вражеского состава. Сеть не нужна.

Часть проверок идёт на сохранённой странице Drow Ranger, часть — на
придуманных матчапах, где ответ известен заранее.

Запуск:  python -m unittest discover -s tests -v
"""

import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotacounters.dotabuff import Matchup, parse_counters  # noqa: E402
from dotacounters.draft import (  # noqa: E402
    MAX_ENEMIES, ROLE_FILTERS, DraftBoard, analyse, has_role,
)
from dotacounters.heroes import ALL_HEROES  # noqa: E402
from dotacounters.roles import ROLE_LEVELS, ROLE_ORDER  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "fixtures", "dotabuff_counters_drow_ranger.html")


def drow_report():
    with io.open(FIXTURE, encoding="utf-8") as f:
        return parse_counters(f.read(), "drow-ranger")


class FakeReport:
    """Отчёт с заданными матчапами: значение = насколько хуже играет враг."""

    def __init__(self, pairs):
        self.matchups = [Matchup(hero=hero, win_rate="50.00%", advantage_value=value)
                         for hero, value in pairs]


class AdvantageValueTest(unittest.TestCase):
    """Число берётся из data-value, а не из подписи с процентом."""

    def test_parsed_from_page(self):
        report = drow_report()
        mars = report.matchups[0]
        self.assertEqual(mars.hero, "Mars")
        self.assertAlmostEqual(mars.advantage_value, 3.2809, places=4)
        self.assertEqual(mars.advantage, "3.28%", "текст с процентом тоже на месте")

    def test_sign_shows_direction(self):
        report = drow_report()
        self.assertGreater(report.matchups[0].advantage_value, 0,
                           "первый в таблице контрит героя страницы")
        self.assertLess(report.matchups[-1].advantage_value, 0,
                        "последний, наоборот, ему уступает")


class AnalyseTest(unittest.TestCase):
    def test_sums_across_enemies(self):
        reports = {
            "Enemy A": FakeReport([("Хорош против обоих", 3.0), ("Плох против обоих", -3.0),
                                   ("Средний", 1.0)]),
            "Enemy B": FakeReport([("Хорош против обоих", 2.0), ("Плох против обоих", -2.0),
                                   ("Средний", -1.0)]),
        }
        result = analyse(reports, limit=3)
        self.assertEqual([p.hero for p in result.picks],
                         ["Хорош против обоих", "Средний", "Плох против обоих"])
        self.assertAlmostEqual(result.picks[0].total, 5.0)
        self.assertAlmostEqual(result.picks[0].average, 2.5)
        self.assertEqual(result.picks[0].per_enemy, {"Enemy A": 3.0, "Enemy B": 2.0})

    def test_avoid_is_the_other_end(self):
        reports = {"E": FakeReport([("Лучший", 5.0), ("Средний", 0.0), ("Худший", -5.0)])}
        result = analyse(reports, limit=1)
        self.assertEqual([p.hero for p in result.picks], ["Лучший"])
        self.assertEqual([p.hero for p in result.avoid], ["Худший"])

    def test_enemies_are_not_suggested(self):
        """Взятого врагом героя предлагать нельзя — он уже занят."""
        reports = {"Mars": FakeReport([("Mars", 9.0), ("Zeus", 1.0)])}
        result = analyse(reports, limit=5)
        self.assertNotIn("Mars", [p.hero for p in result.picks])
        self.assertIn("Zeus", [p.hero for p in result.picks])

    def test_hero_missing_for_one_enemy_is_dropped(self):
        """Иначе сумма по одному врагу соперничала бы с суммой по двум."""
        reports = {"A": FakeReport([("Общий", 1.0), ("Только у A", 9.0)]),
                   "B": FakeReport([("Общий", 1.0)])}
        result = analyse(reports, limit=5)
        self.assertEqual([p.hero for p in result.picks], ["Общий"])

    def test_enemy_without_matchups_is_reported(self):
        reports = {"A": FakeReport([("Герой", 1.0)]), "Пустой": FakeReport([])}
        result = analyse(reports)
        self.assertEqual(result.skipped, ["Пустой"])
        self.assertEqual(result.enemies, ["A"])
        self.assertEqual([p.hero for p in result.picks], ["Герой"])

    def test_no_usable_reports(self):
        result = analyse({"Пустой": FakeReport([])})
        self.assertEqual(result.picks, [])
        self.assertEqual(result.skipped, ["Пустой"])

    def test_limit(self):
        reports = {"E": FakeReport([("h%02d" % i, float(i)) for i in range(20)])}
        self.assertEqual(len(analyse(reports, limit=3).picks), 3)
        self.assertEqual(len(analyse(reports, limit=0).picks), 1, "меньше одного не бывает")


class RealPageTest(unittest.TestCase):
    """Против одного врага подбор обязан совпасть с его же таблицей контрпиков."""

    def test_single_enemy_matches_the_page(self):
        report = drow_report()
        result = analyse({"Drow Ranger": report}, limit=5)
        self.assertEqual([p.hero for p in result.picks],
                         [m.hero for m in report.countered_by],
                         "лучшие против Drow — те, кто её контрит")
        self.assertEqual([p.hero for p in result.avoid],
                         [m.hero for m in report.counters],
                         "худшие — те, кого она сама контрит")

    def test_five_enemies_is_the_cap(self):
        self.assertEqual(MAX_ENEMIES, 5)

    def test_every_hero_on_the_page_has_roles(self):
        """Имена Dotabuff и Valve должны совпадать, иначе фильтр молча выкинет героя."""
        missing = [m.hero for m in drow_report().matchups if m.hero not in ROLE_LEVELS]
        self.assertEqual(missing, [])


class TakenHeroesTest(unittest.TestCase):
    """Союзников и забаненных героев брать нельзя — их нет в пуле."""

    REPORTS = {"E": FakeReport([("Zeus", 5.0), ("Lina", 4.0), ("Axe", 3.0), ("Pudge", -1.0)])}

    def test_allies_and_bans_are_left_out(self):
        result = analyse(self.REPORTS, limit=5, exclude=["zeus", " Axe "])
        heroes = [p.hero for p in result.picks + result.avoid]
        self.assertNotIn("Zeus", heroes, "регистр и пробелы не важны")
        self.assertNotIn("Axe", heroes)
        self.assertEqual([p.hero for p in result.picks], ["Lina", "Pudge"])


class RoleFilterTest(unittest.TestCase):
    def test_roles_from_valve(self):
        self.assertTrue(has_role("Crystal Maiden", "support"))
        self.assertFalse(has_role("Crystal Maiden", "carry"))
        self.assertTrue(has_role("Anti-Mage", "carry"))
        self.assertFalse(has_role("Незнакомец", "carry"))

    def test_filter_applies_to_both_lists(self):
        reports = {"E": FakeReport([("Crystal Maiden", 5.0), ("Anti-Mage", 4.0),
                                    ("Lion", -3.0), ("Spectre", -4.0)])}
        result = analyse(reports, limit=5, role="support")
        self.assertEqual([p.hero for p in result.picks], ["Crystal Maiden", "Lion"])
        self.assertEqual([p.hero for p in result.avoid], ["Lion", "Crystal Maiden"])

    def test_every_filter_role_is_known(self):
        for role in ROLE_FILTERS:
            self.assertIn(role, ROLE_ORDER)

    def test_every_hero_has_roles(self):
        self.assertEqual(sorted(set(ALL_HEROES) - set(ROLE_LEVELS)), [])


class DraftBoardTest(unittest.TestCase):
    def test_add_dup_move_full(self):
        board = DraftBoard()
        self.assertEqual(board.add("enemies", "Pudge"), "added")
        self.assertEqual(board.add("enemies", "pudge"), "dup")
        self.assertEqual(board.add("allies", "Pudge"), "moved",
                         "один герой не может быть и врагом, и союзником")
        self.assertEqual(board.groups, {"enemies": [], "allies": ["Pudge"], "bans": []})
        for hero in ("Lina", "Axe", "Zeus", "Lion", "Mars"):
            board.add("enemies", hero)
        self.assertEqual(board.add("enemies", "Tiny"), "full")

    def test_analysis_uses_allies_bans_and_role(self):
        board = DraftBoard()
        board.add("enemies", "E")
        board.add("allies", "Crystal Maiden")
        board.add("bans", "Lion")
        self.assertIsNone(board.analyse(), "страницы врага ещё нет")
        self.assertEqual(board.missing(), ["E"])
        board.store("E", report=FakeReport([("Crystal Maiden", 5.0), ("Lion", 4.0),
                                            ("Witch Doctor", 3.0), ("Anti-Mage", 2.0)]))
        self.assertEqual([p.hero for p in board.analyse().picks], ["Witch Doctor", "Anti-Mage"])
        board.role = "carry"
        self.assertEqual([p.hero for p in board.analyse().picks], ["Anti-Mage"])

    def test_missing_skips_loading_and_failed_unless_retried(self):
        board = DraftBoard()
        for hero in ("A", "B", "C"):
            board.add("enemies", hero)
        board.loading.add("A")
        board.store("B", error="HTTP 403")
        self.assertEqual(board.missing(), ["C"], "не долбить отказавший Dotabuff при каждом изменении")
        self.assertEqual(board.missing(retry=True), ["B", "C"])
        board.store("A", report=FakeReport([]))
        self.assertNotIn("A", board.loading)

    def test_failed_and_clear(self):
        board = DraftBoard()
        board.add("enemies", "E")
        board.store("E", error="HTTP 403")
        self.assertEqual(board.failed, {"E": "HTTP 403"})
        board.store("E", report=FakeReport([("Axe", 1.0)]))
        self.assertEqual(board.failed, {}, "удачная загрузка снимает ошибку")
        board.clear()
        self.assertEqual(board.enemies, [])
        self.assertIn("E", board.reports, "страницы остаются для следующего драфта")


if __name__ == "__main__":
    unittest.main(verbosity=2)
