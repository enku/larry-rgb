"""Solid color Effect"""

import asyncio
import logging

from larry.color import Color, ColorList
from larry.plugins import apply_plugin_filter

from larry_rgb import effects
from larry_rgb import hardware as hw
from larry_rgb.config import Config

logger = logging.getLogger(__package__)


class Effect(effects.Effect):
    """Solid color Effect"""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._running = False

    def is_alive(self) -> bool:
        """Return True if the Effect is running"""
        return self._running

    async def start(self, colors: ColorList, config: Config) -> None:
        """Start the effect"""
        logger.debug("Running solid Effect")

        if self.is_alive():
            logger.debug("Effect is already running")
            return

        async with self._lock:
            self._running = True

        await self.reset(colors, config)

    async def reset(self, colors: ColorList, config: Config) -> None:
        """Reset the effect"""
        logger.debug("Resetting solid Effect")

        effect_config = config.effect_config
        logger.debug("config: %s", f"{effect_config=}")

        if color_name := effect_config.get("color", "").strip():
            color = Color(color_name)
        else:
            color = Color.dominant(colors, 1)[0]

        [color] = apply_plugin_filter([color], config.config)
        logger.debug("color: %s", color)
        color_all_rgbs(color, get_rgb(config))

    async def stop(self) -> None:
        """Stop the Effect"""
        async with self._lock:
            self._running = False


def color_all_rgbs(color: Color, rgb: hw.RGB) -> None:
    """Set all rgbs to the given color"""
    logger.debug("Setting all LEDs color to %s", color)
    rgb.set_color(color)


def get_rgb(config: Config) -> hw.RGB:
    """Return an RGB instance given the config"""
    address_and_port = config.address
    address, _, port_str = address_and_port.partition(":")
    port = int(port_str) if port_str else 6742

    return hw.RGB(address=address, port=port)
