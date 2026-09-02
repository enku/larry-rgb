"""A dummy effect.

Does nothing. Use for testing
"""

# pylint: disable=missing-docstring

from larry.color import ColorList

from larry_rgb import effects
from larry_rgb.config import Config


class Effect(effects.Effect):
    def __init__(self) -> None:
        self.running = False

    async def reset(self, colors: ColorList, config: Config) -> None:
        pass

    def is_alive(self) -> bool:
        return self.running

    async def start(self, colors: ColorList, config: Config) -> None:
        self.running = True

    async def stop(self) -> None:
        self.running = False
