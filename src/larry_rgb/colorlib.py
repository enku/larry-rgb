"""Color utilities"""

from typing import Iterator

from larry.color import Color


def get_gradient_colors(
    colors: Iterator[Color], prev_stop_color: Color | None
) -> tuple[Color, Color]:
    """Return the start_color and stop_color for the next gradient cycle"""
    return prev_stop_color if prev_stop_color else next(colors), next(colors)
