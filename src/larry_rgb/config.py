"""LarryRGB config"""
import os.path

from larry import Color
from larry.config import ConfigType


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
    def input(self) -> str:
        """Input image file path"""
        return os.path.expanduser(self.config["input"])

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

    @property
    def quality(self) -> int:
        """Quality of image primary color calculation (higher is better)"""
        return self.config.getint("quality", fallback=10)

    def __eq__(self, other) -> bool:
        other_configtype = getattr(other, "config", None)

        if isinstance(other_configtype, ConfigType):
            return self.config == other.config

        return NotImplemented

    @property
    def pastelize(self) -> bool:
        """Whether or not to pastelize the colors acquired from the input image

        The default is False.
        """
        return self.config.getboolean("pastelize", False)

    @property
    def colors(self) -> list[Color]:
        """colors to use instead of image-generated colors"""
        color_str = self.config.get("colors", fallback="").strip()

        return [Color(item) for item in color_str.split()]

    @property
    def intensity(self) -> float:
        """Amount of intensity to add to the colors (between -1 and 1)"""
        return self.config.getfloat("intensity", fallback=0.0)
