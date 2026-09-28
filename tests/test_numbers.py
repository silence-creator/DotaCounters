"""Короткая запись числа матчей.

Запуск:  python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotacounters.numbers import short_count  # noqa: E402


class ShortCountTest(unittest.TestCase):
    def test_english(self):
        self.assertEqual(short_count(663), "663")
        self.assertEqual(short_count(1500), "1.5k")
        self.assertEqual(short_count(48459), "48k")
        self.assertEqual(short_count(327517), "327k")
        self.assertEqual(short_count(1_234_567), "1.2M")
        self.assertEqual(short_count(26_634_519), "26M")

    def test_never_rounds_up(self):
        """1 999 — редкая пара, «2k» рядом с ней путало бы."""
        self.assertEqual(short_count(1999), "1.9k")
        self.assertEqual(short_count(2000), "2k")

    def test_russian(self):
        self.assertEqual(short_count(1500, "к", " млн", ","), "1,5к")
        self.assertEqual(short_count(2_000_000, "к", " млн", ","), "2 млн",
                         "«2,0 млн» пишется без нуля")

    def test_unknown(self):
        self.assertEqual(short_count(None), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
