"""Set the OpenRGB rbg colors to the dominant color of the image"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import cache, cached_property
from itertools import cycle
from typing import Awaitable, Callable

from larry import Color, ColorList
from larry.config import ConfigType

from larry_rgb import colorlib
from larry_rgb import hardware as hw
from larry_rgb.config import Config


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
    """Container for the Effect coroutine"""

    def __init__(self) -> None:
        self.config: Config
        self.lock = asyncio.Lock()
        self.colors: cycle[Color] = cycle([])
        self.running = False

    def is_alive(self) -> bool:
        """Return True if effect is running"""
        return self.running

    @cached_property
    def rgb(self) -> RGB:
        """Returns the RGB instance.

        A (cached) property so we only instantiate it once, lazily
        """
        if not hasattr(self, "config"):
            raise RuntimeError("Effect has not been (re)set")

        address_and_port = self.config.address
        address, _, port_str = address_and_port.partition(":")
        port = int(port_str) if port_str else 6742

        return RGB(address=address, port=port)

    async def run(self, config: Config) -> None:  # pragma: no cover
        """Run the effect"""
        await self.reset(config)
        stop_color = None

        async with self.lock:
            self.running = True

        while self.running:
            async with self.lock:
                stop_color = await set_gradient(
                    self.rgb,
                    self.colors,
                    self.config.steps,
                    self.config.pause_after_fade,
                    self.config.interval,
                    stop_color,
                )
        self.running = False

    async def stop(self):
        """Queue the effect to stop"""
        async with self.lock:
            self.running = False

    async def reset(self, config: Config) -> None:
        """Reset the effect's color list"""
        async with self.lock:
            self.colors = cycle(
                colorlib.get_colors(
                    config.input, config.max_palette_size, config.quality
                )
            )
            self.config = config


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


def plugin(_colors: ColorList, larry_config: ConfigType) -> asyncio.Task:
    """RGB plugin handler"""
    effect = get_effect()
    config = Config(larry_config)

    if not effect.is_alive():
        task = asyncio.create_task(effect.run(config))
    else:
        task = asyncio.create_task(effect.reset(config))

    return task
