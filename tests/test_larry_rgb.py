# pylint: disable=missing-docstring
import importlib.metadata
import tempfile
from configparser import ConfigParser
from itertools import cycle
from pathlib import Path
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, Mock, call, patch

import PIL
from larry.color import Color
from larry.config import ConfigType
from openrgb.utils import RGBColor

import larry_rgb

TEST_DIR = Path(__file__).resolve().parent
IMAGE = TEST_DIR / "input.jpeg"

RED = Color("red")
GREEN = Color("green")
BLUE = Color("blue")


class PluginTestCase(IsolatedAsyncioTestCase):
    """Tests for the plugin method"""

    def setUp(self):
        larry_rgb.get_effect.cache_clear()

    async def test_instantiates_and_sets_effect(self):
        config = make_config(input=IMAGE)

        with patch.object(larry_rgb.Effect, "run") as mock_run:
            await larry_rgb.plugin([], config)

        effect = larry_rgb.get_effect()
        self.assertIs(effect.config, config)
        mock_run.assert_called_once_with()

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

    def test_against_svg_image(self):
        larry_pkg = importlib.metadata.distribution("larry")
        svg_file = larry_pkg.locate_file("larry/data/gentoo-cow-gdm-remake.svg")
        image_colors = larry_rgb.get_colors(str(svg_file), 3, 15)

        expected = {
            Color(34, 65, 80),
            Color(123, 139, 147),
            Color(4, 4, 4),
            Color(84, 100, 111),
        }
        self.assertEqual(set(image_colors), expected)

    def test_against_bad_svg_image(self):
        with tempfile.NamedTemporaryFile(suffix=".svg") as bad_svg:
            bad_svg.write(b"not really an svg")
            bad_svg.flush()

            with self.assertRaises(PIL.UnidentifiedImageError):
                larry_rgb.get_colors(bad_svg.name, 3, 15)


class EffectTestCase(IsolatedAsyncioTestCase):
    """Tests for the Effect class"""

    async def test_reset(self):
        effect = larry_rgb.Effect()
        image_colors = larry_rgb.get_colors(IMAGE, 3, 15)
        config = make_config(input=IMAGE, max_palette_size=3, quality=15)

        with patch.object(larry_rgb, "cycle") as mock_cycle:
            await effect.reset(config)

        self.assertIs(effect.config, config)
        self.assertEqual(effect.colors, mock_cycle(image_colors))

    def test_rgb(self):
        effect = larry_rgb.Effect()
        effect.config["address"] = "foo.invalid:666"

        with patch.object(larry_rgb, "RGB", autospec=True) as mock_rgb:
            rgb = effect.rgb

        self.assertIsInstance(rgb, larry_rgb.RGB)
        mock_rgb.assert_called_once_with(address="foo.invalid", port=666)


def make_config(**kwargs) -> ConfigType:
    parser = ConfigParser()
    parser.add_section("rgb")
    config = ConfigType(parser, "rgb")

    for name, value in kwargs.items():
        config[name] = str(value)

    return config


@patch.object(larry_rgb.hw, "make_client", autospec=True)
class RGBDataclassTestCase(TestCase):
    """Tests for the RGB dataclass"""

    def test_instantiates_client(self, mock_make_client):
        rgb = larry_rgb.RGB(address="polaris.invalid")
        mock_client = mock_make_client.return_value

        self.assertEqual(rgb.openrgb, mock_client)
        mock_make_client.assert_called_once_with("polaris.invalid", 6742)

    def test_set_color(self, _mock_make_client):
        rgb = larry_rgb.RGB(address="polaris.invalid")
        blue = Color("blue")

        rgb.openrgb.ee_devices = [Mock(), Mock(), Mock()]

        rgb.set_color(blue)

        rgb_blue = RGBColor(red=0, green=0, blue=255)
        for device in rgb.openrgb.ee_devices:
            device.set_color.assert_called_once_with(rgb_blue)


class GetGradientColors(TestCase):
    """Tests for the get_gradient_colors() method"""

    def test_with_none(self):
        colors = cycle([RED, GREEN, BLUE])
        start_color, stop_color = larry_rgb.get_gradient_colors(colors, None)

        self.assertEqual(start_color, RED)
        self.assertEqual(stop_color, GREEN)

    def test_with_prev_stop_color(self):
        prev_stop_color = Color(45, 23, 212)
        colors = cycle([RED, GREEN, BLUE])
        start_color, stop_color = larry_rgb.get_gradient_colors(colors, prev_stop_color)

        self.assertEqual(start_color, Color(prev_stop_color))
        self.assertEqual(stop_color, RED)


class SetGradient(IsolatedAsyncioTestCase):
    """Tests for the set_gradient() method"""

    async def test_with_none(self):
        mock_rgb = Mock(spec=larry_rgb.RGB)()
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
        mock_rgb = Mock(spec=larry_rgb.RGB)()
        mock_rgb.devices = [Mock(), Mock(), Mock()]
        mock_sleep = AsyncMock()

        colors = cycle([RED, GREEN, BLUE])
        steps = 5
        interval = 6.0
        pause_after_fade = 20.0
        color = await larry_rgb.set_gradient(
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
