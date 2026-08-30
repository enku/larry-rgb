# pylint: disable=missing-docstring,unused-argument
import random as sys_random
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, patch

from unittest_fixtures import Fixtures, given

from larry_rgb.config import Config
from larry_rgb.effects import get_effect, random

from .lib import (
    IMAGE_COLORS,
    clear_cache,
    effects_entry_points,
    make_config,
    rgb_client,
)


@given(clear_cache)
class ResetTests(IsolatedAsyncioTestCase):
    async def test(self, fixtures: Fixtures) -> None:
        effect = random.Effect()
        config = Config(make_config())
        self.assertEqual(effect.actual_effect, get_effect("dummy"))

        with patch.object(effect, "stop"), patch.object(effect, "start"):
            await effect.reset([], config)

            # pylint: disable=no-member
            effect.stop.assert_called_once_with()  # type: ignore[attr-defined]
            effect.start.assert_called_once_with([], config)  # type: ignore[attr-defined]


@given(clear_cache, effects_entry_points)
class StartTests(IsolatedAsyncioTestCase):
    async def test(self, fixtures: Fixtures) -> None:
        effect = random.Effect()
        ge_path = "larry_rgb.effects.random.effects.get_effect"

        with patch(ge_path, return_value=AsyncMock()) as mock_get_effect:
            with patch("larry_rgb.effects.random.random", sys_random.Random(34)):
                await effect.start(IMAGE_COLORS, Config(make_config()))

        mock_get_effect.assert_called_once_with("gradient")

    async def test_with_exclude(self, fixtures: Fixtures) -> None:
        effect = random.Effect()
        config = {"effect": "random", "effect.random.exclude": "bogus gradient"}
        ge_path = "larry_rgb.effects.random.effects.get_effect"

        with patch(ge_path, return_value=AsyncMock()) as mock_get_effect:
            with patch("larry_rgb.effects.random.random", sys_random.Random(34)):
                await effect.start([], Config(make_config(**config)))

        mock_get_effect.assert_called_once_with("fade")


@given(clear_cache, rgb_client)
class StopTests(IsolatedAsyncioTestCase):
    async def test(self, fixtures: Fixtures) -> None:
        effect = random.Effect()

        with patch("larry_rgb.effects.random.random", sys_random.Random(34)):
            await effect.start(IMAGE_COLORS, Config(make_config()))
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
