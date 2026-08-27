"""A dummy effect.

Does nothing. Use for testing
"""

# pylint: disable=missing-docstring

from larry.color import ColorList

from larry_rgb.config import Config


class Effect:
    def __init__(self) -> None:
        self.running = False

    async def reset(self, _colors: ColorList, _config: Config) -> None: ...
    def is_alive(self) -> bool:
        return self.running

    async def run(self, _colors: ColorList, _config: Config) -> None:
        self.running = True

    async def stop(self) -> None:
        self.running = False
