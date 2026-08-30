"""The random Effect

It wouldn't be larry if there wasn't a random plugin. This Effect returns a random
Effect (excluding "dummy" and itself.
"""

import random
from typing import Iterable

from larry import LOGGER
from larry.color import ColorList

from larry_rgb import effects
from larry_rgb.config import Config

EXCLUDED_NAMES = {"random", "dummy"}

logger = LOGGER.getChild(__name__)


class Effect(effects.Effect):
    """The random Effect"""

    def __init__(self) -> None:
        self.running = False
        self.actual_effect: effects.Effect = effects.get_effect("dummy")

    async def reset(self, colors: ColorList, config: Config) -> None:
        """Reset the effect"""
        await self.stop()
        await self.start(colors, config)

    async def start(self, colors: ColorList, config: Config) -> None:
        """Start the Effect"""
        effect_config = config.effect_config
        exclude = effect_config.get("exclude", "").strip().split()
        effect_name = get_random_effect_name(exclude=exclude)
        logger.debug("Working on behalf of %s", effect_name)
        self.actual_effect = effects.get_effect(effect_name)

        actual_config = Config.for_effect(effect_name, config)
        await self.actual_effect.start(colors, actual_config)

    async def stop(self) -> None:
        """Stop the Effect and remove the reference"""
        await self.actual_effect.stop()
        self.actual_effect = effects.get_effect("dummy")

    def is_alive(self) -> bool:
        """Return True if the effect is running"""
        return self.actual_effect.is_alive()


def get_random_effect_name(*, exclude: Iterable[str] = ()) -> str:
    """Return a random Effect name for the available Effects

    Excludes EXCLUDED_NAMES and `excludes`
    """
    excludes = EXCLUDED_NAMES.union(exclude)

    return random.choice([e for e in effects.list_effects() if e not in excludes])
