"""Tests for the larry_rgb.colorlib module"""

# pylint: disable=missing-docstring
import unittest

from larry import Color
from unittest_fixtures import Fixtures, given

from larry_rgb import colorlib

from .lib import GREEN, RED, color_cycle


@given(color_cycle)
class GetGradientColors(unittest.TestCase):
    """Tests for the get_gradient_colors() method"""

    def test_with_none(self, fixtures: Fixtures) -> None:
        colors = fixtures.color_cycle
        start_color, stop_color = colorlib.get_gradient_colors(colors, None)

        self.assertEqual(start_color, RED)
        self.assertEqual(stop_color, GREEN)

    def test_with_prev_stop_color(self, fixtures: Fixtures) -> None:
        prev_stop_color = Color(45, 23, 212)
        colors = fixtures.color_cycle
        start_color, stop_color = colorlib.get_gradient_colors(colors, prev_stop_color)

        self.assertEqual(start_color, Color(prev_stop_color))
        self.assertEqual(stop_color, RED)
