# pylint: disable=missing-docstring,unused-argument
from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, patch

from openrgb.utils import RGBColor  # type: ignore

from larry_rgb import hardware
from larry_rgb.config import Config
from larry_rgb.effects import gradient

from .lib import BLUE, GREEN, IMAGE_COLORS, RED, make_config


class GradientEffectTests(IsolatedAsyncioTestCase):
    async def test_reset_sets_config(self) -> None:
        effect = gradient.Effect()
        config = Config(make_config())

        with patch("larry_rgb.effects.gradient.hw.RGB", autospec=True):
            await effect.reset(IMAGE_COLORS, config)

        self.assertEqual(effect.config, config)

    async def test_reset_colors_devices(self) -> None:
        effect = gradient.Effect()
        config = Config(make_config())

        with patch("larry_rgb.effects.gradient.hw.RGB", autospec=True) as mock_rgb:
            mock_rgb.return_value.openrgb_client.ee_devices = [
                Mock(zones=[]) for _ in range(3)
            ]
            with patch.object(
                effect, "color_device", wraps=effect.color_device
            ) as color_device:
                await effect.reset(IMAGE_COLORS, config)

        self.assertEqual(color_device.call_count, 3)

    async def test_reset_color_count_from_config(self) -> None:
        effect = gradient.Effect()
        config = Config(
            make_config(
                **{"effect": "gradient", "effect.gradient.dominant_color_count": "4"}
            )
        )

        with patch("larry_rgb.effects.gradient.hw.RGB", autospec=True):
            with patch("larry_rgb.effects.gradient.Color.dominant") as dominant:
                await effect.reset([], config)

        dominant.assert_called_once_with([], 4)

    async def test_run(self) -> None:
        effect = gradient.Effect()
        config = Config(make_config())

        with patch.object(effect, "reset", autospec=True) as reset:
            await effect.run([], config)

        self.assertTrue(effect.running)
        reset.assert_called_once_with([], config)

        await effect.stop()
        self.assertFalse(effect.running)

    async def test_rgb_property(self) -> None:
        effect = gradient.Effect()
        config = Config(make_config())

        with patch("larry_rgb.effects.gradient.hw.RGB", autospec=True):
            await effect.reset(IMAGE_COLORS, config)

        rgb = effect.rgb

        self.assertIsInstance(rgb, hardware.RGB)

    async def test_color_device(self) -> None:
        effect = gradient.Effect()
        config = Config(make_config())
        device = Mock(zones=[Mock(leds=[Mock() for _ in range(5)]) for _ in range(3)])

        with patch("larry_rgb.effects.gradient.hw.RGB", autospec=True):
            await effect.reset(IMAGE_COLORS, config)

        effect.color_device(device, [RED, GREEN, BLUE])

        expected = [(255, 0, 0), (170, 85, 0), (0, 255, 0), (0, 170, 85), (0, 0, 255)]
        expected = expected * 3
        i = 0
        for zone in range(3):
            for led in range(5):
                color = RGBColor(*expected[i])
                device.zones[zone].leds[led].set_color.assert_called_once_with(color)
                i += 1
