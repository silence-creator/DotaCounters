"""Разбор горячей клавиши. Регистрация в системе здесь не проверяется.

Запуск:  python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotacounters.hotkey import (  # noqa: E402
    DEFAULT_HOTKEY, HOTKEY_PRESETS, MOD_ALT, MOD_CONTROL, MOD_SHIFT, format_hotkey,
    parse_hotkey,
)


class ParseTest(unittest.TestCase):
    def test_default(self):
        self.assertEqual(parse_hotkey(DEFAULT_HOTKEY), (MOD_CONTROL | MOD_SHIFT, ord("D")))

    def test_case_and_spaces_do_not_matter(self):
        self.assertEqual(parse_hotkey(" Ctrl + Alt + o "), (MOD_CONTROL | MOD_ALT, ord("O")))

    def test_function_and_named_keys(self):
        self.assertEqual(parse_hotkey("f9"), (0, 0x78))
        self.assertEqual(parse_hotkey("alt+space"), (MOD_ALT, 0x20))
        self.assertEqual(parse_hotkey("shift+5"), (MOD_SHIFT, ord("5")))

    def test_rejects_nonsense(self):
        for text in ("", "ctrl+", "ctrl+shift", "hyper+d", "ctrl+ф", "ctrl+f25", None):
            with self.assertRaises(ValueError, msg=repr(text)):
                parse_hotkey(text)

    def test_plain_letter_is_refused(self):
        """Иначе буква перестала бы печататься во всех программах."""
        with self.assertRaises(ValueError):
            parse_hotkey("d")


class PresetsTest(unittest.TestCase):
    def test_presets_parse_and_differ(self):
        parsed = [parse_hotkey(text) for text in HOTKEY_PRESETS]
        self.assertEqual(len(set(parsed)), len(parsed))
        self.assertIn(DEFAULT_HOTKEY, HOTKEY_PRESETS)

    def test_no_layout_switch_combo(self):
        """Alt+Shift в Windows переключает раскладку."""
        for text in HOTKEY_PRESETS:
            mods, _ = parse_hotkey(text)
            self.assertNotEqual(mods & (MOD_ALT | MOD_SHIFT), MOD_ALT | MOD_SHIFT, text)


class FormatTest(unittest.TestCase):
    def test_label(self):
        self.assertEqual(format_hotkey("ctrl+shift+d"), "Ctrl+Shift+D")
        self.assertEqual(format_hotkey("shift+ctrl+f5"), "Ctrl+Shift+F5")
        self.assertEqual(format_hotkey("alt+space"), "Alt+Space")


if __name__ == "__main__":
    unittest.main(verbosity=2)
