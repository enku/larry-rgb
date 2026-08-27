"""LarryRGB config"""

import warnings
from types import SimpleNamespace
from typing import Any

from larry.color import Color
from larry.config import ConfigType


class EffectConfig(SimpleNamespace):  # pylint: disable=too-few-public-methods
    """Configuration for a specific Effect

    Effects can have their own configuration, set up in larry.cfg like the following:

        [larry]
        plugins = larry_rgb

        [plugins:larry_rgb]
        effect = dummy
        effect.dummy.filter = neonize
        effect.dummy.filter.neonize.brightness = 50
        effect.gradient.filter = error
        effect.dummy.filter.gradient.brightness = 100
    """


class EffectInfo:  # pylint: disable=too-few-public-methods
    """Information about an Effect

    Includes the effect's name and configuration.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.config = EffectConfig()


class Config:
    """plugin configuration getter with defaults"""

    def __init__(self, config: ConfigType):
        self.config = config

    @property
    def address(self) -> str:
        """Address of the OpenRGB server"""
        return self.config.get("address", fallback="localhost")

    @property
    def steps(self) -> int:
        """The number of steps (colors) for the color gradients"""
        return self.config.getint("gradient_steps", fallback=20)

    @property
    def interval(self) -> float:
        """Interval between each color in the gradient"""
        return self.config.getfloat("interval", fallback=0.05)

    @property
    def max_palette_size(self) -> int:
        """Maximum number of colors to acquire from the input image"""
        return self.config.getint("max_palette_size", fallback=10)

    @property
    def pause_after_fade(self) -> float:
        """Number of seconds to pause between gradients"""
        return self.config.getfloat("pause_after_fade", fallback=0.0)

    def __eq__(self, other: Any) -> bool:
        other_config = getattr(other, "config", None)

        if isinstance(other_config, ConfigType):
            return self.config == other_config

        return NotImplemented

    @property
    def pastelize(self) -> bool:
        """Whether or not to pastelize the colors acquired from the input image

        The default is False.
        """
        warnings.warn(
            "The pastelize config is deprecated in favor of plugin filters",
            DeprecationWarning,
        )
        return self.config.getboolean("pastelize", False)

    @property
    def timeofday(self) -> bool:
        """Whether or not to adjust the brightness according to the time of day.

        The default is False.
        """
        warnings.warn(
            "The timeofday config is deprecated in favor of plugin filters",
            DeprecationWarning,
        )
        return self.config.getboolean("timeofday", False)

    @property
    def colors(self) -> list[Color]:
        """colors to use instead of image-generated colors"""
        color_str = self.config.get("colors", fallback="").strip()

        return [Color(item) for item in color_str.split()]

    @property
    def intensity(self) -> float:
        """Amount of intensity to add to the colors (between -1 and 1)"""
        warnings.warn(
            "The intensity config is deprecated in favor of plugin filters",
            DeprecationWarning,
        )
        return self.config.getfloat("intensity", fallback=0.0)

    @property
    def effect(self) -> EffectInfo:
        """The RGB Effect to run"""
        info = EffectInfo(self.config.get("effect", fallback="colorfade").strip())

        prefix = f"effect.{info.name}."
        for key, value in self.config.items():
            if key.startswith(prefix):
                setattr(info.config, key.removeprefix(prefix), value)

        return info
