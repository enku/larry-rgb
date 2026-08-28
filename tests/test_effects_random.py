# pylint: disable=missing-docstring,unused-argument
import random as sys_random
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import patch

from unittest_fixtures import Fixtures, given

from larry_rgb.config import Config
from larry_rgb.effects import get_effect, random

from .lib import IMAGE_COLORS, clear_cache, effects_entry_points, make_config


@given(clear_cache)
class ResetTests(IsolatedAsyncioTestCase):
    async def test(self, fixtures: Fixtures) -> None:
        effect = random.Effect()
        config = Config(make_config())
        self.assertEqual(effect.actual_effect, get_effect("dummy"))

        with patch.object(effect, "stop"), patch.object(effect, "run"):
            await effect.reset([], config)

            # pylint: disable=no-member
            effect.stop.assert_called_once_with()  # type: ignore[attr-defined]
            effect.run.assert_called_once_with([], config)  # type: ignore[attr-defined]


@given(clear_cache, effects_entry_points)
class RunTests(IsolatedAsyncioTestCase):
    async def test(self, fixtures: Fixtures) -> None:
        effect = random.Effect()

        with patch("larry_rgb.effects.random.random", sys_random.Random(34)):
            with patch("larry_rgb.effects.gradient.hw.RGB", autospec=True):
                await effect.run(IMAGE_COLORS, Config(make_config()))

        self.assertEqual(effect.actual_effect, get_effect("gradient"))


@given(clear_cache)
class StopTests(IsolatedAsyncioTestCase):
    async def test(self, fixtures: Fixtures) -> None:
        effect = random.Effect()

        with patch("larry_rgb.effects.random.random", sys_random.Random(34)):
            with patch("larry_rgb.effects.gradient.hw.RGB", autospec=True):
                await effect.run(IMAGE_COLORS, Config(make_config()))
                self.assertEqual(effect.is_alive(), True)

        await effect.stop()
        self.assertEqual(effect.is_alive(), False)


@given(effects_entry_points)
class GetRandomEffectName(TestCase):
    def test(self, *, fixtures: Fixtures) -> None:
        with patch("larry_rgb.effects.random.random", sys_random.Random(1)):
            effect_name = random.get_random_effect_name()

        self.assertEqual(effect_name, "colorfade")

        with patch("larry_rgb.effects.random.random", sys_random.Random(34)):
            effect_name = random.get_random_effect_name()

        self.assertEqual(effect_name, "gradient")
