"""Считывание драфта с экрана: разметка, узнавание, пустые клетки, перенос в драфт.

Фикстуры — куски настоящих снимков: верхняя полоса двух матчей All Pick
1280×720 (видео), пустой драфт и пустая доска Captains Mode 1920×1200 и
доска старого формата 1920×1080. Портреты — атлас 64×36 всех героев. Кусок
вставляется на чистое поле размером с исходный снимок: разметка считается от
середины и высоты экрана.
"""

import os
import tempfile
import unittest

from PIL import Image

from dotacounters import screen
from dotacounters.draft import CaptainsDraft, DraftBoard

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
BACKGROUND = (22, 26, 32)


def _portraits():
    names = open(os.path.join(FIXTURES, "screen_portraits.txt"), encoding="utf-8").read().split("\n")
    names = [n for n in names if n]
    atlas = Image.open(os.path.join(FIXTURES, "screen_portraits.jpg")).convert("RGB")
    w, h, cols = 64, 36, 16
    return {n: atlas.crop(((i % cols) * w, (i // cols) * h, (i % cols + 1) * w, (i // cols + 1) * h))
            for i, n in enumerate(names)}


PORTRAITS = _portraits()
MATCHER = screen.Matcher(PORTRAITS)


def _screen(name, size, at=(0, 0)):
    """Кусок снимка name на поле size в точке at."""
    canvas = Image.new("RGB", size, BACKGROUND)
    canvas.paste(Image.open(os.path.join(FIXTURES, name)).convert("RGB"), at)
    return canvas


class LayoutTest(unittest.TestCase):

    def test_top_slots_symmetric(self):
        for size in ((1920, 1080), (1920, 1200), (1280, 720)):
            boxes = screen.top_slots(size)
            self.assertEqual(len(boxes), 10)
            mid = size[0] / 2
            for k in range(5):
                l, _, r, _ = boxes[k]                  # Radiant k+1
                l2, _, r2, _ = boxes[9 - k]            # Dire 5−k
                self.assertAlmostEqual(mid - (l + r) / 2, (l2 + r2) / 2 - mid, delta=1)

    def test_top_bar_wider_at_16_10(self):
        """При 16:10 полоса раздвинута к краям (замер на снимках пользователя)."""
        self.assertAlmostEqual(screen.top_inner(16 / 9), 195)
        self.assertAlmostEqual(screen.top_inner(16 / 10), 220)
        a = screen.top_slots((1920, 1080))[4]
        b = screen.top_slots((1728, 1080))[4]       # та же высота, 16:10
        self.assertGreater((1920 / 2) - (a[0] + a[2]) / 2, 190)
        self.assertGreater((1728 / 2) - (b[0] + b[2]) / 2, (1920 / 2) - (a[0] + a[2]) / 2)

    def test_board_columns_follow_first(self):
        radiant = screen.board_cells((1920, 1080), "radiant")
        dire = screen.board_cells((1920, 1080), "dire")
        self.assertEqual(len(radiant), 24)
        # ход 1 — у того, кто начинает: при Radiant слева от середины... то есть
        # в левой колонке доски, при Dire — в правой
        self.assertLess(radiant[0][0], dire[0][0])
        # ходы 2 и 3 — в одной строке, у разных сторон
        self.assertEqual(radiant[1][1], radiant[2][1])
        self.assertNotEqual(radiant[1][0], radiant[2][0])
        # бан меньше пика
        self.assertLess(radiant[0][3] - radiant[0][1], radiant[7][3] - radiant[7][1])


class AllPickTest(unittest.TestCase):

    def test_reads_full_draft(self):
        reader = screen.Reader(MATCHER)
        reading = reader.read_allpick(_screen("screen_ap_1280.jpg", (1280, 720)))
        self.assertTrue(reading.present)
        heroes = [c.hero if c.hero_seen else None for c in reading.cells]
        self.assertEqual(heroes, ["Drow Ranger", "Kunkka", "Oracle", "Zeus", "Jakiro", None,
                                  "Crystal Maiden", "Skywrath Mage", "Chaos Knight", "Necrophos"])
        # пустая клетка со значком уровня — не герой
        self.assertFalse(reading.cells[5].hero_seen)
        # своё имя ярче: игрок — Dire 1
        self.assertEqual(reading.local, 5)
        self.assertEqual(reading.ours, "dire")

    def test_hovered_hero_is_not_a_pick(self):
        """Серый герой под курсором у невыбравшего — не пик."""
        reader = screen.Reader(MATCHER)
        reading = reader.read_allpick(_screen("screen_ap_1280b.jpg", (1280, 714)))
        self.assertFalse(reading.cells[0].hero_seen)
        heroes = [c.hero for c in reading.cells[1:]]
        self.assertEqual(heroes, ["Tiny", "Lina", "Witch Doctor", "Phantom Assassin", "Lich",
                                  "Razor", "Sven", "Death Prophet", "Skywrath Mage"])
        self.assertEqual(reading.ours, "radiant")

    def test_empty_draft_16_10(self):
        """Пустой драфт пользователя 1920×1200: значок ранга и наведённый герой — не пики."""
        reader = screen.Reader(MATCHER)
        reading = reader.read_allpick(_screen("screen_ap_empty_1920x1200.jpg", (1917, 1199)))
        self.assertTrue(reading.present)
        self.assertFalse(any(c.hero_seen for c in reading.cells))
        self.assertEqual(reading.local, 0)

    def test_not_a_draft(self):
        reader = screen.Reader(MATCHER)
        reading = reader.read_allpick(Image.new("RGB", (1920, 1080), BACKGROUND))
        self.assertFalse(reading.present)
        self.assertEqual(reading.cells, [])

    def test_shift_is_remembered_per_size(self):
        reader = screen.Reader(MATCHER)
        img = _screen("screen_ap_1280.jpg", (1280, 720))
        reader.read_allpick(img)
        self.assertIn(((1280, 720), "radiant"), reader._shifts)
        self.assertIn(((1280, 720), "dire"), reader._shifts)


class CaptainsTest(unittest.TestCase):

    def test_empty_board_16_10(self):
        img = _screen("screen_cm_empty_1920x1200.jpg", (1919, 1199), at=(1380, 195))
        scores = screen.board_scores(img)
        self.assertTrue(screen.board_present(img, scores))
        self.assertEqual(screen.first_side(img, scores), "radiant")
        # своя сторона подписана цветом: Radiant зелёным
        self.assertEqual(screen.our_board_side(img), "radiant")
        reading = screen.Reader(MATCHER).read_captains(img)
        self.assertEqual(len(reading.cells), 24)
        self.assertFalse(any(c.hero_seen for c in reading.cells))
        self.assertEqual(reading.first, "radiant")

    def test_no_board(self):
        img = _screen("screen_ap_1280.jpg", (1280, 720))
        self.assertFalse(screen.board_present(img))
        self.assertFalse(screen.Reader(MATCHER).read_captains(img).present)

    def _old_cells(self):
        """Клетки доски старого формата (22 хода) с известными героями."""
        img = Image.open(os.path.join(FIXTURES, "screen_cm_old.jpg")).convert("RGB")
        ox, oy = -50, -40
        picks, bans = [], []
        rows = [(160, 205), (213, 258), (355, 400), (407, 452)]
        for side, (x0, x1) in (("radiant", (57, 145)), ("dire", (230, 318))):
            for k, (y0, y1) in enumerate(rows):
                if side == "radiant" and k == 3:
                    continue                    # на этом месте кнопка PICK
                picks.append(img.crop((ox + x0, oy + y0, ox + x1, oy + y1)))
        for x0, x1 in ((90, 145), (230, 285)):
            for y0, y1 in ((45, 75), (82, 112), (118, 148), (275, 305), (311, 341)):
                bans.append(img.crop((ox + x0, oy + y0, ox + x1, oy + y1)))
        return picks, bans

    def test_picks_and_bans(self):
        picks, bans = self._old_cells()
        found = [screen.judge(MATCHER.rank(c, "pick")) for c in picks]
        self.assertEqual(found, ["Lion", "Grimstroke", "Kunkka", "Witch Doctor", "Axe", "Pudge",
                                 "Death Prophet"])
        found = [screen.judge(MATCHER.rank(c, "ban")) for c in bans]
        expected = ["Silencer", "Bristleback", None, "Phantom Assassin", "Storm Spirit", "Ursa",
                    "Windranger", "Juggernaut", "Anti-Mage", "Slark"]
        # третий бан программа честно не узнаёт — под вопросом, а не наугад
        self.assertEqual(found, expected)
        self.assertTrue(all(screen.has_hero(c) for c in picks + bans))


class JudgeTest(unittest.TestCase):

    def test_thresholds(self):
        self.assertEqual(screen.judge([(0.3, "Lina"), (0.8, "Lion")]), "Lina")
        self.assertIsNone(screen.judge([(0.3, "Lina"), (0.35, "Lion")]))     # мал отрыв
        self.assertIsNone(screen.judge([(0.9, "Lina"), (1.5, "Lion")]))      # далеко
        self.assertIsNone(screen.judge([]))

    def test_duplicates(self):
        a = screen.Cell(True, "pick", [(0.2, "Lina"), (0.9, "Lion")], "Lina")
        b = screen.Cell(True, "pick", [(0.5, "Lina"), (0.7, "Lion")], "Lina")
        screen.resolve_duplicates([a, b])
        self.assertEqual(a.hero, "Lina")
        self.assertIsNone(b.hero)
        self.assertTrue(b.unsure)


def _reading(values, mode="allpick"):
    cells = []
    for v in values:
        if v is None:
            cells.append(screen.Cell(False))
        else:
            cells.append(screen.Cell(True, "pick", [], None if v == "?" else v))
    return screen.Reading(mode, cells)


class TrackerTest(unittest.TestCase):

    def test_needs_agreement(self):
        t = screen.Tracker(agree=3)
        self.assertEqual(t.update(_reading(["Lina", None])), {})
        self.assertEqual(t.update(_reading(["Lina", None])), {})
        self.assertEqual(t.update(_reading(["Lina", None])), {0: "Lina", 1: None})

    def test_change_restarts(self):
        t = screen.Tracker(agree=2)
        t.update(_reading(["Lina"]))
        t.update(_reading(["Lina"]))
        self.assertEqual(t.update(_reading(["Lion"])), {})
        self.assertEqual(t.update(_reading(["Lion"])), {0: "Lion"})

    def test_unsure_is_a_value(self):
        t = screen.Tracker(agree=1)
        self.assertEqual(t.update(_reading(["?"])), {0: "?"})

    def test_mode_change_resets(self):
        t = screen.Tracker(agree=2)
        t.update(_reading(["Lina"]))
        self.assertEqual(t.update(_reading(["Lina"], mode="captains")), {})


class ApplyTest(unittest.TestCase):

    def test_allpick_sides(self):
        board, applied = DraftBoard(), {}
        stable = {0: "Lina", 1: "?", 5: "Axe", 6: None}
        done, gone = screen.apply_allpick(board, stable, "radiant", applied)
        self.assertEqual((done, gone), (["Lina", "Axe"], []))
        self.assertEqual(board.groups["allies"], ["Lina"])
        self.assertEqual(board.enemies, ["Axe"])

    def test_allpick_unknown_side(self):
        board = DraftBoard()
        self.assertEqual(screen.apply_allpick(board, {0: "Lina"}, None, {}), ([], []))
        self.assertEqual(board.groups["allies"], [])

    def test_removed_by_user_stays_removed(self):
        board, applied = DraftBoard(), {}
        screen.apply_allpick(board, {5: "Axe"}, "radiant", applied)
        board.remove("Axe")
        screen.apply_allpick(board, {5: "Axe"}, "radiant", applied)
        self.assertEqual(board.enemies, [])

    def test_slot_changed(self):
        board, applied = DraftBoard(), {}
        screen.apply_allpick(board, {5: "Axe"}, "radiant", applied)
        screen.apply_allpick(board, {5: "Pudge"}, "radiant", applied)
        self.assertEqual(board.enemies, ["Pudge"])

    def test_slot_emptied(self):
        """Клетка опустела — начался новый драфт: перенесённый оттуда герой уходит,
        а добавленный руками остаётся."""
        board, applied = DraftBoard(), {}
        screen.apply_allpick(board, {5: "Axe"}, "radiant", applied)
        board.add("enemies", "Lina")
        done, gone = screen.apply_allpick(board, {5: None}, "radiant", applied)
        self.assertEqual(gone, ["Axe"])
        self.assertEqual(board.enemies, ["Lina"])
        self.assertEqual(applied, {})

    def test_slot_became_unsure(self):
        """В клетке теперь неузнанный герой (новый матч): прежний уходит.
        Найдено прогоном: Zeus прошлого матча оставался среди врагов."""
        board, applied = DraftBoard(), {}
        screen.apply_allpick(board, {2: "Zeus"}, "dire", applied)
        screen.apply_allpick(board, {2: "?"}, "radiant", applied)
        self.assertEqual(board.enemies, [])
        self.assertEqual(board.groups["allies"], [])

    def test_captains_in_order(self):
        cm = CaptainsDraft()
        played, undone, conflict = screen.apply_captains(cm, {0: "Lina", 1: "Lion", 3: "Axe"})
        self.assertEqual(played, ["Lina", "Lion"])     # ход 3 не устоялся — дальше не пишем
        self.assertEqual((undone, conflict), (0, None))
        self.assertEqual(cm.current, 2)

    def test_captains_stops_at_unsure(self):
        cm = CaptainsDraft()
        played, _, _ = screen.apply_captains(cm, {0: "?", 1: "Lion"})
        self.assertEqual(played, [])

    def test_captains_conflict(self):
        cm = CaptainsDraft()
        cm.play("Lina")
        played, undone, conflict = screen.apply_captains(cm, {0: "Pudge", 1: "Lion"})
        self.assertEqual((played, undone, conflict), ([], 0, 0))
        self.assertEqual(cm.heroes[0], "Lina")         # записанное не переписывается

    def test_captains_already_taken(self):
        cm = CaptainsDraft()
        played, undone, conflict = screen.apply_captains(cm, {0: "Lina", 1: "Lina"})
        self.assertEqual((played, undone, conflict), (["Lina"], 0, 1))

    def test_captains_fewer_moves_on_screen(self):
        """Экран показывает меньше ходов (новый драфт) — лишние снимаются."""
        cm = CaptainsDraft()
        for hero in ("Lina", "Lion", "Axe"):
            cm.play(hero)
        played, undone, conflict = screen.apply_captains(cm, {0: "Lina", 1: None, 2: None})
        self.assertEqual((played, undone, conflict), ([], 2, None))
        self.assertEqual(cm.heroes[:3], ["Lina", None, None])
        cm2 = CaptainsDraft()
        cm2.play("Lina")
        screen.apply_captains(cm2, {i: None for i in range(24)})
        self.assertEqual(cm2.current, 0)

    def test_captains_unsettled_cell_keeps_moves(self):
        """Ход, который ещё не устоялся (нет в stable), ничего не снимает."""
        cm = CaptainsDraft()
        cm.play("Lina")
        screen.apply_captains(cm, {})
        self.assertEqual(cm.heroes[0], "Lina")


class SamplesTest(unittest.TestCase):

    def test_roundtrip_and_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            cell = Image.new("RGB", (60, 40), (120, 30, 30))
            for _ in range(screen.MAX_SAMPLES + 2):
                screen.save_sample(folder, "pick", "Anti-Mage", cell)
            screen.save_sample(folder, "pick", "Nobody", cell)
            samples = screen.load_samples(folder, PORTRAITS)
            self.assertEqual(len(samples), screen.MAX_SAMPLES)
            self.assertEqual({(k, h) for k, h, _ in samples}, {("pick", "Anti-Mage")})

    def test_no_folder(self):
        self.assertEqual(screen.load_samples(None, PORTRAITS), [])
        screen.save_sample(None, "pick", "Lina", Image.new("RGB", (4, 4)))   # не падает

    def test_sample_teaches_matcher(self):
        """Подтверждённая клетка узнаётся по образцу, даже если портрет на неё не похож."""
        _, bans = CaptainsTest()._old_cells()
        cell = bans[2]
        self.assertIsNone(screen.judge(MATCHER.rank(cell, "ban")))
        taught = screen.Matcher(PORTRAITS, samples=[("ban", "Wraith King", cell)])
        self.assertEqual(screen.judge(taught.rank(cell, "ban")), "Wraith King")


if __name__ == "__main__":
    unittest.main()
