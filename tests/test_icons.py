"""Адреса иконок патча и вписывание картинок в рамку. Сеть не нужна.

Запуск:  python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotacounters.icons import (  # noqa: E402
    LOCAL_ICON_PREFIX, draw_local_icon, fit_to_box, is_glyph, rasterize_svg,
    thicken, tint,
)
from dotacounters.patches import (  # noqa: E402
    ICON_CDN, ability_icon_url, hero_icon_url, item_icon_url, stat_icon_url,
)


class IconUrlTest(unittest.TestCase):
    """Адреса проверены вручную на CDN Valve на патче 7.41e."""

    def test_hero(self):
        self.assertEqual(hero_icon_url("npc_dota_hero_axe"),
                         ICON_CDN + "/heroes/icons/axe.png")

    def test_item_strips_prefix(self):
        self.assertEqual(item_icon_url("item_abyssal_blade"),
                         ICON_CDN + "/items/abyssal_blade.png")

    def test_item_prefix_only_at_start(self):
        # «item_» внутри имени трогать нельзя
        self.assertEqual(item_icon_url("item_foo_item_bar"),
                         ICON_CDN + "/items/foo_item_bar.png")

    def test_ability_keeps_key(self):
        self.assertEqual(ability_icon_url("bane_nightmare"),
                         ICON_CDN + "/abilities/bane_nightmare.png")

    def test_missing_key_gives_no_url(self):
        for fn in (hero_icon_url, item_icon_url, ability_icon_url):
            self.assertIsNone(fn(None))
            self.assertIsNone(fn(""))


class StatIconTest(unittest.TestCase):
    """Значки характеристик: все 12 имён, встреченных в патчах 7.36b–7.41f."""

    SEEN_IN_PATCHES = ("damage", "strength", "agility", "intelligence", "movement",
                       "armor", "attack_speed", "health_regen", "mana_regen",
                       "attack_range", "attack_time", "projectile_speed")

    def test_every_seen_name_has_an_icon(self):
        for name in self.SEEN_IN_PATCHES:
            self.assertIsNotNone(stat_icon_url(name), name)

    def test_attributes_and_stats_urls(self):
        self.assertEqual(stat_icon_url("agility"), ICON_CDN + "/icons/hero_agility.png")
        self.assertEqual(stat_icon_url("movement"),
                         ICON_CDN + "/heroes/stats/icon_movement_speed.png")

    def test_regen_is_drawn_locally(self):
        for name in ("health_regen", "mana_regen"):
            url = stat_icon_url(name)
            self.assertTrue(url.startswith(LOCAL_ICON_PREFIX), url)
            img = draw_local_icon(url[len(LOCAL_ICON_PREFIX):])
            self.assertIsNotNone(img)
            self.assertEqual(fit_to_box(img, (24, 16)).size, (24, 16))

    def test_unknown_gives_nothing(self):
        self.assertIsNone(stat_icon_url("no_such_stat"))
        self.assertIsNone(stat_icon_url(None))
        self.assertIsNone(draw_local_icon("no_such_stat"))


class RasterizeSvgTest(unittest.TestCase):
    """Минимальный SVG: хватает для значка таланта, остальное честно отвергается."""

    # Квадрат 100x100 с квадратной дыркой 40x40 в центре, два контура в одном path
    RING = ('<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M0 0 L100 0 L100 100 L0 100 Z M30 30 L70 30 L70 70 L30 70 Z" '
            'fill="white" fill-opacity="0.5"/></svg>')

    def test_inner_contour_is_a_hole(self):
        img = rasterize_svg(self.RING, height=100)
        self.assertEqual(img.size, (100, 100))
        self.assertEqual(img.getpixel((50, 50))[3], 0, "центр — дырка")
        self.assertGreater(img.getpixel((10, 10))[3], 0, "кольцо залито")

    def test_colour_and_opacity(self):
        r, g, b, a = rasterize_svg(self.RING, height=100).getpixel((10, 10))
        self.assertEqual((r, g, b), (255, 255, 255))
        self.assertAlmostEqual(a, 128, delta=2)

    def test_relative_commands_match_absolute(self):
        rel = self.RING.replace(
            "M0 0 L100 0 L100 100 L0 100 Z M30 30 L70 30 L70 70 L30 70 Z",
            "m0 0 h100 v100 h-100 z M30 30 l40 0 l0 40 l-40 0 z")
        self.assertEqual(rasterize_svg(rel, 50).tobytes(),
                         rasterize_svg(self.RING, 50).tobytes())

    def test_cubic_curve(self):
        svg = ('<svg viewBox="0 0 100 100"><path d="M0 100 C0 0 100 0 100 100 Z" '
               'fill="#ff0000"/></svg>')
        img = rasterize_svg(svg, 100)
        self.assertEqual(img.getpixel((50, 90))[:3], (255, 0, 0))
        self.assertEqual(img.getpixel((5, 5))[3], 0, "над дугой — пусто")

    def test_unsupported_input_raises(self):
        arc = '<svg viewBox="0 0 10 10"><path d="M0 0 A5 5 0 0 1 10 10 Z"/></svg>'
        stray = '<svg viewBox="0 0 10 10"><path d="M0 0 L10 0 L10 10 Z 5 5"/></svg>'
        for svg in (arc, stray, '<svg><path d="M0 0 L1 1 Z"/></svg>'):
            with self.assertRaises(ValueError):
                rasterize_svg(svg, 20)

    def test_tint_keeps_shape_changes_colour(self):
        img = rasterize_svg(self.RING, height=100)
        dark = tint(img, "#1a2030")
        self.assertEqual(dark.getpixel((10, 10))[:3], (0x1a, 0x20, 0x30))
        self.assertEqual(dark.getchannel("A").tobytes(), img.getchannel("A").tobytes())

    def test_only_svg_is_a_glyph(self):
        self.assertTrue(is_glyph(ICON_CDN + "/icons/talents.svg"))
        self.assertFalse(is_glyph(ICON_CDN + "/items/blink.png"))
        self.assertFalse(is_glyph(LOCAL_ICON_PREFIX + "health_regen"),
                         "рисованные значки регенерации цветные — не перекрашиваем")
        self.assertFalse(is_glyph(None))

    def test_all_themes_have_a_hex_text_colour(self):
        from dotacounters.themes import THEMES
        for name, theme in THEMES.items():
            self.assertRegex(theme["TEXT_PRIMARY"], r"^#[0-9a-fA-F]{6}$", name)

    def test_thicken_widens_thin_lines(self):
        img = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
        for y in range(96):
            img.putpixel((48, y), (255, 255, 255, 255))
        before = sum(1 for p in img.getchannel("A").tobytes() if p)
        after = sum(1 for p in thicken(img).getchannel("A").tobytes() if p)
        self.assertGreater(after, before * 5)


class FitToBoxTest(unittest.TestCase):
    BOX = (24, 16)

    def test_output_is_exactly_the_box(self):
        # Квадратная способность, вытянутый предмет, высокий портрет
        for size in ((128, 128), (88, 64), (32, 64), (1, 1)):
            img = fit_to_box(Image.new("RGB", size, "red"), self.BOX)
            self.assertEqual(img.size, self.BOX, "исходник %s" % (size,))
            self.assertEqual(img.mode, "RGBA")

    def test_aspect_is_kept_and_rest_is_transparent(self):
        # Квадрат в рамке 24x16 становится 16x16 по центру, по бокам — прозрачно
        img = fit_to_box(Image.new("RGB", (128, 128), "red"), self.BOX)
        self.assertEqual(img.getpixel((0, 8))[3], 0, "левый край должен быть прозрачным")
        self.assertEqual(img.getpixel((23, 8))[3], 0, "правый край должен быть прозрачным")
        self.assertEqual(img.getpixel((12, 8))[:3], (255, 0, 0), "центр — сама картинка")


if __name__ == "__main__":
    unittest.main(verbosity=2)
