"""Tests lib"""

from itertools import cycle
from typing import Iterable

from larry import Color
from unittest_fixtures import Fixtures, fixture

import larry_rgb

RED = Color("red")
GREEN = Color("green")
BLUE = Color("blue")


@fixture()
def clear_cache(_: Fixtures) -> None:
    """Clear the get_effect cache"""
    larry_rgb.get_effect.cache_clear()


@fixture()
def color_cycle(
    _: Fixtures, colors: Iterable[Color] = (RED, GREEN, BLUE)
) -> Iterable[Color]:
    """Return an endless cycle of colors"""
    return cycle(colors)
