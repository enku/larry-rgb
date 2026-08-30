"""LarryRGB config"""

import re
from copy import copy
from functools import cached_property
from typing import Any, Self

from larry.config import ConfigType

from larry_rgb import hardware


class Config:
    """plugin configuration getter with defaults"""

    def __init__(self, config: ConfigType):
        self.config = config

    @classmethod
    def for_effect(cls, effect_name: str, config: Config) -> Self:
        """Use the given Config to create a Config for the given effect"""
        larry_config = copy(config.config)
        larry_config["effect"] = effect_name

        return cls(larry_config)

    @property
    def address(self) -> str:
        """Address of the OpenRGB server"""
        return self.config.get("address", fallback="localhost")

    @cached_property
    def rgb(self) -> hardware.RGB:
        """Returns the RGB instance.

        A (cached) property so we only instantiate it once, lazily
        """
        address_and_port = self.address
        address, _, port_str = address_and_port.partition(":")
        port = int(port_str) if port_str else 6742

        return hardware.RGB(address=address, port=port)

    def __eq__(self, other: Any) -> bool:
        other_config = getattr(other, "config", None)

        if isinstance(other_config, ConfigType):
            return self.config == other_config

        return NotImplemented

    @property
    def effect(self) -> str:
        """The RGB Effect to run"""
        return self.config.get("effect", fallback="fade").strip()

    @property
    def effect_config(self) -> dict[str, str]:
        """The config for the configured effect"""
        return self.effect_configs.get(self.effect, {})

    @property
    def effect_configs(self) -> dict[str, dict[str, str]]:
        """Return a dict of effect configs for all configured effects"""
        config: dict[str, dict[str, str]] = {}

        for key, value in self.config.items():
            if match := re.match(r"effect\.(?P<effect>.*?)\.(?P<setting>.*)", key):
                config.setdefault(match.group("effect"), {})[
                    match.group("setting")
                ] = value

        return config
