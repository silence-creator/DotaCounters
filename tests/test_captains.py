"""Драфт Captains Mode: порядок ходов, стороны, подсказки. Сеть не нужна.

Запуск:  python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotacounters.dotabuff import Matchup  # noqa: E402
from dotacounters.draft import CM_BOARD, CM_ORDER, CaptainsDraft  # noqa: E402


class FakeReport:
    def __init__(self, pairs):
        self.matchups = [Matchup(hero=h, win_rate="50.00%", advantage_value=v, matches=50000)
                         for h, v in pairs]


class OrderTest(unittest.TestCase):
    """Порядок со скриншота игры (7.41)."""

    def test_counts(self):
        self.assertEqual(len(CM_ORDER), 24)
        for who in ("first", "second"):
            self.assertEqual(sum(1 for w, k in CM_ORDER if w == who and k == "ban"), 7)
            self.assertEqual(sum(1 for w, k in CM_ORDER if w == who and k == "pick"), 5)

    def test_board_matches_order(self):
        """Строка доски: слева ходы первого, справа второго, тип строки — тип хода."""
        seen = []
        for kind, left, right in CM_BOARD:
            for number, who in ((left, "first"), (right, "second")):
                if number is None:
                    continue
                self.assertEqual(CM_ORDER[number - 1], (who, kind), "ход %d" % number)
                seen.append(number)
        self.assertEqual(sorted(seen), list(range(1, 25)))

    def test_known_moves(self):
        """Выписано со скриншота: 1 и 2 — баны первого, 8 — его первый пик, 24 — последний пик."""
        self.assertEqual(CM_ORDER[0], ("first", "ban"))
        self.assertEqual(CM_ORDER[1], ("first", "ban"))
        self.assertEqual(CM_ORDER[2], ("second", "ban"))
        self.assertEqual(CM_ORDER[7], ("first", "pick"))
        self.assertEqual(CM_ORDER[23], ("second", "pick"))


class DraftTest(unittest.TestCase):
    def test_sides_follow_who_starts(self):
        cm = CaptainsDraft()
        self.assertEqual(cm.side(0), "radiant")
        cm.first = "dire"
        self.assertEqual(cm.side(0), "dire")
        self.assertEqual(cm.side(2), "radiant")

    def test_play_undo_and_duplicates(self):
        cm = CaptainsDraft()
        self.assertEqual(cm.play("Pudge"), "ok")
        self.assertEqual(cm.current, 1)
        self.assertEqual(cm.play("pudge"), "taken", "забаненного второй раз не взять")
        self.assertEqual(cm.undo(), "Pudge")
        self.assertEqual(cm.current, 0)
        for i in range(24):
            cm.play("h%d" % i)
        self.assertIsNone(cm.current)
        self.assertEqual(cm.play("Axe"), "done")

    def test_picks_bans_and_upcoming(self):
        cm = CaptainsDraft()
        for hero in ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "Mars", "Drow Ranger"):
            cm.play(hero)
        self.assertEqual(cm.picks("radiant"), ["Mars"])
        self.assertEqual(cm.picks("dire"), ["Drow Ranger"])
        self.assertEqual(cm.bans("radiant"), ["B1", "B2", "B5"])
        self.assertEqual(cm.current, 9)
        self.assertEqual(cm.phase(9), ("ban", 2))
        self.assertEqual(cm.upcoming(3), [(10, "radiant", "ban"), (11, "dire", "ban"),
                                          (12, "radiant", "pick")])
        self.assertEqual(cm.next_pick("radiant"), 12)

    def test_suggestions(self):
        """Бан — против наших пиков, пик — против их пиков; взятые и забаненные не в счёт."""
        cm = CaptainsDraft()
        for hero in ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "Mars", "Drow Ranger"):
            cm.play(hero)
        self.assertIsNone(cm.ban_suggestions(), "страниц ещё нет")
        self.assertEqual(cm.missing(), ["Mars", "Drow Ranger"], "баны страниц не требуют")
        cm.store("Mars", report=FakeReport([("Lifestealer", 3.1), ("B1", 9.0), ("Axe", 1.0)]))
        cm.store("Drow Ranger", report=FakeReport([("Earth Spirit", 2.3), ("Mars", 5.0)]))
        self.assertEqual([p.hero for p in cm.ban_suggestions().picks], ["Lifestealer", "Axe"])
        self.assertEqual([p.hero for p in cm.pick_suggestions().picks], ["Earth Spirit"])

    def test_we_play_dire(self):
        cm = CaptainsDraft()
        cm.ours = "dire"
        for hero in ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "Mars", "Drow Ranger"):
            cm.play(hero)
        cm.store("Drow Ranger", report=FakeReport([("Earth Spirit", 2.3)]))
        cm.store("Mars", report=FakeReport([("Lifestealer", 3.1)]))
        self.assertEqual([p.hero for p in cm.ban_suggestions().picks], ["Earth Spirit"])
        self.assertEqual([p.hero for p in cm.pick_suggestions().picks], ["Lifestealer"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
