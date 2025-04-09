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

    def test_steps(self) -> None:
        config = make_config(gradient_steps="30")

        self.assertEqual(30, config.steps)

    def test_interval(self) -> None:
        config = make_config(interval="0.4")

        self.assertEqual(0.4, config.interval)

    def test_pause_after_fade(self) -> None:
        config = make_config(pause_after_fade="0.4")

        self.assertEqual(0.4, config.pause_after_fade)

    def test_equality_of_different_type(self) -> None:
        config = make_config()

        self.assertFalse(6 == config)
