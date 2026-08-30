# pylint: disable=missing-docstring
from configparser import ConfigParser
from unittest import IsolatedAsyncioTestCase, TestCase, mock

from unittest_fixtures import Fixtures, given, where

from larry_rgb import hardware, plugin
from larry_rgb.config import Config
from larry_rgb.effects import get_effect

from .lib import clear_cache
from .lib import config as config_f


@given(config_f)
@where(
    config={
        "address": "host.invalid:6789",
        "effect": "random",
        "effect.random.filter": "foo",
        "effect.gradient.filter": "bar",
        "effect.fade.filter": "baz",
    }
)
class ConfigTestCase(TestCase):
    def test_equality_of_different_type(self, *, fixtures: Fixtures) -> None:
        self.assertFalse(6 == fixtures.config)

    def test_for_effect(self, *, fixtures: Fixtures) -> None:
        orig_config = fixtures.config
        self.assertEqual(orig_config.effect, "random")
        self.assertEqual(orig_config.effect_config["filter"], "foo")

        new_config = Config.for_effect("gradient", orig_config)

        self.assertEqual(new_config.effect, "gradient")
        self.assertEqual(new_config.effect_config["filter"], "bar")

    def test_rgb_property(self, *, fixtures: Fixtures) -> None:
        with mock.patch("larry_rgb.config.hardware.OpenRGBClient"):
            self.assertIsInstance(fixtures.config.rgb, hardware.RGB)


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

        self.assertEqual(config.effect, "dummy")
        self.assertEqual(config.effect_config["filter"], "neonize")
