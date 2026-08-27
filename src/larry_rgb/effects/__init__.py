"""Larry RGB Effects

Affects are classes that follow the Effect protocol and register themselves under the
"larry_rgb.effects" entry point.
"""

from functools import cache
from importlib.metadata import entry_points
from typing import Any, Protocol

from larry.color import ColorList

from larry_rgb.config import Config


class Effect(Protocol):
    # pylint: disable=missing-docstring
    async def reset(self, colors: ColorList, config: Config) -> Any: ...
    def is_alive(self) -> bool: ...
    async def run(self, colors: ColorList, config: Config) -> Any: ...
    async def stop(self) -> Any: ...


@cache
def get_effect(name: str) -> Effect:
    """Return the "global" Effect instance"""
    effects = entry_points().select(group="larry_rgb.effects", name=name)

    if not effects:
        raise LookupError(name)

    effect: type[Effect] = tuple(effects)[0].load()

    return effect()


class _Current:
    """State of the currently running Effect"""

    def __init__(self) -> None:
        self.effect: Effect | None = None

    def set(self, effect: Effect | None) -> None:
        """Set the current effect to the one given"""
        self.effect = effect

    def get(self) -> Effect | None:
        """Return the current effect"""
        return self.effect


current = _Current()
