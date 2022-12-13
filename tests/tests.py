# pylint: disable=missing-docstring
from configparser import ConfigParser
from itertools import cycle
from pathlib import Path
from threading import Thread
from typing import Any
from unittest import TestCase
from unittest.mock import Mock, call, patch

from larry import ConfigType
from larry.color import Color
from openrgb import OpenRGBClient
from openrgb.utils import RGBColor

import larry_rgb

TEST_DIR = Path(__file__).resolve().parent
IMAGE = TEST_DIR / "input.jpeg"

RED = Color("red")
GREEN = Color("green")
BLUE = Color("blue")


class MockThread(Thread):
    def __init__(  # pylint: disable=too-many-arguments,super-init-not-called
        self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None
    ):
        self.target = target
        self.args = args
        self.kwargs = kwargs or {}
        self.group = group
        self._running = False

    def start(self) -> None:
        if self.target is not None:
            target = self.target
        else:
            target = self.run

        self._running = True
        target(*self.args, **self.kwargs)
        self._running = False

    def run(self) -> Any:
        return

    def is_alive(self) -> bool:
        return self._running


class MockEffect(larry_rgb.Effect):
    def __init__(self) -> None:
        super().__init__()
        self.thread = MockThread()


class PluginTestCase(TestCase):
    """Tests for the plugin method"""

    def setUp(self):
        larry_rgb.get_effect.cache_clear()

    def test_instantiates_and_sets_effect(self):
        with patch.object(larry_rgb, "get_effect") as mock_get_effect:
            mock_effect = mock_get_effect.return_value = MockEffect()
            config = make_config(input=IMAGE)
            larry_rgb.plugin([], config)

        self.assertEqual(mock_effect.config, config)

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


@patch.object(larry_rgb, "OpenRGBClient")
@patch.object(larry_rgb.time, "sleep")
class EffectTestCase(TestCase):
    """Tests for the Effect class"""

    def setUp(self):
        self.effect = larry_rgb.Effect()

    def test_set_next_gradient_with_none(self, mock_sleep, mock_rgbclient):
        rgb_client = mock_rgbclient.return_value
        rgb_client.ee_devices = [Mock(), Mock(), Mock()]

        self.effect.image_colors = [RED, GREEN, BLUE]
        self.effect.colors = cycle(self.effect.image_colors)
        self.effect.config["gradient_steps"] = "5"
        self.effect.config["interval"] = "6"
        self.effect.config["pause_after_fade"] = "20"
        color = self.effect.set_next_gradient(None)

        self.assertEqual(color, GREEN)

        gradient = Color.gradient(RED, GREEN, 5)
        calls = [
            call(RGBColor(color.red, color.green, color.blue)) for color in gradient
        ]
        for device in rgb_client.ee_devices:
            self.assertEqual(device.set_color.call_args_list, calls)

        calls = [call(10.0), call(6.0), call(6.0), call(6.0), call(10.0)]
        self.assertEqual(mock_sleep.call_args_list, calls)

        mock_sleep.reset_mock()
        color = self.effect.set_next_gradient(color)

        self.assertEqual(color, BLUE)
        self.assertEqual(mock_sleep.call_args_list, calls)

        mock_sleep.reset_mock()
        color = self.effect.set_next_gradient(color)

        self.assertEqual(color, RED)
        self.assertEqual(mock_sleep.call_args_list, calls)

    def test_set_next_gradient_with_prev_stop_color(self, mock_sleep, mock_rgbclient):
        prev_stop_color = Color(45, 23, 212)
        rgb_client = mock_rgbclient.return_value
        rgb_client.ee_devices = [Mock(), Mock(), Mock()]

        self.effect.colors = cycle([RED, GREEN, BLUE])
        self.effect.config["gradient_steps"] = "5"
        self.effect.config["interval"] = "6"
        color = self.effect.set_next_gradient(prev_stop_color)

        gradient = Color.gradient(prev_stop_color, RED, 5)
        calls = [
            call(RGBColor(color.red, color.green, color.blue)) for color in gradient
        ]
        for device in rgb_client.ee_devices:
            self.assertEqual(device.set_color.call_args_list, calls)

        self.assertEqual(mock_sleep.call_count, 5)
        mock_sleep.assert_called_with(6.0)

    def test_get_gradient_colors_with_none(self, *_):
        self.effect.colors = cycle([RED, GREEN, BLUE])
        start_color, stop_color = self.effect.get_gradient_colors(None)

        self.assertEqual(start_color, RED)
        self.assertEqual(stop_color, GREEN)

    def test_get_gradient_colors_with_prev_stop_color(self, *_):
        prev_stop_color = Color(45, 23, 212)
        self.effect.colors = cycle([RED, GREEN, BLUE])
        start_color, stop_color = self.effect.get_gradient_colors(prev_stop_color)

        self.assertEqual(start_color, Color(prev_stop_color))
        self.assertEqual(stop_color, RED)

    def test_reset(self, *_):
        config = make_config(input=IMAGE, max_palette_size=3, quality=15)

        with patch.object(larry_rgb, "cycle") as mock_cycle:
            self.effect.reset(config)

        self.assertIs(self.effect.config, config)

        image_colors = larry_rgb.get_colors(IMAGE, 3, 15)
        mock_cycle.assert_called_once_with(image_colors)
        self.assertEqual(self.effect.colors, mock_cycle.return_value)


def make_config(**kwargs) -> ConfigType:
    parser = ConfigParser()
    parser.add_section("rgb")
    config = ConfigType(parser, "rgb")

    for name, value in kwargs.items():
        config[name] = str(value)

    return config


@patch.object(larry_rgb, "OpenRGBClient", spec=OpenRGBClient)
class RGBDataclassTestCase(TestCase):
    """Tests for the RGB dataclass"""

    def test_instantiates_client(self, mock_openrgb_client_cls):
        rgb = larry_rgb.RGB(address="polaris.invalid")
        mock_client = mock_openrgb_client_cls.return_value

        mock_openrgb_client_cls.assert_called_once_with("polaris.invalid", 6742)
        self.assertEqual(rgb.openrgb, mock_client)

    def test_get_devices(self, mock_openrgb_client_cls):
        mock_devices = [Mock(), Mock(), Mock()]
        mock_openrgb_client_cls.return_value.ee_devices = mock_devices

        rgb = larry_rgb.RGB(address="polaris.invalid")

        self.assertEqual(rgb.devices, mock_devices)

    def test_put_devices_in_direct_mode(self, mock_openrgb_client_cls):
        mock_devices = [Mock(), Mock(), Mock()]
        mock_openrgb_client_cls.return_value.ee_devices = mock_devices
        larry_rgb.RGB(address="polaris.invalid")

        for device in mock_devices:
            device.set_mode.assert_called_with("Direct")

    def test_set_color(self, mock_openrgb_client_cls):
        mock_devices = [Mock(), Mock(), Mock()]
        mock_openrgb_client_cls.return_value.ee_devices = mock_devices
        rgb = larry_rgb.RGB(address="polaris.invalid")
        blue = Color("blue")

        rgb.set_color(blue)

        for device in mock_devices:
            device.set_color.assert_called_once_with(RGBColor(red=0, green=0, blue=255))
