"""Tests for the larry_rgb.colorlib module"""

# pylint: disable=missing-docstring
import unittest
from itertools import cycle

from larry import Color

from larry_rgb import colorlib

RED = Color("red")
GREEN = Color("green")
BLUE = Color("blue")


class GetGradientColors(unittest.TestCase):
    """Tests for the get_gradient_colors() method"""

    def test_with_none(self) -> None:
        colors = cycle([RED, GREEN, BLUE])
        start_color, stop_color = colorlib.get_gradient_colors(colors, None)

        self.assertEqual(start_color, RED)
        self.assertEqual(stop_color, GREEN)

    def test_with_prev_stop_color(self) -> None:
        prev_stop_color = Color(45, 23, 212)
        colors = cycle([RED, GREEN, BLUE])
        start_color, stop_color = colorlib.get_gradient_colors(colors, prev_stop_color)

        self.assertEqual(start_color, Color(prev_stop_color))
        self.assertEqual(stop_color, RED)
