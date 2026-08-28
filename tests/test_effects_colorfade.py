# pylint: disable=missing-docstring,unused-argument

import datetime as dt
from itertools import cycle
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, call, patch

from larry.color import Color
from unittest_fixtures import Fixtures, given

from larry_rgb import hardware
from larry_rgb.config import Config
from larry_rgb.effects import colorfade

from .lib import BLUE, GREEN, IMAGE_COLORS, RED, make_config, np_random_seed


@given(np_random_seed)
class EffectTestCase(IsolatedAsyncioTestCase):
    """Tests for the Effect class"""

    async def test_reset(self, fixtures: Fixtures) -> None:
        config = Config(make_config(max_palette_size="3"))
        effect = colorfade.Effect()

        with patch.object(colorfade, "cycle") as mock_cycle:
            await effect.reset(IMAGE_COLORS, config)

        self.assertIs(effect.config, config)
        self.assertEqual(effect.colors, mock_cycle.return_value)
        call_args = mock_cycle.call_args[0]
        colors = call_args[0]
        self.assertEqual(
            set(colors), {Color(156, 125, 57), Color(224, 175, 65), Color(91, 80, 35)}
        )

    async def test_reset_with_pastelize_true(self, fixtures: Fixtures) -> None:
        config = Config(make_config(max_palette_size="3", pastelize="true"))
        effect = colorfade.Effect()

        with patch.object(colorfade, "cycle") as mock_cycle:
            await effect.reset(IMAGE_COLORS, config)

        self.assertIs(effect.config, config)
        self.assertEqual(effect.colors, mock_cycle.return_value)
        call_args = mock_cycle.call_args[0]
        colors = call_args[0]
        self.assertEqual(
            set(colors),
            {Color(255, 215, 127), Color(255, 229, 127), Color(255, 215, 127)},
        )

    async def test_reset_with_timeofday_true(self, fixtures: Fixtures) -> None:
        config = Config(make_config(max_palette_size="3", timeofday="true"))
        effect = colorfade.Effect()
        now = dt.datetime(2025, 9, 7, 21, 54)

        with patch.object(colorfade, "cycle") as mock_cycle:
            with patch("larry.filters.timeofday.now", return_value=now):
                await effect.reset(IMAGE_COLORS, config)

        self.assertIs(effect.config, config)
        self.assertEqual(effect.colors, mock_cycle.return_value)
        call_args = mock_cycle.call_args[0]
        colors = call_args[0]

        self.assertEqual(
            set(colors), {Color("#2d2811"), Color("#705720"), Color("#4e3e1c")}
        )

    async def test_with_intensity_set(self, fixtures: Fixtures) -> None:
        config = Config(
            make_config(max_palette_size="3", pastelize="false", intensity="0.5")
        )
        effect = colorfade.Effect()

        with patch.object(colorfade, "cycle") as mock_cycle:
            await effect.reset(IMAGE_COLORS, config)

        call_args = mock_cycle.call_args[0]
        colors = call_args[0]
        self.assertEqual(
            set(colors), {Color(91, 74, 7), Color(224, 150, 0), Color(156, 109, 7)}
        )

    async def test_reset_with_colors(self, fixtures: Fixtures) -> None:
        config = Config(make_config(colors="#ff0000 #000000"))
        effect = colorfade.Effect()

        with patch.object(colorfade, "cycle") as mock_cycle:
            await effect.reset(IMAGE_COLORS, config)

        self.assertEqual(effect.colors, mock_cycle.return_value)
        mock_cycle.assert_called_once_with([Color("#ff0000"), Color("#000000")])

    async def test_rgb(self, fixtures: Fixtures) -> None:
        config = Config(make_config(max_palette_size="3"))
        effect = colorfade.Effect()

        with patch("larry_rgb.effects.colorfade.hw.RGB", autospec=True) as mock_rgb:
            await effect.reset(IMAGE_COLORS, config)
            rgb = effect.rgb

        self.assertIs(rgb, mock_rgb.return_value)

    async def test_start_calls_reset_with_correct_args(
        self, fixtures: Fixtures
    ) -> None:
        config = Config(make_config(colors="#ff0000 #000000"))
        effect = colorfade.Effect()

        with patch.object(
            effect, "reset", side_effect=lambda *_: setattr(effect, "config", config)
        ) as effect_reset:
            # this ensures that the loop only iterates once
            with (
                patch.object(type(effect), "rgb"),
                patch.object(
                    colorfade,
                    "set_gradient",
                    side_effect=lambda *_: setattr(effect, "running", False),
                ),
            ):
                await effect.start([], config)

        effect_reset.assert_called_with([], config)

    async def test_stop(self, fixtures: Fixtures) -> None:
        effect = colorfade.Effect()
        effect.running = True

        await effect.stop()

        self.assertIs(effect.is_alive(), False)

    def test_rgb_when_not_reset(self, fixtures: Fixtures) -> None:
        effect = colorfade.Effect()

        with self.assertRaises(RuntimeError) as error_context:
            effect.rgb  # pylint: disable=pointless-statement

        exception = error_context.exception
        self.assertEqual("Effect has not been (re)set", str(exception))


class SetGradientTests(IsolatedAsyncioTestCase):
    """Tests for the set_gradient() method"""

    async def test_with_none(self) -> None:
        mock_rgb = Mock(spec=hardware.RGB)()
        mock_rgb.devices = [Mock(), Mock(), Mock()]
        mock_sleep = AsyncMock()

        colors = cycle([RED, GREEN, BLUE])
        steps = 5
        interval = 6.0
        pause_after_fade = 20.0
        color = await colorfade.set_gradient(
            mock_rgb, colors, steps, pause_after_fade, interval, None, mock_sleep
        )

        self.assertEqual(color, GREEN)

        gradient = Color.gradient(RED, GREEN, 5)
        calls = [call(color) for color in gradient]
        self.assertEqual(mock_rgb.set_color.call_args_list, calls)

        calls = [call(10.0), call(6.0), call(6.0), call(6.0), call(10.0)]
        self.assertEqual(mock_sleep.call_args_list, calls)

        mock_sleep.reset_mock()
        color = await colorfade.set_gradient(
            mock_rgb, colors, steps, pause_after_fade, interval, color, mock_sleep
        )

        self.assertEqual(color, BLUE)
        self.assertEqual(mock_sleep.call_args_list, calls)

        mock_sleep.reset_mock()
        color = await colorfade.set_gradient(
            mock_rgb, colors, steps, pause_after_fade, interval, color, mock_sleep
        )

        self.assertEqual(color, RED)
        self.assertEqual(mock_sleep.call_args_list, calls)

    async def test_with_prev_stop_color(self) -> None:
        prev_stop_color = Color(45, 23, 212)
        mock_rgb = Mock(spec=hardware.RGB)()
        mock_rgb.devices = [Mock(), Mock(), Mock()]
        mock_sleep = AsyncMock()

        colors = cycle([RED, GREEN, BLUE])
        steps = 5
        interval = 6.0
        pause_after_fade = 20.0
        await colorfade.set_gradient(
            mock_rgb,
            colors,
            steps,
            pause_after_fade,
            interval,
            prev_stop_color,
            mock_sleep,
        )

        gradient = Color.gradient(prev_stop_color, RED, 5)
        calls = [call(color) for color in gradient]
        self.assertEqual(mock_rgb.set_color.call_args_list, calls)

        self.assertEqual(mock_sleep.call_count, 5)
        mock_sleep.assert_called_with(10.0)

    async def test_with_same_color_does_not_set_again(self) -> None:
        color = Color(45, 23, 212)
        mock_rgb = Mock(spec=hardware.RGB)()
        mock_rgb.devices = [Mock(), Mock(), Mock()]
        mock_sleep = AsyncMock()

        colors = cycle([color])
        steps = 5
        interval = 6.0
        pause_after_fade = 20.0

        await colorfade.set_gradient(
            mock_rgb, colors, steps, pause_after_fade, interval, None, mock_sleep
        )

        mock_rgb.set_color.assert_called_once_with(color)
