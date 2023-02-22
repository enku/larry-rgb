"""Set the OpenRGB rbg colors to the dominant color of the image"""
from __future__ import annotations

import asyncio
import os.path
import tempfile
from configparser import ConfigParser
from dataclasses import dataclass
from functools import cache, cached_property
from itertools import cycle
from typing import Awaitable, Callable
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

            # Not resizing the zones on OpenRGB 0.8 results in not all rgbs getting set
            # on my system.  See https://github.com/jath03/openrgb-python/discussions/64
            led_count = len(device.leds)
            for zone in device.zones:
                zone.resize(led_count)

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
        self.lock = asyncio.Lock()
        self.colors: cycle[Color] = cycle([])
        self.die = False
        self.running = False

    def is_alive(self) -> bool:
        """Return True if effect is running"""
        return self.running

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

    async def run(self) -> None:  # pragma: no cover
        """Effect thread target"""
        stop_color = None

        while not self.die:
            self.running = True
            async with self.lock:
                steps = self.config.getint("gradient_steps", fallback=20)
                pause_after_fade = self.config.getfloat(
                    "pause_after_fade", fallback=0.0
                )
                interval = self.config.getfloat("interval", fallback=0.05)

            stop_color = await set_gradient(
                self.rgb, self.colors, steps, pause_after_fade, interval, stop_color
            )
        self.running = False

    async def reset(self, config: ConfigType) -> None:
        """Reset the thread's color list"""
        input_fn = os.path.expanduser(config["input"])
        color_count = config.getint("max_palette_size", fallback=10)
        quality = config.getint("quality", fallback=10)

        async with self.lock:
            self.colors = cycle(get_colors(input_fn, color_count, quality))
            self.config = config

    def initial_config(self) -> ConfigType:
        """Return a dummy config.

        Because the initializer needs one
        """
        parser = ConfigParser()
        parser.add_section("rgb")

        return ConfigType(parser, "rgb")


async def set_gradient(
    rgb: RGB,
    colors: cycle[Color],
    steps: int,
    pause_after_fade: float,
    interval: float,
    prev_stop_color: Color | None,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> Color:
    """Set the next gradient in the cycle

    If prev_stop_color is None, the start color is the next color in the colors
    cycle, otherwise it's the prev_stop_color. The stop color is the next color in
    the colors cycle.
    """
    color_set: set[Color] = set()
    start_color, stop_color = get_gradient_colors(colors, prev_stop_color)
    color_set.add(start_color)
    color_set.add(stop_color)

    for color in Color.gradient(start_color, stop_color, steps):
        is_image_color = color in color_set
        rgb_color = RGBColor(color.red, color.green, color.blue)

        for device in rgb.devices:
            device.set_color(rgb_color)
        if is_image_color and pause_after_fade:
            await sleep(pause_after_fade / 2)

        if not (is_image_color and pause_after_fade):
            await sleep(interval)

    return stop_color


def get_gradient_colors(
    colors: cycle[Color], prev_stop_color: Color | None
) -> tuple[Color, Color]:
    """Return the start_color and stop_color for the next gradient cycle"""
    return prev_stop_color if prev_stop_color else next(colors), next(colors)


def get_colors(
    input_fn: str, color_count: int, quality: int, from_svg: bool = False
) -> ColorList:
    """Return the dominant color of the given image"""
    try:
        color_thief = ColorThief(input_fn)
    except PIL.UnidentifiedImageError as unidentified_image_error:
        if from_svg:
            raise

        # Maybe it's an SVG
        try:
            with tempfile.NamedTemporaryFile("wb", buffering=0) as tmp:
                tmp.write(convert_svg_to_png(input_fn))
                return get_colors(tmp.name, color_count, quality, from_svg=True)
        except ElementTree.ParseError:
            # Not a (good) SVG either. Raise the original error
            raise PIL.UnidentifiedImageError from unidentified_image_error

    palette = color_thief.get_palette(color_count, quality)

    return [Color(*rgb) for rgb in palette]


def convert_svg_to_png(svg_fn: str) -> bytes:
    """Convert the given svg filename to PNG and return the PNG bytes"""
    return cairosvg.svg2png(url=svg_fn)


@cache
def get_effect() -> Effect:
    """Return the "global" Effect instance"""
    return Effect()


def plugin(_colors: ColorList, config: ConfigType) -> asyncio.Task:
    """RGB plugin handler"""
    effect = get_effect()
    reset_task = asyncio.create_task(effect.reset(config))

    if not effect.is_alive():
        asyncio.create_task(effect.run())

    return reset_task
