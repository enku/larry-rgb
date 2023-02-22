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
from larry import Color, ColorList
from larry.config import ConfigType

from larry_rgb import colorlib
from larry_rgb import hardware as hw


@dataclass
class RGB:
    """Config for OpenRGB"""

    address: str = "127.0.0.1"
    port: int = hw.OPENRGB_PORT

    def __post_init__(self) -> None:
        self.openrgb = hw.make_client(self.address, self.port)

    def set_color(self, color: Color) -> None:
        """Send the given color to openrgb"""
        hw.color_all_devices(self.openrgb, color)


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
            self.colors = cycle(colorlib.get_colors(input_fn, color_count, quality))
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
    end_colors = colorlib.get_gradient_colors(colors, prev_stop_color)
    end_wait = pause_after_fade / 2

    for color in Color.gradient(*end_colors, steps):
        rgb.set_color(color)
        await sleep(end_wait if color in end_colors and pause_after_fade else interval)

    return end_colors[1]


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
