"""Gradient Effect"""

import asyncio
import random
from dataclasses import dataclass
from enum import StrEnum, unique
from itertools import cycle
from typing import Self

from larry import LOGGER
from larry.color import Color, ColorList
from larry.plugins import apply_plugin_filter
from openrgb.orgb import Device  # type: ignore
from openrgb.utils import RGBColor  # type: ignore

from larry_rgb import effects
from larry_rgb.config import Config

logger = LOGGER.getChild(__name__)


@unique
class Direction(StrEnum):
    """Configured direction of the stream"""

    FORWARD = "forward"
    BACKWARD = "backward"
    RANDOM = "random"


class Effect(effects.Effect):
    """Gradient Effect"""

    def __init__(self) -> None:
        self.config: Config
        self._running = False
        self._task: asyncio.Task[None] = asyncio.create_task(asyncio.sleep(0))

    async def start(self, colors: ColorList, config: Config) -> None:
        """Just does a reset"""
        if not self._running:
            await self.reset(colors, config)

    async def reset(self, colors: ColorList, config: Config) -> None:
        """Reset the effect"""
        await self.stop()

        self.config = config
        self._running = True

        effect_config = EffectConfig.from_config(config)
        dominant_colors = Color.dominant(colors, effect_config.dominant_color_count)
        interval = effect_config.interval

        match effect_config.direction:
            case Direction.FORWARD:
                reverse = False
            case Direction.BACKWARD:
                reverse = True
            case _:
                reverse = random.choice([True, False])

        self._task = asyncio.create_task(
            self.hw_update(dominant_colors, interval, reverse)
        )
        logger.debug("started task for hw_update: %s", self._task.get_name())

    def is_alive(self) -> bool:
        """Return True if the effect is running"""
        return self._running

    async def stop(self) -> None:
        """Stop the Effect"""
        self._running = False
        await self._task

    async def hw_update(
        self, dominant_colors: ColorList, interval: float, reverse: bool
    ) -> None:
        """Update hardware, forever"""
        logger.debug(
            "hw_update() started with interval=%s, reverse=%s", interval, reverse
        )
        client = self.config.rgb.openrgb_client
        offsets = {dev: cycle(range(len(dev.colors) - 1)) for dev in client.ee_devices}

        while self._running:
            for device in client.ee_devices:
                self.color_device(
                    device, dominant_colors, next(offsets[device]), reverse=reverse
                )

            client.show()
            await asyncio.sleep(interval)

        logger.debug("hw_update() shutting down")

    def color_device(
        self, device: Device, colors: ColorList, i: int, *, reverse: bool = False
    ) -> None:
        """Set the given device's color to the given color

        If reverse=True, colors are set in their reverse order.
        """
        # stop at the start color
        colors = colors + colors[::-1][1:]

        color_count = len(device.colors)

        # Create gradient. Shave off the last color because it's the same as the start
        # color
        gradient = list(Color.gradient2(colors[:color_count], color_count + 1))[:-1]
        gradient = apply_plugin_filter(gradient, self.config.config)
        i = i % len(gradient)

        to_set = gradient[i : i + color_count]

        while len(to_set) < color_count:
            to_set = to_set + gradient[: color_count - len(to_set)]

        iterable = reversed(to_set) if reverse else to_set
        device.colors = [RGBColor(c.red, c.green, c.blue) for c in iterable]


@dataclass(kw_only=True, frozen=True)
class EffectConfig:
    """Effect-specific config for the stream effect"""

    dominant_color_count: int
    direction: Direction
    interval: float

    @classmethod
    def from_config(cls, config: Config) -> Self:
        """Convert Config.effect_config to EffectConfig"""
        effect_config = config.effect_config

        return cls(
            dominant_color_count=int(effect_config.get("dominant_color_count", "10")),
            direction=Direction(effect_config.get("direction", "forward").lower()),
            interval=float(effect_config.get("interval", "0.1")),
        )
