"""Larry RGB Effects

Affects are classes that follow the Effect protocol and register themselves under the
"larry_rgb.effects" entry point.
"""

from typing import Any, Protocol

from larry.color import ColorList

from larry_rgb.config import Config


class Effect(Protocol):
    # pylint: disable=missing-docstring
    async def reset(self, colors: ColorList, config: Config) -> Any: ...
    def is_alive(self) -> bool: ...
    async def run(self, colors: ColorList, config: Config) -> Any: ...
