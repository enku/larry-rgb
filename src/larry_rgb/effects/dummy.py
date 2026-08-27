"""A dummy effect.

Does nothing. Use for testing
"""

# pylint: disable=missing-docstring

from larry.color import ColorList

from larry_rgb.config import Config


class Effect:
    def __init__(self) -> None:
        self.config: Config
        self.colors: ColorList
        self.running = False

    async def reset(self, colors: ColorList, config: Config) -> None:
        self.colors = colors
        self.config = config

    def is_alive(self) -> bool:
        return self.running

    async def run(self, colors: ColorList, config: Config) -> None:
        self.colors = colors
        self.config = config

        self.running = True

    async def stop(self) -> None:
        self.running = False
