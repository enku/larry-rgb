"""Hardware functions for larry_rgb"""

from dataclasses import dataclass

from larry.color import Color
from openrgb import OpenRGBClient
from openrgb.orgb import Device
from openrgb.utils import RGBColor

OPENRGB_PORT = 6742


def color_all_devices(openrgb: OpenRGBClient, color: Color) -> None:
    """Set every device's color to the given color"""
    for device in openrgb.ee_devices:
        color_device(device, color)


def color_device(device: Device, color: Color) -> None:
    """Set the given device's color to the given color"""
    device.set_color(RGBColor(color.red, color.green, color.blue))


def make_client(address: str, port: int = OPENRGB_PORT) -> OpenRGBClient:
    """Create and initialize OpenRGBClient"""
    openrgb = OpenRGBClient(address, port)

    for device in openrgb.ee_devices:
        device.set_mode("Direct")

        # Not resizing the zones on OpenRGB 0.8 results in not all rgbs getting set on
        # my system.  See https://github.com/jath03/openrgb-python/discussions/64
        led_count = len(device.leds)
        for zone in device.zones:
            zone.resize(led_count)

    return openrgb


@dataclass
class RGB:
    """Config for OpenRGB"""

    address: str = "127.0.0.1"
    port: int = OPENRGB_PORT

    def __post_init__(self) -> None:
        self.openrgb = make_client(self.address, self.port)

    def set_color(self, color: Color) -> None:
        """Send the given color to openrgb"""
        color_all_devices(self.openrgb, color)
