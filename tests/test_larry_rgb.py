# pylint: disable=missing-docstring
from configparser import ConfigParser
from itertools import cycle
from pathlib import Path
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, Mock, call, patch

from larry.color import Color
from larry.config import ConfigType

import larry_rgb
from larry_rgb import colorlib, hardware
from larry_rgb.config import Config

TEST_DIR = Path(__file__).resolve().parent
IMAGE = TEST_DIR / "input.jpeg"

RED = Color("red")
GREEN = Color("green")
BLUE = Color("blue")


class PluginTestCase(IsolatedAsyncioTestCase):
    """Tests for the plugin method"""

    def setUp(self):
        larry_rgb.get_effect.cache_clear()

    async def test_instantiates_and_runs_effect(self):
        config = make_config(input=IMAGE)

        with patch.object(larry_rgb.Effect, "run") as mock_run:
            await larry_rgb.plugin([], config)

        larry_rgb.get_effect()
        mock_run.assert_called_once_with(Config(config))

    async def test_when_running_resets_config(self):
        config = make_config(input=IMAGE, interval=500)
        effect = larry_rgb.get_effect()

        # Mock running state
        effect.running = True

        with patch.object(larry_rgb.Effect, "reset") as mock_reset:
            await larry_rgb.plugin([], config)

        mock_reset.assert_called_once_with(Config(config))

    def test_get_effect_when_effect_not_exists(self):
        with patch.object(larry_rgb, "Effect", autospec=True) as mock_effect_cls:
            larry_rgb.get_effect()

        mock_effect_cls.assert_called_once_with()

    def test_get_effect_when_effect_does_exist(self):
        with patch.object(larry_rgb, "Effect", autospec=True) as mock_effect_cls:
            original_effect = larry_rgb.get_effect()
            mock_effect_cls.reset_mock()
            effect = larry_rgb.get_effect()

        self.assertIs(effect, original_effect)
        mock_effect_cls.assert_not_called()


class EffectTestCase(IsolatedAsyncioTestCase):
    """Tests for the Effect class"""

    async def test_reset(self):
        config = Config(make_config(input=IMAGE, max_palette_size=3, quality=15))
        effect = larry_rgb.Effect()
        image_colors = colorlib.get_colors(IMAGE, 3, 15)

        with patch.object(larry_rgb, "cycle") as mock_cycle:
            await effect.reset(config)

        self.assertIs(effect.config, config)
        self.assertEqual(effect.colors, mock_cycle.return_value)
        mock_cycle.assert_called_once_with(image_colors)

    async def test_reset_with_pastelize_true(self):
        config = Config(
            make_config(input=IMAGE, max_palette_size=3, quality=15, pastelize=True)
        )
        effect = larry_rgb.Effect()
        image_colors = colorlib.get_colors(IMAGE, 3, 15)
        pastel_colors = [color.pastelize() for color in image_colors]

        with patch.object(larry_rgb, "cycle") as mock_cycle:
            await effect.reset(config)

        self.assertIs(effect.config, config)
        self.assertEqual(effect.colors, mock_cycle.return_value)
        mock_cycle.assert_called_once_with(pastel_colors)

    async def test_with_intensity_set(self):
        config = Config(
            make_config(
                input=IMAGE,
                max_palette_size=3,
                quality=15,
                pastelize=False,
                intensity=0.5,
            )
        )
        effect = larry_rgb.Effect()
        image_colors = colorlib.get_colors(IMAGE, 3, 15)
        intense_colors = larry_rgb.intensify_colors(image_colors, 0.5)

        with patch.object(larry_rgb, "cycle") as mock_cycle:
            await effect.reset(config)

        mock_cycle.assert_called_once_with(intense_colors)

    async def test_reset_with_colors(self):
        config = Config(make_config(input=IMAGE, colors="#ff0000 #000000"))
        effect = larry_rgb.Effect()

        with patch.object(larry_rgb, "cycle") as mock_cycle:
            await effect.reset(config)

        self.assertEqual(effect.colors, mock_cycle.return_value)
        mock_cycle.assert_called_once_with([Color("#ff0000"), Color("#000000")])

    async def test_rgb(self):
        config = Config(make_config(input=IMAGE, max_palette_size=3, quality=15))
        effect = larry_rgb.Effect()

        with patch("larry_rgb.hw.RGB", autospec=True) as mock_rgb:
            await effect.reset(config)
            rgb = effect.rgb

        self.assertIs(rgb, mock_rgb.return_value)

    async def test_stop(self):
        effect = larry_rgb.Effect()
        effect.running = True

        await effect.stop()

        self.assertIs(effect.running, False)


def make_config(**kwargs) -> ConfigType:
    parser = ConfigParser()
    parser.add_section("rgb")
    config = ConfigType(parser, "rgb")

    for name, value in kwargs.items():
        config[name] = str(value)

    return config


class SetGradient(IsolatedAsyncioTestCase):
    """Tests for the set_gradient() method"""

    async def test_with_none(self):
        mock_rgb = Mock(spec=hardware.RGB)()
        mock_rgb.devices = [Mock(), Mock(), Mock()]
        mock_sleep = AsyncMock()

        colors = cycle([RED, GREEN, BLUE])
        steps = 5
        interval = 6.0
        pause_after_fade = 20.0
        color = await larry_rgb.set_gradient(
            mock_rgb, colors, steps, pause_after_fade, interval, None, mock_sleep
        )

        self.assertEqual(color, GREEN)

        gradient = Color.gradient(RED, GREEN, 5)
        calls = [call(color) for color in gradient]
        self.assertEqual(mock_rgb.set_color.call_args_list, calls)

        calls = [call(10.0), call(6.0), call(6.0), call(6.0), call(10.0)]
        self.assertEqual(mock_sleep.call_args_list, calls)

        mock_sleep.reset_mock()
        color = await larry_rgb.set_gradient(
            mock_rgb, colors, steps, pause_after_fade, interval, color, mock_sleep
        )

        self.assertEqual(color, BLUE)
        self.assertEqual(mock_sleep.call_args_list, calls)

        mock_sleep.reset_mock()
        color = await larry_rgb.set_gradient(
            mock_rgb, colors, steps, pause_after_fade, interval, color, mock_sleep
        )

        self.assertEqual(color, RED)
        self.assertEqual(mock_sleep.call_args_list, calls)

    async def test_with_prev_stop_color(self):
        prev_stop_color = Color(45, 23, 212)
        mock_rgb = Mock(spec=hardware.RGB)()
        mock_rgb.devices = [Mock(), Mock(), Mock()]
        mock_sleep = AsyncMock()

        colors = cycle([RED, GREEN, BLUE])
        steps = 5
        interval = 6.0
        pause_after_fade = 20.0
        await larry_rgb.set_gradient(
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

    async def test_with_same_color_does_not_set_again(self):
        color = Color(45, 23, 212)
        mock_rgb = Mock(spec=hardware.RGB)()
        mock_rgb.devices = [Mock(), Mock(), Mock()]
        mock_sleep = AsyncMock()

        colors = cycle([color])
        steps = 5
        interval = 6.0
        pause_after_fade = 20.0

        await larry_rgb.set_gradient(
            mock_rgb,
            colors,
            steps,
            pause_after_fade,
            interval,
            None,
            mock_sleep,
        )

        mock_rgb.set_color.assert_called_once_with(color)


class EnsureRangeTests(TestCase):
    def test(self):
        larry_rgb.ensure_range("l", ("a", "z"))

        with self.assertRaises(ValueError) as ctx:
            larry_rgb.ensure_range("z", ("a", "l"))

        expected = "Value 'z' is out of range ('a', 'l')"
        self.assertEqual(ctx.exception.args, (expected,))

    def test_with_error_message(self):
        with self.assertRaises(ValueError) as ctx:
            larry_rgb.ensure_range(19, (1, 10), "This is a test")

        self.assertEqual(ctx.exception.args, ("This is a test",))
