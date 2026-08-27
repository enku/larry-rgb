"""Gradient Effect"""

from functools import cached_property

from larry.color import Color, ColorList
from larry.plugins import apply_plugin_filter
from openrgb.orgb import Device  # type: ignore
from openrgb.utils import RGBColor  # type: ignore

from larry_rgb import hardware as hw
from larry_rgb.config import Config


class Effect:
    """Gradient Effect"""

    def __init__(self) -> None:
        self.config: Config
        self.running = False

    async def reset(self, colors: ColorList, config: Config) -> None:
        """Reset the effect"""
        self.config = config
        effect_config = config.effect.config
        dominant_colors = Color.dominant(
            colors, int(getattr(effect_config, "dominant_color_count", "10"))
        )

        for device in self.rgb.openrgb_client.ee_devices:
            self.color_device(device, dominant_colors)

    def is_alive(self) -> bool:
        """Return True if the effect is running"""
        return self.running

    async def run(self, colors: ColorList, config: Config) -> None:
        """Just does a reset"""
        self.running = True
        await self.reset(colors, config)

    async def stop(self) -> None:
        """Stop the Effect"""
        self.running = False

    @cached_property
    def rgb(self) -> hw.RGB:
        """Returns the RGB instance.

        A (cached) property so we only instantiate it once, lazily
        """  # pylint: disable=duplicate-code
        if not hasattr(self, "config"):
            raise RuntimeError("Effect has not been (re)set")

        address_and_port = self.config.address
        address, _, port_str = address_and_port.partition(":")
        port = int(port_str) if port_str else 6742

        return hw.RGB(address=address, port=port)

    def color_device(self, device: Device, colors: ColorList) -> None:
        """Set the given device's color to the given color"""
        for zone in device.zones:
            led_count = len(zone.leds)
            gradient = list(Color.gradient2(colors[:led_count], led_count))
            gradient = apply_plugin_filter(gradient, self.config.config)

            for led, color in zip(zone.leds, gradient):
                led.set_color(RGBColor(color.red, color.green, color.blue))
