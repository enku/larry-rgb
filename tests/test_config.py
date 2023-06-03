# pylint: disable=missing-docstring
from configparser import ConfigParser
from unittest import TestCase

from larry_rgb import Color
from larry_rgb.config import Config, ConfigType


def make_config(**kwargs: str) -> Config:
    parser = ConfigParser()
    parser.add_section("rgb")
    config = ConfigType(parser, "rgb")

    for name, value in kwargs.items():
        config[name] = value

    return Config(config)


class ConfigTestCase(TestCase):
    def test_colors(self):
        colors_str = "#ff0000 #000000"
        config = make_config(colors=colors_str)

        self.assertEqual(config.colors, [Color("#ff0000"), Color("#000000")])
