"""Color utilities"""
from __future__ import annotations

import tempfile
from itertools import cycle
from xml.etree import ElementTree

import cairosvg
import PIL
from colorthief import ColorThief
from larry import Color, ColorList


def get_gradient_colors(
    colors: cycle[Color], prev_stop_color: Color | None
) -> tuple[Color, Color]:
    """Return the start_color and stop_color for the next gradient cycle"""
    return prev_stop_color if prev_stop_color else next(colors), next(colors)


def get_colors(input_fn: str, color_count: int, quality: int) -> ColorList:
    """Return the dominant color of the given image"""
    try:
        color_thief = ColorThief(input_fn)
    except PIL.UnidentifiedImageError as unidentified_image_error:
        # Maybe it's an SVG
        with tempfile.NamedTemporaryFile("wb", buffering=0) as tmp:
            try:
                tmp.write(convert_svg_to_png(input_fn))
            except ElementTree.ParseError:
                # Not a (good) SVG either. Raise the original error
                raise unidentified_image_error from unidentified_image_error

            color_thief = ColorThief(tmp.name)

    return [Color(*rgb) for rgb in color_thief.get_palette(color_count, quality)]


def convert_svg_to_png(svg_fn: str) -> bytes:
    """Convert the given svg filename to PNG and return the PNG bytes"""
    return cairosvg.svg2png(url=svg_fn)
