# pylint: disable=missing-docstring,unused-argument,protected-access

import asyncio
from itertools import cycle
from typing import Any
from unittest import IsolatedAsyncioTestCase
from unittest.mock import ANY, AsyncMock, Mock, call, patch

from larry.color import Color
from unittest_fixtures import Fixtures, given

from larry_rgb import hardware
from larry_rgb.config import Config
from larry_rgb.effects import fade

from .lib import BLUE, GREEN, RED, make_config, np_random_seed


@given(np_random_seed)
class EffectTestCase(IsolatedAsyncioTestCase):
    """Tests for the Effect class"""

    async def test_reset(self, fixtures: Fixtures) -> None:
        config = Config(
            make_config(
                **{"address": "host.invalid:1234", "effect.fade.max_palette_size": "3"}
            )
        )
        effect = fade.Effect()

        orig_task = effect._task
        self.assertEqual(orig_task.done(), False)

        with patch.object(effect, "hw_update") as hw_update:
            with patch.object(effect, "stop", wraps=effect.stop) as stop:
                await effect.reset([], config)

        hw_update.assert_called_once_with(config, [])
        stop.assert_called_once_with()
        self.assertEqual(orig_task.done(), True)

    async def test_hw_update(self, fixtures: Fixtures) -> None:
        config = Config(
            make_config(
                **{"address": "host.invalid:1234", "effect.fade.max_palette_size": "3"}
            )
        )
        effect = fade.Effect()
        effect.running = True

        with patch.object(fade, "set_gradient") as set_gradient:
            # stop the loop at first iteration
            set_gradient.side_effect = lambda *_: setattr(effect, "running", False)

            with patch.object(effect, "rgb") as rgb:
                await effect.hw_update(config, [RED, GREEN, BLUE])

        set_gradient.assert_called_once_with(rgb.return_value, ANY, 20, 0.0, 0.05, None)
        rgb.assert_called_once_with("host.invalid:1234")

    async def test_hw_update2(self, fixtures: Fixtures) -> None:
        config = Config(
            make_config(
                **{"address": "host.invalid:1234", "effect.fade.max_palette_size": "3"}
            )
        )
        effect = fade.Effect()
        effect.running = True
        call_count = 0

        # side effect to run set_gradient twice
        def side_effect(*_: Any) -> Color:
            nonlocal call_count

            call_count += 1

            if call_count == 2:
                effect.running = False

            return Color(call_count * 10, call_count * 10, call_count * 10)

        with patch.object(fade, "set_gradient") as set_gradient:
            set_gradient.side_effect = side_effect

            with patch.object(effect, "rgb") as rgb:
                await effect.hw_update(config, [RED, GREEN, BLUE])

        self.assertEqual(call_count, 2)
        self.assertEqual(set_gradient.call_count, 2)
        set_gradient.assert_called_with(
            rgb.return_value, ANY, 20, 0.0, 0.05, Color(10, 10, 10)
        )

    async def test_rgb(self, fixtures: Fixtures) -> None:
        effect = fade.Effect()
        config = Config(make_config(address="host.invalid:4444"))

        with patch("larry_rgb.effects.fade.hw.RGB", autospec=True) as mock_rgb:
            rgb = effect.rgb(config.address)

        self.assertIs(rgb, mock_rgb.return_value)

    async def test_start_calls_reset_with_correct_args(
        self, fixtures: Fixtures
    ) -> None:
        config = Config(make_config(colors="#ff0000 #000000"))
        effect = fade.Effect()

        with (
            patch.object(effect, "hw_update"),
            patch.object(effect, "reset") as effect_reset,
        ):
            await effect.start([], config)
            await effect._task  # pylint: disable=protected-access

        effect_reset.assert_called_with([], config)

    async def test_stop(self, fixtures: Fixtures) -> None:
        effect = fade.Effect()
        effect.running = True

        await effect.stop()

        self.assertIs(effect.is_alive(), False)


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

        with patch.object(asyncio, "sleep") as mock_sleep:
            color = await fade.set_gradient(
                mock_rgb, colors, steps, pause_after_fade, interval, None
            )

        self.assertEqual(color, GREEN)

        gradient = Color.gradient(RED, GREEN, 5)
        calls = [call(color) for color in gradient]
        self.assertEqual(mock_rgb.set_color.call_args_list, calls)

        calls = [call(10.0), call(6.0), call(6.0), call(6.0), call(10.0)]
        self.assertEqual(mock_sleep.call_args_list, calls)

        with patch.object(asyncio, "sleep") as mock_sleep:
            color = await fade.set_gradient(
                mock_rgb, colors, steps, pause_after_fade, interval, color
            )

        self.assertEqual(color, BLUE)
        self.assertEqual(mock_sleep.call_args_list, calls)

        with patch.object(asyncio, "sleep") as mock_sleep:
            color = await fade.set_gradient(
                mock_rgb, colors, steps, pause_after_fade, interval, color
            )

        self.assertEqual(color, RED)
        self.assertEqual(mock_sleep.call_args_list, calls)

    async def test_with_prev_stop_color(self) -> None:
        prev_stop_color = Color(45, 23, 212)
        mock_rgb = Mock(spec=hardware.RGB)()
        mock_rgb.devices = [Mock(), Mock(), Mock()]

        colors = cycle([RED, GREEN, BLUE])
        steps = 5
        interval = 6.0
        pause_after_fade = 20.0

        with patch.object(asyncio, "sleep") as mock_sleep:
            await fade.set_gradient(
                mock_rgb, colors, steps, pause_after_fade, interval, prev_stop_color
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

        colors = cycle([color])
        steps = 5
        interval = 6.0
        pause_after_fade = 20.0

        with patch.object(asyncio, "sleep"):
            await fade.set_gradient(
                mock_rgb, colors, steps, pause_after_fade, interval, None
            )

        mock_rgb.set_color.assert_called_once_with(color)
