"""Подсказки при вводе имени героя. Сеть не нужна.

Запуск:  python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotacounters.heroes import ALL_HEROES, SUGGEST_LIMIT, suggest  # noqa: E402


class SuggestTest(unittest.TestCase):
    def test_prefix(self):
        self.assertEqual(suggest("pud"), ["Pudge"])
        self.assertEqual(suggest("drow"), ["Drow Ranger"])

    def test_case_does_not_matter(self):
        self.assertEqual(suggest("PUDGE"), suggest("pudge"))

    def test_punctuation_can_be_skipped(self):
        """Дефис и апостроф при вводе обычно не набирают."""
        self.assertEqual(suggest("antimage"), ["Anti-Mage"])
        self.assertEqual(suggest("natures"), ["Nature's Prophet"])
        self.assertEqual(suggest("anti-m"), ["Anti-Mage"])

    def test_prefix_matches_come_first(self):
        found = suggest("war")
        self.assertEqual(found[0], "Warlock")
        self.assertIn("Troll Warlord", found)
        self.assertLess(found.index("Warlock"), found.index("Troll Warlord"))

    def test_substring_match(self):
        self.assertIn("Clockwerk", suggest("ck"))

    def test_empty_query_gives_nothing(self):
        for query in ("", "   ", "-"):
            self.assertEqual(suggest(query), [], repr(query))

    def test_unknown_gives_nothing(self):
        self.assertEqual(suggest("zzzz"), [])

    def test_limit(self):
        self.assertLessEqual(len(suggest("a")), SUGGEST_LIMIT)
        self.assertEqual(len(suggest("a", limit=3)), 3)

    def test_every_hero_is_reachable_by_its_own_name(self):
        for hero in ALL_HEROES:
            self.assertIn(hero, suggest(hero), hero)


if __name__ == "__main__":
    unittest.main(verbosity=2)
