# pylint: disable=missing-docstring
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, patch

from larry.color import Color
from unittest_fixtures import Fixtures, given

import larry_rgb
from larry_rgb.config import Config
from larry_rgb.effects import get_effect

from . import lib

IMAGE_COLORS = lib.IMAGE_COLORS
DOMINANT_COLOR = Color("#9c7e35")
make_config = lib.make_config


@patch("larry_rgb.effects.solid.color_all_rgbs")
@patch("larry_rgb.effects.solid.get_rgb")
class SolidEffectTests(IsolatedAsyncioTestCase):
    async def test_with_dominant(self, get_rgb: Mock, color_all_rgbs: Mock) -> None:
        # given the config to run the solid effect
        config = make_config(effect="solid")

        # when the effect is run
        task = await larry_rgb.plugin(IMAGE_COLORS, config)
        await task

        # it colors the leds the expected color
        get_rgb.assert_called_with(Config(config))
        rgb = get_rgb.return_value

        color_all_rgbs.assert_called_once_with(DOMINANT_COLOR, rgb)

    async def test_with_color_from_config(
        self, get_rgb: Mock, color_all_rgbs: Mock
    ) -> None:
        # given the config to run the solid effect, with configured color
        config = make_config(**{"effect": "solid", "effect.solid.color": "white"})

        # when the effect is run
        task = await larry_rgb.plugin([], config)
        await task

        # it colors the leds the expected color
        get_rgb.assert_called_with(Config(config))
        rgb = get_rgb.return_value

        color_all_rgbs.assert_called_once_with(Color("white"), rgb)


@given(lib.clear_cache)
class EffectIsAliveTests(IsolatedAsyncioTestCase):
    # pylint: disable=unused-argument
    def test_before_running(self, *, fixtures: Fixtures) -> None:
        effect = get_effect("solid")

        self.assertEqual(effect.is_alive(), False)

    async def test_when_run(self, *, fixtures: Fixtures) -> None:
        effect = get_effect("solid")

        with patch.object(effect, "reset"):
            await effect.start([], Config(make_config()))

        self.assertEqual(effect.is_alive(), True)

    async def test_when_stopped(self, *, fixtures: Fixtures) -> None:
        effect = get_effect("solid")

        with patch.object(effect, "reset"):
            await effect.start([], Config(make_config()))

        await effect.stop()

        self.assertEqual(effect.is_alive(), False)


@given(lib.clear_cache)
class EffectStartTests(IsolatedAsyncioTestCase):
    # SolidEffectTests already tests most of this
    # pylint: disable=unused-argument
    async def test_when_running_does_not_reset(self, *, fixtures: Fixtures) -> None:
        # given the solid effect
        effect = get_effect("solid")

        # given the config to run the solid effect
        config = make_config(effect="solid")

        with patch.object(effect, "reset") as reset:
            # when the effect is run once
            await effect.start([], Config(config))

            # and then run a second time
            await effect.start([], Config(config))

        # then the effect isn't reset
        self.assertEqual(reset.call_count, 1)
