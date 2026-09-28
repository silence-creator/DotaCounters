"""Темы: читаемость текста (контраст по WCAG) и перевод старых названий тем."""

import unittest

from dotacounters.themes import DEFAULT_THEME, THEMES, theme_key


def _luminance(color):
    """Относительная яркость цвета #rrggbb по WCAG 2."""
    channels = []
    for i in (1, 3, 5):
        c = int(color[i:i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


class ContrastTest(unittest.TestCase):
    """Текст и числа — не ниже 4.5:1 (AA для обычного текста) на всех фонах;
    TEXT4 — будущие ходы и заглушки, для него 3:1."""

    BACKGROUNDS = ("BG", "TOPBAR", "PANEL")

    def check(self, fg, minimum):
        for name, theme in THEMES.items():
            for bg in self.BACKGROUNDS:
                ratio = contrast(theme[fg], theme[bg])
                self.assertGreaterEqual(ratio, minimum,
                                        "%s: %s на %s — %.2f:1" % (name, fg, bg, ratio))

    def test_text_is_readable(self):
        for fg in ("TEXT", "TEXT2", "TEXT3", "GOLD", "GOOD", "BAD", "RADIANT", "DIRE"):
            self.check(fg, 4.5)

    def test_faint_text_is_still_visible(self):
        self.check("TEXT4", 3.0)

    def test_text_on_gold_button(self):
        for name, theme in THEMES.items():
            self.assertGreaterEqual(contrast(theme["ON_GOLD"], theme["GOLD"]), 4.5, name)


class ThemeKeyTest(unittest.TestCase):

    def test_known_names_kept(self):
        for key in THEMES:
            self.assertEqual(theme_key(key), key)

    def test_old_light_theme_becomes_light(self):
        self.assertEqual(theme_key("ghost"), "light")

    def test_old_and_unknown_become_default(self):
        for value in ("neon", "matrix", None, "", 5):
            self.assertEqual(theme_key(value), DEFAULT_THEME)


if __name__ == "__main__":
    unittest.main(verbosity=2)
