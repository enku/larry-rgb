"""Gradient Effect"""

from larry.color import Color, ColorList
from larry.plugins import apply_plugin_filter
from openrgb.orgb import Device  # type: ignore
from openrgb.utils import RGBColor  # type: ignore

from larry_rgb import effects
from larry_rgb.config import Config


class Effect(effects.Effect):
    """Gradient Effect"""

    def __init__(self) -> None:
        self.running = False

    async def reset(self, colors: ColorList, config: Config) -> None:
        """Reset the effect"""
        effect_config = config.effect_config
        dominant_colors = Color.dominant(
            colors, int(effect_config.get("dominant_color_count", "10"))
        )

        for device in config.rgb.openrgb_client.ee_devices:
            self.color_device(device, dominant_colors, config)

    def is_alive(self) -> bool:
        """Return True if the effect is running"""
        return self.running

    async def start(self, colors: ColorList, config: Config) -> None:
        """Just does a reset"""
        self.running = True
        await self.reset(colors, config)

    async def stop(self) -> None:
        """Stop the Effect"""
        self.running = False

    def color_device(self, device: Device, colors: ColorList, config: Config) -> None:
        """Set the given device's color to the given color"""
        for zone in device.zones:
            led_count = len(zone.leds)
            gradient = list(Color.gradient2(colors[:led_count], led_count))
            gradient = apply_plugin_filter(gradient, config.config)

            for led, color in zip(zone.leds, gradient):
                led.set_color(RGBColor(color.red, color.green, color.blue))
