"""Gradient Effect"""

import asyncio
import math
import random
from dataclasses import dataclass
from enum import StrEnum, unique
from itertools import cycle
from typing import Callable, Self

from larry import LOGGER
from larry.color import Color, ColorList
from larry.plugins import apply_plugin_filter
from openrgb.orgb import Device  # type: ignore
from openrgb.utils import RGBColor  # type: ignore

from larry_rgb import effects
from larry_rgb.config import Config

type Transform = Callable[[Color, int, int], Color]
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
        transform = effect_config.transform
        if transform == "random":
            transform = random.choice(list(TRANSFORMS))

        match effect_config.direction:
            case Direction.FORWARD:
                reverse = False
            case Direction.BACKWARD:
                reverse = True
            case _:
                reverse = random.choice([True, False])

        self._task = asyncio.create_task(
            self.hw_update(dominant_colors, interval, reverse, transform)
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
        self, dominant_colors: ColorList, interval: float, reverse: bool, transform: str
    ) -> None:
        """Update hardware, forever"""
        logger.debug(
            "hw_update() started with interval=%s, reverse=%s, transform=%s",
            interval,
            reverse,
            transform,
        )
        client = self.config.rgb.openrgb_client
        offsets = {dev: cycle(range(len(dev.colors) - 1)) for dev in client.ee_devices}

        while self._running:
            for device in client.ee_devices:
                self.color_device(
                    device,
                    dominant_colors,
                    next(offsets[device]),
                    reverse=reverse,
                    transform=transform,
                )

            client.show()
            await asyncio.sleep(interval)

        logger.debug("hw_update() shutting down")

    def color_device(
        self,
        device: Device,
        colors: ColorList,
        i: int,
        *,
        transform: str,
        reverse: bool = False,
    ) -> None:
        """Set the given device's color to the given color

        If reverse=True, colors are set in their reverse order.
        """
        # stop at the start color
        colors = colors + [colors[0]]

        color_count = len(device.colors)

        # Create gradient. Shave off the last color because it's the same as the start
        # color
        gradient = list(Color.gradient2(colors[:color_count], color_count + 1))[:-1]
        gradient = apply_plugin_filter(gradient, self.config.config)
        i = i % len(gradient)

        to_set = gradient[i : i + color_count]

        while len(to_set) < color_count:
            to_set = to_set + gradient[: color_count - len(to_set)]

        xform = TRANSFORMS[transform]
        to_set = [
            xform(c, i, color_count) for c in (reversed(to_set) if reverse else to_set)
        ]
        device.colors = [RGBColor(c.red, c.green, c.blue) for c in to_set]


## Transforms are a way to further tweak the LED color based on the i value passed to
## color_device and the number of LEDs on the device


def transform_fade(color: Color, i: int, total: int) -> Color:
    """Fade the color

    The fade amount is a factor of the iterator value's distance from the total number
    of LEDs.
    """
    return color * logarithmic_curve(i, total)


def transform_none(color: Color, _i: int, _total: int) -> Color:
    """A no-op transform"""
    return color


def transform_twinkle(color: Color, _i: int, _total: int) -> Color:
    """Darken the color by a random amount"""
    return color * random.random()


def logarithmic_curve(i: int, n: int) -> float:
    """Return a float for a given integer i (0 <= i < n) based on n.

    Starts at 1 at i=0, drops logarithmically to 0 by i=n/2, and rises
    logarithmically back up to 1 as i approaches n-1.
    """
    if n <= 1:
        raise ValueError("n must be greater than 1")
    if not 0 <= i < n:
        raise ValueError("i must be between 0 and n-1")

    mid = n / 2.0

    if i <= mid:
        if mid <= 0:
            return 1.0
        numerator = math.log(mid - i + 1)
        denominator = math.log(mid + 1)

        if denominator == 0:
            return 0.0 if i > 0 else 1.0

        return max(0.0, min(1.0, numerator / denominator))

    span = (n - 1) - mid
    if span <= 0:
        return 1.0
    d = i - mid
    numerator = math.log(d + 1)
    denominator = math.log(span + 1)

    if denominator == 0:
        return 1.0

    return max(0.0, min(1.0, numerator / denominator))


TRANSFORMS: dict[str, Transform] = {
    "fade": transform_fade,
    "none": transform_none,
    "twinkle": transform_twinkle,
}


@dataclass(kw_only=True, frozen=True)
class EffectConfig:
    """Effect-specific config for the stream effect"""

    direction: Direction
    dominant_color_count: int
    interval: float
    transform: str

    @classmethod
    def from_config(cls, config: Config) -> Self:
        """Convert Config.effect_config to EffectConfig"""
        effect_config = config.effect_config

        return cls(
            dominant_color_count=int(effect_config.get("dominant_color_count", "10")),
            direction=Direction(effect_config.get("direction", "forward").lower()),
            interval=float(effect_config.get("interval", "0.1")),
            transform=effect_config.get("transform", "none").lower(),
        )
