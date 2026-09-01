# pylint: disable=missing-docstring,unused-argument
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import patch

from unittest_fixtures import Fixtures, given, where

from larry_rgb.config import Config
from larry_rgb.effects import Effect, get_effect, list_effects

from .lib import IMAGE_COLORS, clear_cache
from .lib import config as config_f
from .lib import effects_entry_points, rgb_client


@given(clear_cache)
class GetEffectTests(TestCase):
    def test_get_effect_when_effect_not_exists(self, *, fixtures: Fixtures) -> None:
        with patch("larry_rgb.effects.dummy.Effect", autospec=True) as mock_effect_cls:
            get_effect("dummy")

        mock_effect_cls.assert_called_once_with()

    def test_get_effect_when_effect_does_exist(self, *, fixtures: Fixtures) -> None:
        effect = get_effect("dummy")
        with patch("larry_rgb.effects.dummy.Effect", autospec=True) as mock_effect_cls:
            original_effect = get_effect("dummy")
            mock_effect_cls.reset_mock()
            effect = get_effect("dummy")

        self.assertIs(effect, original_effect)
        mock_effect_cls.assert_not_called()

    def test_nonexistent_effect(self, *, fixtures: Fixtures) -> None:
        with self.assertRaises(LookupError) as context:
            get_effect("bogus")

        self.assertEqual(str(context.exception), "'bogus'")


@given(effects_entry_points)
@where(effects_entry_points__names=["foo", "bar", "baz", "random", "dummy", "candy"])
class TestListEffects(TestCase):
    def test(self, *, fixtures: Fixtures) -> None:
        names = list_effects()

        self.assertEqual(names, ["foo", "bar", "baz", "random", "dummy", "candy"])


@given(config_f, rgb_client)
class AllEffectsTests(IsolatedAsyncioTestCase):
    async def test(self, *, fixtures: Fixtures) -> None:
        for effect_name in list_effects():
            with self.subTest(effect=effect_name):
                await self.assert_good_effect(effect_name, fixtures.config)

    async def assert_good_effect(self, effect_name: str, config: Config) -> None:
        get_effect.cache_clear()

        # we should be able to instantiate with no args
        effect = get_effect(effect_name)

        # it should be an instance of Effect
        self.assertIsInstance(effect, Effect)

        # it should start out not running
        self.assertEqual(effect.is_alive(), False)

        # we should be able to start it with colors and config
        await effect.start(IMAGE_COLORS, config)
        self.assertEqual(effect.is_alive(), True)

        # we should be able to reset it with colors and config
        await effect.reset(IMAGE_COLORS, config)
        self.assertEqual(effect.is_alive(), True)

        # we should be able to kill it
        await effect.stop()
        self.assertEqual(effect.is_alive(), False)
