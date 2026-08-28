"""Set the OpenRGB rbg colors to the dominant color of the image"""

import asyncio
from typing import Any

from larry.color import ColorList
from larry.config import ConfigType

from larry_rgb.config import Config
from larry_rgb.effects import current, get_effect


async def plugin(colors: ColorList, larry_config: ConfigType) -> asyncio.Task[Any]:
    """RGB plugin handler"""
    config = Config(larry_config)
    effect = get_effect(config.effect.name)

    if current_effect := current.get():
        if current_effect != effect:
            await current_effect.stop()

    current.set(effect)

    func = effect.reset if effect.is_alive() else effect.run

    return asyncio.create_task(func(colors, config))
