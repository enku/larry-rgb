# pylint: disable=missing-docstring
from configparser import ConfigParser
from unittest import IsolatedAsyncioTestCase, TestCase

from larry.color import Color
from larry.config import ConfigType
from unittest_fixtures import Fixtures, given

from larry_rgb import plugin
from larry_rgb.config import Config
from larry_rgb.effects import get_effect

from .lib import clear_cache


def make_config(**kwargs: str) -> Config:
    parser = ConfigParser()
    parser.add_section("rgb")
    config = ConfigType(parser, "rgb")

    for name, value in kwargs.items():
        config[name] = value

    return Config(config)


class ConfigTestCase(TestCase):
    def test_colors(self) -> None:
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

    def test_for_effect(self) -> None:
        orig_config = make_config(
            **{
                "effect": "random",
                "effect.random.filter": "foo",
                "effect.gradient.filter": "bar",
                "effect.colorfade.filter": "baz",
            }
        )

        self.assertEqual(orig_config.effect.name, "random")
        self.assertEqual(orig_config.effect.config["filter"], "foo")

        new_config = Config.for_effect("gradient", orig_config)

        self.assertEqual(new_config.effect.name, "gradient")
        self.assertEqual(new_config.effect.config["filter"], "bar")


@given(clear_cache)
class EffectSpecificConfigTests(IsolatedAsyncioTestCase):
    larry_config = ConfigParser()
    larry_config.read_string("""
[larry]
plugins = larry_rgb

[plugins:larry_rgb]
effect = dummy
effect.dummy.filter = neonize
effect.gradient.filter = error
""")
    plugin_config = larry_config["plugins:larry_rgb"]

    # pylint: disable=unused-argument
    async def test(self, fixtures: Fixtures) -> None:
        task = await plugin([], self.plugin_config)
        await task

        effect = get_effect("dummy")
        config = effect.config  # type: ignore[attr-defined]

        self.assertEqual(config.effect.name, "dummy")
        self.assertEqual(config.effect.config["filter"], "neonize")
