# pylint: disable=missing-docstring
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, patch

from larry.color import Color
from unittest_fixtures import Fixtures, given, where

import larry_rgb
from larry_rgb.effects import get_effect

from . import lib

IMAGE_COLORS = lib.IMAGE_COLORS
DOMINANT_COLOR = Color("#9c7e35")


@given(lib.rgb_client, lib.config)
@where(config={"effect": "solid", "effect.solid.color": "white"})
@patch("larry_rgb.effects.solid.color_all_rgbs")
class SolidEffectTests(IsolatedAsyncioTestCase):
    async def test_with_dominant(
        self, color_all_rgbs: Mock, *, fixtures: Fixtures
    ) -> None:
        del fixtures.config.config["effect.solid.color"]

        # when the effect is run
        task = await larry_rgb.plugin(IMAGE_COLORS, fixtures.config.config)
        await task

        color_all_rgbs.assert_called_once_with(DOMINANT_COLOR, fixtures.config.rgb)

    async def test_with_color_from_config(
        self, color_all_rgbs: Mock, *, fixtures: Fixtures
    ) -> None:
        # when the effect is run
        task = await larry_rgb.plugin([], fixtures.config.config)
        await task

        color_all_rgbs.assert_called_once_with(Color("white"), fixtures.config.rgb)


@given(lib.clear_cache, lib.config)
class EffectIsAliveTests(IsolatedAsyncioTestCase):
    # pylint: disable=unused-argument
    def test_before_running(self, *, fixtures: Fixtures) -> None:
        effect = get_effect("solid")

        self.assertEqual(effect.is_alive(), False)

    async def test_when_run(self, *, fixtures: Fixtures) -> None:
        effect = get_effect("solid")

        with patch.object(effect, "reset"):
            await effect.start([], fixtures.config)

        self.assertEqual(effect.is_alive(), True)

    async def test_when_stopped(self, *, fixtures: Fixtures) -> None:
        effect = get_effect("solid")

        with patch.object(effect, "reset"):
            await effect.start([], fixtures.config)

        await effect.stop()

        self.assertEqual(effect.is_alive(), False)


@given(lib.clear_cache, lib.config)
@where(config={"effect": "solid"})
class EffectStartTests(IsolatedAsyncioTestCase):
    # SolidEffectTests already tests most of this
    async def test_when_running_does_not_reset(self, *, fixtures: Fixtures) -> None:
        # given the solid effect
        effect = get_effect("solid")

        with patch.object(effect, "reset") as reset:
            # when the effect is run once
            await effect.start([], fixtures.config)

            # and then run a second time
            await effect.start([], fixtures.config)

        # then the effect isn't reset
        self.assertEqual(reset.call_count, 1)
