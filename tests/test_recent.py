"""Недавние герои, избранное и геометрия окна. Сеть не нужна.

Запуск:  python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotacounters.recent import (  # noqa: E402
    MAX_FAVOURITES, MAX_HISTORY, clean_list, is_favourite, remember,
    sane_geometry, sane_position, toggle_favourite,
)


class HistoryTest(unittest.TestCase):
    def test_newest_first(self):
        history = remember(remember([], "Pudge"), "Lina")
        self.assertEqual(history, ["Lina", "Pudge"])

    def test_repeat_moves_to_front_without_duplicating(self):
        history = remember(["Lina", "Pudge", "Axe"], "pudge")
        self.assertEqual(history, ["pudge", "Lina", "Axe"])

    def test_limit(self):
        history = []
        for i in range(MAX_HISTORY + 5):
            history = remember(history, "Hero %d" % i)
        self.assertEqual(len(history), MAX_HISTORY)
        self.assertEqual(history[0], "Hero %d" % (MAX_HISTORY + 4))

    def test_empty_name_changes_nothing(self):
        self.assertEqual(remember(["Lina"], "   "), ["Lina"])


class FavouritesTest(unittest.TestCase):
    def test_toggle_adds_and_removes(self):
        favourites = toggle_favourite([], "Pudge")
        self.assertEqual(favourites, ["Pudge"])
        self.assertEqual(toggle_favourite(favourites, "Pudge"), [])

    def test_toggle_ignores_case(self):
        self.assertEqual(toggle_favourite(["Pudge"], "pudge"), [])

    def test_is_favourite(self):
        self.assertTrue(is_favourite(["Pudge"], "pudge"))
        self.assertFalse(is_favourite(["Pudge"], "Lina"))
        self.assertFalse(is_favourite(None, "Lina"))

    def test_limit_is_not_exceeded(self):
        favourites = [str(i) for i in range(MAX_FAVOURITES)]
        self.assertEqual(toggle_favourite(favourites, "Pudge"), favourites)


class CleanListTest(unittest.TestCase):
    def test_garbage_from_config_is_dropped(self):
        self.assertEqual(clean_list(["Pudge", 5, None, "  ", "Lina"], 10), ["Pudge", "Lina"])
        self.assertEqual(clean_list("не список", 10), [])
        self.assertEqual(clean_list(None, 10), [])

    def test_duplicates_and_limit(self):
        self.assertEqual(clean_list(["Pudge", "pudge", "Lina"], 10), ["Pudge", "Lina"])
        self.assertEqual(len(clean_list([str(i) for i in range(50)], 8)), 8)


class GeometryTest(unittest.TestCase):
    SCREEN = (1920, 1080)

    def test_good_value_passes(self):
        self.assertEqual(sane_geometry("800x900+100+50", *self.SCREEN), "800x900+100+50")

    def test_garbage_is_rejected(self):
        for value in ("", "чепуха", "800x900", None, 42, "0x0+0+0", "800x900+10"):
            self.assertIsNone(sane_geometry(value, *self.SCREEN), repr(value))

    def test_larger_than_screen_is_rejected(self):
        self.assertIsNone(sane_geometry("3000x900+0+0", *self.SCREEN))
        self.assertIsNone(sane_geometry("800x2000+0+0", *self.SCREEN))

    def test_smaller_than_minimum_is_rejected(self):
        self.assertIsNone(sane_geometry("300x300+0+0", *self.SCREEN))

    def test_offscreen_is_rejected(self):
        """Монитор могли отключить — окно не должно открыться в пустоте."""
        self.assertIsNone(sane_geometry("800x900+3000+10", *self.SCREEN))
        self.assertIsNone(sane_geometry("800x900+10+1075", *self.SCREEN))
        self.assertIsNone(sane_geometry("800x900-900+10", *self.SCREEN))

    def test_slightly_offscreen_left_is_kept(self):
        """Чуть выехавшее за край окно поймать мышью ещё можно."""
        self.assertEqual(sane_geometry("800x900-100+10", *self.SCREEN), "800x900-100+10")


class PositionTest(unittest.TestCase):
    """Место оверлея: окно без рамки должно целиком помещаться на экране."""

    SCREEN = (1920, 1080, 340, 560)

    def test_fits(self):
        self.assertEqual(sane_position("+1500+100", *self.SCREEN), "+1500+100")

    def test_off_screen_or_broken(self):
        for value in ("+1700+100", "+100+600", "-10+100", "+100-5", "junk", "", None, 42):
            self.assertIsNone(sane_position(value, *self.SCREEN), repr(value))


if __name__ == "__main__":
    unittest.main(verbosity=2)
