"""Tests for the larry_rgb.colorlib module"""
# pylint: disable=missing-docstring
import importlib.metadata
import tempfile
import unittest
from itertools import cycle

import PIL
from larry import Color

from larry_rgb import colorlib

RED = Color("red")
GREEN = Color("green")
BLUE = Color("blue")


class GetColorsTestCase(unittest.TestCase):
    """tests for the get_colors() function"""

    def test_against_svg_image(self):
        larry_pkg = importlib.metadata.distribution("larry")
        svg_file = larry_pkg.locate_file("larry/data/gentoo-cow-gdm-remake.svg")
        image_colors = colorlib.get_colors(str(svg_file), 3, 15)

        expected = {
            Color(34, 65, 80),
            Color(123, 139, 147),
            Color(4, 4, 4),
            Color(84, 100, 111),
        }
        self.assertEqual(set(image_colors), expected)

    def test_against_bad_svg_image(self):
        with tempfile.NamedTemporaryFile(suffix=".svg") as bad_svg:
            bad_svg.write(b"not really an svg")
            bad_svg.flush()

            with self.assertRaises(PIL.UnidentifiedImageError):
                colorlib.get_colors(bad_svg.name, 3, 15)


class GetGradientColors(unittest.TestCase):
    """Tests for the get_gradient_colors() method"""

    def test_with_none(self):
        colors = cycle([RED, GREEN, BLUE])
        start_color, stop_color = colorlib.get_gradient_colors(colors, None)

        self.assertEqual(start_color, RED)
        self.assertEqual(stop_color, GREEN)

    def test_with_prev_stop_color(self):
        prev_stop_color = Color(45, 23, 212)
        colors = cycle([RED, GREEN, BLUE])
        start_color, stop_color = colorlib.get_gradient_colors(colors, prev_stop_color)

        self.assertEqual(start_color, Color(prev_stop_color))
        self.assertEqual(stop_color, RED)
