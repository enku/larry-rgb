"""Larry RGB Effects

Affects are classes that follow the Effect protocol and register themselves under the
"larry_rgb.effects" entry point.
"""

from abc import ABC, abstractmethod
from functools import cache
from importlib.metadata import entry_points
from typing import Any

from larry.color import ColorList

from larry_rgb.config import Config


class Effect(ABC):
    """A larry-rgb Effect

    Effects are plugins for larry-rgb. The plugin is configured to run an effect. The
    plugin's `run()` method is responsible for instantiating, running, resetting, and
    stopping the Effect.

    When Effects are run/reset their effect-specific configuration is provided in the
    config argument as `config.effect.config`. This will be a dict[str, str] object.

    Effects register under the entry-point "larry_rgb.effects"
    """

    @abstractmethod
    def __init__(self) -> None:
        """Initializer

        Takes no arguments
        """

    @abstractmethod
    async def reset(self, colors: ColorList, config: Config) -> Any:
        """Reset the Effect

        When the Effect has already been started but the colors and/or config has
        changed then this method is called.
        """

    @abstractmethod
    def is_alive(self) -> bool:
        """Return True iff the Effect is running"""

    @abstractmethod
    async def run(self, colors: ColorList, config: Config) -> Any:
        """Start the Effect"""

    @abstractmethod
    async def stop(self) -> Any:
        """Stop the Effect"""


@cache
def get_effect(name: str) -> Effect:
    """Return the "global" Effect instance"""
    effects = entry_points().select(group="larry_rgb.effects", name=name)

    if not effects:
        raise LookupError(repr(name))

    effect: type[Effect] = tuple(effects)[0].load()

    return effect()


def list_effects() -> list[str]:
    """Return a list of the available Effects"""
    return [i.name for i in entry_points().select(group="larry_rgb.effects")]


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
