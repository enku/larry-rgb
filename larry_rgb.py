"""Set the OpenRGB rbg colors to the dominant color of the image"""
from __future__ import annotations

import os.path
import tempfile
import time
from configparser import ConfigParser
from dataclasses import dataclass
from functools import cache, cached_property
from itertools import cycle
from threading import Lock, Thread
from typing import IO, Iterator
from xml.etree import ElementTree

import cairosvg
import PIL
from colorthief import ColorThief
from larry import Color, ColorList, ConfigType
from openrgb import OpenRGBClient
from openrgb.orgb import Device
from openrgb.utils import RGBColor


@dataclass
class RGB:
    """Config for OpenRGB"""

    address: str = "127.0.0.1"
    port: int = 6742

    def __post_init__(self) -> None:
        self.openrgb = OpenRGBClient(self.address, self.port)
        for device in self.openrgb.ee_devices:
            device.set_mode("Direct")

    def set_color(self, color: Color) -> None:
        """Send the given color to openrgb"""
        for device in self.openrgb.ee_devices:
            device.set_color(RGBColor(color.red, color.green, color.blue))

    @property
    def devices(self) -> list[Device]:
        """Return the list of direct-mode compatible RGB devices"""
        assert hasattr(self, "openrgb")

        return self.openrgb.ee_devices


class Effect:
    """Effects thread"""

    def __init__(self) -> None:
        self.config = self.initial_config()
        self.lock = Lock()
        self.image_colors: ColorList = []
        self.colors: Iterator[Color] = cycle([Color(0, 0, 0)])
        self.thread = Thread(target=self.run)
        self.die = False

    @cached_property
    def rgb(self) -> RGB:
        """Returns the RGB instance.

        A (cached) property so we only instantiate it once, lazily
        """
        assert self.config is not None

        address_and_port = self.config.get("address", fallback="localhost")
        address, _, port_str = address_and_port.partition(":")
        port = int(port_str) if port_str else 6742

        return RGB(address=address, port=port)

    def run(self) -> None:  # pragma: no cover
        """Effect thread target"""
        stop_color = None

        while not self.die:
            stop_color = self.set_next_gradient(stop_color)

    def set_next_gradient(self, prev_stop_color: Color | None) -> Color:
        """Set the next gradient in the cycle

        If prev_stop_color is None, the start color is the next color in the colors
        cycle, otherwise it's the prev_stop_color. The stop color is the next color in
        the colors cycle.
        """
        start_color, stop_color = self.get_gradient_colors(prev_stop_color)
        steps = self.config.getint("gradient_steps", fallback=20)

        for color in Color.gradient(start_color, stop_color, steps):
            is_image_color = color in self.image_colors
            pause_after_fade = self.config.getfloat("pause_after_fade", fallback=0.0)
            rgb_color = RGBColor(color.red, color.green, color.blue)

            for device in self.rgb.devices:
                device.set_color(rgb_color)
            if is_image_color and pause_after_fade:
                time.sleep(pause_after_fade / 2)

            if not (is_image_color and pause_after_fade):
                time.sleep(self.config.getfloat("interval", fallback=0.05))

        return stop_color

    def get_gradient_colors(self, prev_stop_color: Color | None) -> tuple[Color, Color]:
        """Return the start_color and stop_color for the next gradient cycle"""
        with self.lock:
            start_color = prev_stop_color if prev_stop_color else next(self.colors)
            stop_color = next(self.colors)

        return start_color, stop_color

    def reset(self, config: ConfigType) -> None:
        """Reset the thread's color list"""
        input_fn = os.path.expanduser(config["input"])
        color_count = config.getint("max_palette_size", fallback=10)
        quality = config.getint("quality", fallback=10)

        with self.lock:
            self.image_colors = get_colors(input_fn, color_count, quality)
            self.colors = cycle(self.image_colors)
            self.config = config

    def initial_config(self) -> ConfigType:
        """Return a dummy config.

        Because the initializer needs one
        """
        parser = ConfigParser()
        parser.add_section("rgb")

        return ConfigType(parser, "rgb")


def get_colors(
    input_fn: str, color_count: int, quality: int, from_svg: bool = False
) -> ColorList:
    """Return the dominant color of the given image"""
    try:
        color_thief = ColorThief(input_fn)
    except PIL.UnidentifiedImageError as unidentified_image_error:
        if from_svg:
            raise

        # Maybe it's an svg
        with tempfile.NamedTemporaryFile("wb") as tmp:
            try:
                convert_svg_to_png(str(input_fn), tmp)
            except ElementTree.ParseError:
                # Not a (good) SVG either. Raise the original error
                raise unidentified_image_error

            tmp.flush()
            return get_colors(tmp.name, color_count, quality, from_svg=True)

    palette = color_thief.get_palette(color_count, quality)

    return [Color(*rgb) for rgb in palette]


def convert_svg_to_png(svg_fn: str, outfile: IO[bytes]) -> None:
    """Convert the given svg filename to PNG and write to outfile object"""
    cairosvg.svg2png(url=svg_fn, write_to=outfile)


@cache
def get_effect() -> Effect:
    """Return the "global" Effect instance"""
    return Effect()


def plugin(_colors: ColorList, config: ConfigType) -> None:
    """RGB plugin handler"""
    effect = get_effect()
    effect.reset(config)

    if not effect.thread.is_alive():
        effect.thread.start()
