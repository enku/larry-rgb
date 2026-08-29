"""Set the OpenRGB rbg colors to the dominant color of the image"""

import asyncio
from typing import Any

from larry import LOGGER
from larry.color import ColorList
from larry.config import ConfigType

from larry_rgb.config import Config
from larry_rgb.effects import current, get_effect

logger = LOGGER.getChild(__name__)


async def plugin(colors: ColorList, larry_config: ConfigType) -> asyncio.Task[Any]:
    """RGB plugin handler"""
    config = Config(larry_config)
    logger.debug("Getting %s Effect", config.effect)
    effect = get_effect(config.effect)

    if current_effect := current.get():
        if current_effect != effect:
            logger.debug("Stopping %s Effect", current_effect)
            await current_effect.stop()

    current.set(effect)

    func = effect.reset if effect.is_alive() else effect.start

    return asyncio.create_task(func(colors, config))
