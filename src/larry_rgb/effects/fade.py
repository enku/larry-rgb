"""The "fade" effect"""

import asyncio
from functools import cached_property
from itertools import cycle
from typing import Awaitable, Callable, Iterator

from larry.color import Color, ColorList
from larry.plugins import apply_plugin_filter

from larry_rgb import colorlib
from larry_rgb import hardware as hw
from larry_rgb.config import Config


class Effect:
    """Container for the Effect coroutine"""

    def __init__(self) -> None:
        self.config: Config
        self.lock = asyncio.Lock()
        self.colors: Iterator[Color] = cycle([])
        self.running = False

    def is_alive(self) -> bool:
        """Return True if effect is running"""
        return self.running

    @cached_property
    def rgb(self) -> hw.RGB:
        """Returns the RGB instance.

        A (cached) property so we only instantiate it once, lazily
        """
        if not hasattr(self, "config"):
            raise RuntimeError("Effect has not been (re)set")

        address_and_port = self.config.address
        address, _, port_str = address_and_port.partition(":")
        port = int(port_str) if port_str else 6742

        return hw.RGB(address=address, port=port)

    async def start(self, colors: ColorList, config: Config) -> None:
        """Start the effect"""
        await self.reset(colors, config)
        stop_color = None

        async with self.lock:
            self.running = True

        while self.running:
            async with self.lock:
                stop_color = await set_gradient(
                    self.rgb,
                    self.colors,
                    int(self.conf("steps", "20")),
                    float(self.conf("pause_after_fade", "0.0")),
                    float(self.conf("interval", "0.05")),
                    stop_color,
                )
        self.running = False

    async def stop(self) -> None:
        """Queue the effect to stop"""
        async with self.lock:
            self.running = False

    async def reset(self, colors: ColorList, config: Config) -> None:
        """Reset the effect's color list"""
        async with self.lock:
            self.config = config

            colors = [
                Color(i) for i in self.conf("colors", "").strip().split()
            ] or Color.dominant(colors, int(self.conf("max_palette_size", "10")))
            colors = apply_plugin_filter(colors, config.config)

            self.colors = cycle(colors)

    def conf(self, key: str, default: str | None = None) -> str:
        """Return the Effect config with the given name

        If default is provided and is not None, it will be returned when no config for
        the given name exists.
        """
        try:
            return self.config.effect_config[key]
        except KeyError:
            if default is not None:
                return default
            raise


async def set_gradient(
    rgb: hw.RGB,
    colors: Iterator[Color],
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

    previous_color = None
    for color in Color.gradient(*end_colors, steps):
        if color != previous_color:
            rgb.set_color(color)
        await sleep(end_wait if color in end_colors and pause_after_fade else interval)
        previous_color = color

    return end_colors[1]
