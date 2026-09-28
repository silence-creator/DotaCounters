"""Пересчёт пикселей макета в экранные при масштабе Windows 125%+."""

import unittest
from unittest import mock

from dotacounters.ui import dpi


class _Widget:
    def __init__(self, name, image=""):
        self.widgetName = name
        self._image = image

    def cget(self, key):
        assert key == "image"
        return self._image


class PxTest(unittest.TestCase):

    def test_scales_ints_and_pad_tuples(self):
        with mock.patch.object(dpi, "SCALE", 1.25):
            self.assertEqual(dpi.px(12), 15)
            self.assertEqual(dpi.px((8, 0)), (10, 0))
            self.assertEqual(dpi.px_size((64, 36)), (80, 45))

    def test_one_pixel_lines_stay_thin(self):
        with mock.patch.object(dpi, "SCALE", 1.25):
            self.assertEqual(dpi.px(1), 1)

    def test_leaves_other_values_alone(self):
        with mock.patch.object(dpi, "SCALE", 1.5):
            self.assertEqual(dpi.px("10"), "10")
            self.assertIs(dpi.px(True), True)
            self.assertEqual(dpi.px(0), 0)
            self.assertEqual(dpi.px(-1), -1)


class ScaledOptionsTest(unittest.TestCase):

    def scaled(self, widget, **cnf):
        with mock.patch.object(dpi, "SCALE", 1.5):
            return dpi._scaled(widget, cnf)

    def test_padding_scaled_everywhere(self):
        out = self.scaled(_Widget("entry"), padx=10, pady=(4, 0), bg="#000")
        self.assertEqual(out, {"padx": 15, "pady": (6, 0), "bg": "#000"})

    def test_frame_size_is_pixels(self):
        self.assertEqual(self.scaled(_Widget("frame"), width=300, height=46),
                         {"width": 450, "height": 69})

    def test_text_label_width_is_characters(self):
        self.assertEqual(self.scaled(_Widget("label"), width=22), {"width": 22})
        self.assertEqual(self.scaled(_Widget("entry"), width=30), {"width": 30})

    def test_image_label_width_is_pixels(self):
        self.assertEqual(self.scaled(_Widget("label"), image="img1", width=40),
                         {"image": "img1", "width": 60})
        self.assertEqual(self.scaled(_Widget("label", image="img1"), width=40), {"width": 60})


if __name__ == "__main__":
    unittest.main(verbosity=2)
