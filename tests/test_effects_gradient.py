# pylint: disable=missing-docstring,unused-argument
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, patch

from unittest_fixtures import Fixtures, given, where

from larry_rgb.effects import gradient

from .lib import BLUE, GREEN, IMAGE_COLORS, RED
from .lib import config as config_f
from .lib import rgb_client, rgbcolors

Arrangement = gradient.Arrangement


@given(rgb_client, config_f)
@where(config={"effect": "gradient", "effect.gradient.dominant_color_count": "4"})
class GradientEffectTests(IsolatedAsyncioTestCase):
    async def test_reset_colors_devices(self, *, fixtures: Fixtures) -> None:
        effect = gradient.Effect()

        fixtures.config.rgb.openrgb_client.ee_devices = [
            Mock(zones=[]) for _ in range(3)
        ]
        with patch.object(
            effect, "color_device", wraps=effect.color_device
        ) as color_device:
            await effect.reset(IMAGE_COLORS, fixtures.config)

        self.assertEqual(color_device.call_count, 3)

    async def test_reset_color_count_from_config(self, *, fixtures: Fixtures) -> None:
        effect = gradient.Effect()

        with patch("larry_rgb.effects.gradient.Color.dominant") as dominant:
            await effect.reset([], fixtures.config)

        dominant.assert_called_once_with([], 4)

    async def test_start(self, *, fixtures: Fixtures) -> None:
        effect = gradient.Effect()

        with patch.object(effect, "reset", autospec=True) as reset:
            await effect.start([], fixtures.config)

        self.assertTrue(effect.running)
        reset.assert_called_once_with([], fixtures.config)

        await effect.stop()
        self.assertFalse(effect.running)

    async def test_color_device(self, *, fixtures: Fixtures) -> None:
        effect = gradient.Effect()
        device = Mock(zones=[Mock(leds=[Mock() for _ in range(5)]) for _ in range(3)])

        await effect.reset(IMAGE_COLORS, fixtures.config)

        effect.color_device(
            device, [RED, GREEN, BLUE], fixtures.config, Arrangement.NORMAL
        )

        expected = rgbcolors("#ff0000 #7f7f00 #00ff00 #007f7f #0000ff")

        for zone in device.zones:
            self.assertEqual(zone.colors, expected)
            zone.show.assert_called_once_with()

    async def test_not_mirrored(self, *, fixtures: Fixtures) -> None:
        effect = gradient.Effect()
        device = Mock(zones=[Mock(leds=[Mock() for _ in range(15)])])

        await effect.reset(IMAGE_COLORS, fixtures.config)

        effect.color_device(
            device, [RED, GREEN, BLUE], fixtures.config, Arrangement.NORMAL
        )

        expected = rgbcolors(
            " #ff0000 #da2400 #b64800 #916d00 #6d9100"
            " #48b600 #24da00 #00ff00 #00da24 #00b648"
            " #00916d #006d91 #0048b6 #0024da #0000ff"
        )

        for zone in device.zones:
            self.assertEqual(zone.colors, expected)
            zone.show.assert_called_once_with()

    async def test_mirrored(self, *, fixtures: Fixtures) -> None:
        effect = gradient.Effect()
        device = Mock(zones=[Mock(leds=[Mock() for _ in range(15)])])

        await effect.reset(IMAGE_COLORS, fixtures.config)

        effect.color_device(
            device, [RED, GREEN, BLUE], fixtures.config, Arrangement.MIRRORED
        )

        expected = rgbcolors(
            " #ff0000 #bb4400 #778800 #32cc00 #00ee10"
            " #00aa54 #006599 #0021dd #0021dd #006599"
            " #00a955 #00ed11 #33cb00 #778700 #bb4300"
        )

        for zone in device.zones:
            self.assertEqual(zone.colors, expected)
            zone.show.assert_called_once_with()

    def test_is_alive_false(self, *, fixtures: Fixtures) -> None:
        effect = gradient.Effect()

        self.assertEqual(effect.is_alive(), False)

    def test_is_alive_true(self, *, fixtures: Fixtures) -> None:
        effect = gradient.Effect()
        effect.running = True

        self.assertEqual(effect.is_alive(), True)
