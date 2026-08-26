"""Set the OpenRGB rbg colors to the dominant color of the image"""

from functools import cache
from typing import Any, Protocol, TypeVar

from larry.color import ColorList
from larry.config import ConfigType

from larry_rgb.config import Config
from larry_rgb.effects import colorfade


class Comparable(Protocol):  # pylint: disable=too-few-public-methods
    """Something that supports <="""

    def __le__(self, other: "Comparable") -> bool: ...


class Effect(Protocol):
    # pylint: disable=missing-docstring
    async def reset(self, colors: ColorList, config: Config) -> Any: ...
    def is_alive(self) -> bool: ...
    async def run(self, colors: ColorList, config: Config) -> Any: ...


@cache
def get_effect() -> Effect:
    """Return the "global" Effect instance"""

    return colorfade.Effect()


async def plugin(colors: ColorList, larry_config: ConfigType) -> None:
    """RGB plugin handler"""
    effect = get_effect()
    func = effect.reset if effect.is_alive() else effect.run

    await func(colors, Config(larry_config))


_T = TypeVar("_T", bound=Comparable)


def ensure_range(
    value: _T, value_range: tuple[_T, _T], error: str | None = None
) -> None:
    """Raise ValueError if value is not withn the given range"""
    if not value_range[0] <= value <= value_range[1]:
        if error is None:
            error = f"Value {value!r} is out of range {value_range!r}"
        raise ValueError(error)
