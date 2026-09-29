"""Позиции героев 1–5: разбор страницы линий Dotabuff и вывод позиций."""

import io
import os
import unittest

from dotacounters.dotabuff import Matchup, ParseError
from dotacounters.draft import CaptainsDraft, DraftBoard, has_role
from dotacounters.heroes import ALL_HEROES
from dotacounters.lanes import LANES
from dotacounters.positions import (MIN_PRESENCE, OFF_CORE_GPM, OFF_SUPPORT_GPM, POSITIONS,
                                    SAFE_CORE_GPM, assign_positions, missing_positions,
                                    parse_lanes, positions_of)

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "dotabuff_lanes_off_table.html")


class ParseLanesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with io.open(FIXTURE, encoding="utf-8") as f:
            cls.rows = parse_lanes(f.read())

    def test_all_rows_read(self):
        self.assertEqual(len(self.rows), 115)

    def test_numbers_from_data_value(self):
        # «Hero» занимает две колонки: без учёта colspan доля и GPM съехали бы
        self.assertEqual(self.rows["Centaur Warrunner"], (94.34, 477))
        self.assertEqual(self.rows["Pudge"], (50.36, 394))

    def test_names_match_hero_list(self):
        self.assertEqual(set(self.rows) - set(ALL_HEROES), set())

    def test_page_without_table_fails_loudly(self):
        with self.assertRaises(ParseError):
            parse_lanes("<html><body>Cloudflare</body></html>")

    def test_missing_column_fails_loudly(self):
        html = ("<table><thead><tr><th colspan='2'>Hero</th><th>Win Rate</th></tr></thead>"
                "<tbody><tr><td></td><td>Axe</td><td data-value='50'>50%</td></tr></tbody></table>")
        with self.assertRaises(ParseError):
            parse_lanes(html)


class PositionsTest(unittest.TestCase):

    def of(self, hero="Test", **lanes):
        return positions_of(hero, {hero: lanes})

    def test_mid(self):
        self.assertEqual(self.of(mid=(MIN_PRESENCE, 550)), ("pos2",))
        self.assertEqual(self.of(mid=(MIN_PRESENCE - 1, 550), off=(80.0, 500)), ("pos3",))

    def test_safe_lane_core_or_hard_support(self):
        self.assertEqual(self.of(safe=(90.0, SAFE_CORE_GPM)), ("pos1",))
        self.assertEqual(self.of(safe=(70.0, SAFE_CORE_GPM - 1)), ("pos5",))

    def test_off_lane_core_support_and_both(self):
        self.assertEqual(self.of(off=(80.0, OFF_SUPPORT_GPM)), ("pos3",))
        self.assertEqual(self.of(off=(40.0, OFF_CORE_GPM - 1)), ("pos4",))
        self.assertEqual(self.of(off=(60.0, 420)), ("pos3", "pos4"))

    def test_valve_support_in_between_is_only_pos4(self):
        # Omniknight — support 2 у Valve, Magnus — 0; GPM одинаковый, из полосы
        self.assertEqual(self.of("Omniknight", off=(50.0, 420)), ("pos4",))
        self.assertEqual(self.of("Magnus", off=(50.0, 420)), ("pos3", "pos4"))

    def test_roaming_adds_to_off_lane(self):
        self.assertEqual(self.of(off=(12.0, 380), roaming=(10.0, 390)), ("pos4",))

    def test_below_threshold_everywhere_takes_most_played(self):
        self.assertEqual(self.of(safe=(15.0, 600), mid=(10.0, 550), off=(8.0, 450)), ("pos1",))

    def test_unknown_hero(self):
        self.assertEqual(positions_of("Nobody", {}), ())


class TeamTest(unittest.TestCase):
    """Расстановка своей команды и свободные позиции."""

    LANES = {
        "Carry": {"safe": (90.0, 600)},
        "Mid": {"mid": (80.0, 550)},
        "Flex": {"mid": (60.0, 540), "off": (35.0, 480)},   # мид чаще, но может и тройку
        "Off": {"off": (85.0, 490)},
        "Off2": {"off": (70.0, 470)},
    }

    def assign(self, *heroes):
        return assign_positions(heroes, self.LANES)

    def test_empty_team_misses_everything(self):
        self.assertEqual(missing_positions([], self.LANES), POSITIONS)

    def test_flex_hero_takes_the_open_position(self):
        self.assertEqual(self.assign("Flex"), {"Flex": "pos2"}, "один — на свою частую линию")
        self.assertEqual(self.assign("Mid", "Flex"), {"Mid": "pos2", "Flex": "pos3"})
        self.assertEqual(missing_positions(["Mid", "Flex"], self.LANES), ("pos1", "pos4", "pos5"))

    def test_two_heroes_for_one_position(self):
        self.assertEqual(missing_positions(["Off", "Off2"], self.LANES),
                         ("pos1", "pos2", "pos4", "pos5"))


class _Report:
    def __init__(self, heroes):
        self.matchups = [Matchup(hero=h, win_rate="50.00%", advantage_value=1.0, matches=50000)
                         for h in heroes]


class FillTest(unittest.TestCase):
    """Подсказки пиков — под свободные позиции своей команды (снимок lanes.py)."""

    CANDIDATES = ("Centaur Warrunner", "Storm Spirit", "Crystal Maiden")   # 3, 2, 5

    def board(self):
        board = DraftBoard()
        board.add("allies", "Axe")                                  # тройка
        board.add("enemies", "Pudge")
        board.store("Pudge", report=_Report(self.CANDIDATES))
        return board

    def picks(self, board):
        return sorted(p.hero for p in board.analyse().picks)

    def test_taken_position_drops_out(self):
        board = self.board()
        self.assertNotIn("pos3", board.needed())
        self.assertEqual(self.picks(board), ["Crystal Maiden", "Storm Spirit"])

    def test_switch_off_shows_all(self):
        board = self.board()
        board.fill = False
        self.assertEqual(self.picks(board), sorted(self.CANDIDATES))

    def test_explicit_filter_wins(self):
        board = self.board()
        board.role = "pos3"               # «ищу тройку», хоть она и занята
        self.assertEqual(self.picks(board), ["Centaur Warrunner"])
        self.assertEqual(board.pick_filter(), ())

    def test_no_allies_no_filter(self):
        board = DraftBoard()
        self.assertEqual(board.needed(), ())
        self.assertEqual(board.pick_filter(), ())

    def test_captains_mode_uses_our_picks(self):
        cm = CaptainsDraft()
        for hero in ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "Axe", "Pudge"):
            cm.play(hero)                  # Axe — наш первый пик (Radiant ходит первым)
        cm.store("Pudge", report=_Report(self.CANDIDATES))
        self.assertEqual(sorted(p.hero for p in cm.pick_suggestions().picks),
                         ["Crystal Maiden", "Storm Spirit"])


class SnapshotTest(unittest.TestCase):
    """Снимок lanes.py: иначе фильтр по позиции молча прятал бы героя."""

    def test_every_hero_has_lanes_and_a_position(self):
        self.assertEqual([h for h in ALL_HEROES if h not in LANES], [])
        self.assertEqual([h for h in ALL_HEROES if not positions_of(h)], [])

    def test_well_known_heroes(self):
        for hero, position in (("Storm Spirit", "pos2"), ("Anti-Mage", "pos1"),
                               ("Axe", "pos3"), ("Crystal Maiden", "pos5"),
                               ("Tusk", "pos4")):
            self.assertIn(position, positions_of(hero), hero)

    def test_every_position_has_heroes(self):
        for position in POSITIONS:
            self.assertGreater(sum(1 for h in ALL_HEROES if position in positions_of(h)), 20,
                               position)

    def test_filter_understands_positions(self):
        self.assertTrue(has_role("Storm Spirit", "pos2"))
        self.assertFalse(has_role("Crystal Maiden", "pos2"))
        self.assertTrue(has_role("Crystal Maiden", "support"))   # роли Valve — как раньше


if __name__ == "__main__":
    unittest.main(verbosity=2)
