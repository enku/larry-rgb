# pylint: disable=missing-docstring,unused-argument
import random as sys_random
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, patch

from unittest_fixtures import Fixtures, given, where

from larry_rgb.effects import get_effect, random

from .lib import IMAGE_COLORS, clear_cache
from .lib import config as config_f
from .lib import effects_entry_points, rgb_client


@given(clear_cache, config_f)
class ResetTests(IsolatedAsyncioTestCase):
    async def test(self, fixtures: Fixtures) -> None:
        effect = random.Effect()
        self.assertEqual(effect.actual_effect, get_effect("dummy"))

        with patch.object(effect, "stop"), patch.object(effect, "start"):
            await effect.reset([], fixtures.config)

            # pylint: disable=no-member
            effect.stop.assert_called_once_with()  # type: ignore[attr-defined]
            effect.start.assert_called_once_with([], fixtures.config)  # type: ignore[attr-defined]


@given(clear_cache, effects_entry_points, config_f)
@where(config={"effect": "random", "effect.random.exclude": "bogus gradient"})
class StartTests(IsolatedAsyncioTestCase):
    async def test(self, fixtures: Fixtures) -> None:
        del fixtures.config.config["effect.random.exclude"]
        effect = random.Effect()
        ge_path = "larry_rgb.effects.random.effects.get_effect"

        with patch(ge_path, return_value=AsyncMock()) as mock_get_effect:
            with patch("larry_rgb.effects.random.random", sys_random.Random(34)):
                await effect.start(IMAGE_COLORS, fixtures.config)

        mock_get_effect.assert_called_once_with("gradient")

    async def test_with_exclude(self, fixtures: Fixtures) -> None:
        effect = random.Effect()
        ge_path = "larry_rgb.effects.random.effects.get_effect"

        with patch(ge_path, return_value=AsyncMock()) as mock_get_effect:
            with patch("larry_rgb.effects.random.random", sys_random.Random(34)):
                await effect.start([], fixtures.config)

        mock_get_effect.assert_called_once_with("fade")


@given(clear_cache, rgb_client, config_f)
class StopTests(IsolatedAsyncioTestCase):
    async def test(self, fixtures: Fixtures) -> None:
        effect = random.Effect()

        with patch("larry_rgb.effects.random.random", sys_random.Random(34)):
            await effect.start(IMAGE_COLORS, fixtures.config)
            self.assertEqual(effect.is_alive(), True)

        await effect.stop()
        self.assertEqual(effect.is_alive(), False)


@given(effects_entry_points)
class GetRandomEffectName(TestCase):
    def test(self, *, fixtures: Fixtures) -> None:
        with patch("larry_rgb.effects.random.random", sys_random.Random(1)):
            effect_name = random.get_random_effect_name()

        self.assertEqual(effect_name, "fade")

        with patch("larry_rgb.effects.random.random", sys_random.Random(34)):
            effect_name = random.get_random_effect_name()

        self.assertEqual(effect_name, "gradient")

    def test_with_exclude(self, *, fixtures: Fixtures) -> None:
        with patch("larry_rgb.effects.random.random", sys_random.Random(1)):
            effect_name = random.get_random_effect_name(exclude=["bogus", "fade"])

        self.assertEqual(effect_name, "gradient")
