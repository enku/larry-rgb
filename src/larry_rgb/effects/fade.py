"""The "fade" effect"""

import asyncio
from dataclasses import dataclass
from itertools import cycle
from typing import Any, Iterator, Self

from larry import LOGGER
from larry.color import Color, ColorList
from larry.plugins import apply_plugin_filter

from larry_rgb import colorlib
from larry_rgb import hardware as hw
from larry_rgb.config import Config

logger = LOGGER.getChild(__name__)


class Effect:
    """Container for the Effect coroutine"""

    def __init__(self) -> None:
        self.running = False
        self._task: asyncio.Task[Any] = asyncio.create_task(asyncio.sleep(0))

    def is_alive(self) -> bool:
        """Return True if effect is running"""
        return self.running

    async def start(self, colors: ColorList, config: Config) -> None:
        """Start the effect"""
        await self.reset(colors, config)

    async def stop(self) -> None:
        """Queue the effect to stop"""
        self.running = False
        await self._task

    async def reset(self, colors: ColorList, config: Config) -> None:
        """Reset the effect's color list"""
        await self.stop()

        self.running = True
        self._task = asyncio.create_task(self.hw_update(config, colors))

    async def hw_update(self, config: Config, colors: ColorList) -> None:
        """Update hardware, forever"""
        stop_color = None
        effect_config = EffectConfig.from_config(config)
        colors = effect_config.colors or Color.dominant(
            colors, effect_config.max_palette_size
        )
        colors = apply_plugin_filter(colors, config.config)
        color_cycle = cycle(colors)

        while self.running:
            stop_color = await set_gradient(
                config.rgb,
                color_cycle,
                effect_config.steps,
                effect_config.pause_after_fade,
                effect_config.interval,
                stop_color,
            )
        logger.debug("Shutting down")


@dataclass(kw_only=True, frozen=True)
class EffectConfig:
    """Effect-specific config for the fade effect"""

    colors: ColorList | None
    interval: float
    max_palette_size: int
    pause_after_fade: float
    steps: int

    @classmethod
    def from_config(cls, config: Config) -> Self:
        """Convert Config.effect_config to EffectConfig"""
        effect_config = config.effect_config

        return cls(
            colors=[Color(i) for i in effect_config.get("colors", "").strip().split()]
            or None,
            interval=float(effect_config.get("interval", "0.05")),
            max_palette_size=int(effect_config.get("max_palette_size", "10")),
            pause_after_fade=float(effect_config.get("pause_after_fade", "0.0")),
            steps=int(effect_config.get("steps", "20")),
        )


async def set_gradient(
    rgb: hw.RGB,
    colors: Iterator[Color],
    steps: int,
    pause_after_fade: float,
    interval: float,
    prev_stop_color: Color | None,
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
        await asyncio.sleep(
            end_wait if color in end_colors and pause_after_fade else interval
        )
        previous_color = color

    return end_colors[1]
