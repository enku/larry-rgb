"""Set the OpenRGB rbg colors to the dominant color of the image"""

from functools import cache
from importlib.metadata import entry_points
from typing import Any, Protocol, TypeVar

from larry.color import ColorList
from larry.config import ConfigType

from larry_rgb.config import Config


class Comparable(Protocol):  # pylint: disable=too-few-public-methods
    """Something that supports <="""

    def __le__(self, other: "Comparable") -> bool: ...


class Effect(Protocol):
    # pylint: disable=missing-docstring
    async def reset(self, colors: ColorList, config: Config) -> Any: ...
    def is_alive(self) -> bool: ...
    async def run(self, colors: ColorList, config: Config) -> Any: ...


@cache
def get_effect(name: str) -> Effect:
    """Return the "global" Effect instance"""
    effects = entry_points().select(group="larry_rgb.effects", name=name)

    if not effects:
        raise LookupError(name)

    effect: type[Effect] = tuple(effects)[0].load()

    return effect()


async def plugin(colors: ColorList, larry_config: ConfigType) -> None:
    """RGB plugin handler"""
    config = Config(larry_config)
    effect = get_effect(config.effect)
    func = effect.reset if effect.is_alive() else effect.run

    await func(colors, config)


_T = TypeVar("_T", bound=Comparable)


def ensure_range(
    value: _T, value_range: tuple[_T, _T], error: str | None = None
) -> None:
    """Raise ValueError if value is not withn the given range"""
    if not value_range[0] <= value <= value_range[1]:
        if error is None:
            error = f"Value {value!r} is out of range {value_range!r}"
        raise ValueError(error)
