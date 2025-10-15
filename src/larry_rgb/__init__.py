"""Set the OpenRGB rbg colors to the dominant color of the image"""

import asyncio
from configparser import ConfigParser
from functools import cache, cached_property
from itertools import cycle
from typing import Awaitable, Callable, Iterator, Protocol, TypeVar

from larry.color import Color, ColorList
from larry.config import ConfigType
from larry.filters.timeofday import cfilter as timeofday
from larry.plugins import apply_plugin_filter

from larry_rgb import colorlib
from larry_rgb import hardware as hw
from larry_rgb.config import Config


class Comparable(Protocol):  # pylint: disable=too-few-public-methods
    """Something that supports <="""

    def __le__(self, other: "Comparable") -> bool: ...


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

    async def run(self, colors: ColorList, config: Config) -> None:  # pragma: no cover
        """Run the effect"""
        await self.reset(colors, config)
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

    async def stop(self) -> None:
        """Queue the effect to stop"""
        async with self.lock:
            self.running = False

    async def reset(self, colors: ColorList, config: Config) -> None:
        """Reset the effect's color list"""
        colors = config.colors or Color.dominant(colors, config.max_palette_size)

        # Note: pastelize, timeofday and intensify below are deprecated as we now use
        # apply_plugin_filter (below). This will eventually be removed.
        if config.pastelize:
            colors = [color.pastelize() for color in colors]

        if config.timeofday:
            colors = timeofday(colors, ConfigParser())

        colors = [color.intensify(config.intensity) for color in colors]
        colors = apply_plugin_filter(colors, config.config)

        async with self.lock:
            self.colors = cycle(colors)
            self.config = config


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


@cache
def get_effect() -> Effect:
    """Return the "global" Effect instance"""
    return Effect()


async def plugin(colors: ColorList, larry_config: ConfigType) -> None:
    """RGB plugin handler"""
    effect = get_effect()
    config = Config(larry_config)
    func = effect.reset if effect.is_alive() else effect.run

    await func(colors, config)


_T = TypeVar("_T", bound=Comparable)


def ensure_range(
    value: _T, value_range: tuple[_T, _T], error: str | None = None
) -> None:
    """Raise ValueError if value is not withn the given range"""
    if not value_range[0] <= value <= value_range[1]:
        if error is None:
            error = f"Value {value!r} is out of range {value_range!r}"
        raise ValueError(error)
