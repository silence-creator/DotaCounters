"""Подсказки при вводе имени героя. Сеть не нужна.

Запуск:  python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotacounters.heroes import (  # noqa: E402
    ALL_HEROES, NICKNAMES, SUGGEST_LIMIT, _key, best_match, resolve, suggest,
)


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


class NamesTest(unittest.TestCase):
    """Имена в списке должны совпадать с Dotabuff: иначе поиск даёт «не найден»."""

    def test_names_dotabuff_knows(self):
        for hero in ("Pangolier", "Windranger", "Largo"):
            self.assertIn(hero, ALL_HEROES)
        for old in ("Pango", "Wind Ranger"):
            self.assertNotIn(old, ALL_HEROES)

    def test_old_names_still_find_the_hero(self):
        """Старые имена могли остаться в недавних и избранном."""
        self.assertEqual(resolve("Pango"), "Pangolier")
        self.assertEqual(resolve("Wind Ranger"), "Windranger")


class NicknameTest(unittest.TestCase):
    def test_slang_comes_first(self):
        for typed, hero in (("бара", "Spirit Breaker"), ("шейкер", "Earthshaker"),
                            ("sf", "Shadow Fiend"), ("сф", "Shadow Fiend"),
                            ("войд", "Faceless Void"), ("карл", "Invoker")):
            self.assertEqual(suggest(typed)[0], hero, typed)

    def test_real_prefix_is_not_crowded_out(self):
        """«void» — это и прозвище Faceless Void, и начало Void Spirit."""
        self.assertEqual(suggest("void")[:2], ["Faceless Void", "Void Spirit"])
        self.assertEqual(suggest("pud")[0], "Pudge")

    def test_every_nickname_points_at_a_real_hero(self):
        self.assertEqual(sorted(set(NICKNAMES) - set(ALL_HEROES)), [])

    def test_no_nickname_is_shared_or_shadows_a_name(self):
        owners = {}
        names = {_key(hero): hero for hero in ALL_HEROES}
        for hero, aliases in NICKNAMES.items():
            for alias in aliases:
                key = _key(alias)
                self.assertEqual(owners.setdefault(key, hero), hero,
                                 "«%s» у двух героев" % alias)
                self.assertIn(names.get(key, hero), (hero,),
                              "«%s» совпадает с именем другого героя" % alias)


class BestMatchTest(unittest.TestCase):
    """Что уйдёт на Dotabuff, если набрать и нажать Enter."""

    def test_typed_names(self):
        self.assertEqual(best_match("пудж"), "Pudge")
        self.assertEqual(best_match("бара"), "Spirit Breaker")
        self.assertEqual(best_match("anti-mage"), "Anti-Mage")

    def test_nothing_similar_is_kept_as_typed(self):
        self.assertEqual(best_match("  qqqzzz "), "qqqzzz")


if __name__ == "__main__":
    unittest.main(verbosity=2)
