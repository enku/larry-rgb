"""Set the OpenRGB rbg colors to the dominant color of the image"""

from typing import Protocol, TypeVar

from larry.color import ColorList
from larry.config import ConfigType

from larry_rgb.config import Config
from larry_rgb.effects import current, get_effect


class Comparable(Protocol):  # pylint: disable=too-few-public-methods
    """Something that supports <="""

    def __le__(self, other: "Comparable") -> bool: ...


async def plugin(colors: ColorList, larry_config: ConfigType) -> None:
    """RGB plugin handler"""
    config = Config(larry_config)
    effect = get_effect(config.effect.name)

    if current_effect := current.get():
        if current_effect != effect:
            await current_effect.stop()
            current.set(effect)

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
