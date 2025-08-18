"""Hardware functions for larry_rgb"""

from dataclasses import dataclass, field

from larry.color import Color
from openrgb import OpenRGBClient  # type: ignore
from openrgb.orgb import Device  # type: ignore
from openrgb.utils import RGBColor  # type: ignore

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
    openrgb_client = OpenRGBClient(address, port)

    for device in openrgb_client.ee_devices:
        device.set_mode("Direct")

        # Not resizing the zones on OpenRGB 0.8 results in not all rgbs getting set on
        # my system.  See https://github.com/jath03/openrgb-python/discussions/64
        resize_device_zones(device)

    return openrgb_client


@dataclass(frozen=True)
class RGB:
    """Config for OpenRGB"""

    address: str = "127.0.0.1"
    port: int = OPENRGB_PORT
    openrgb_client: OpenRGBClient = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "openrgb_client", make_client(self.address, self.port))

    def set_color(self, color: Color) -> None:
        """Send the given color to openrgb"""
        color_all_devices(self.openrgb_client, color)


def resize_device_zones(device: Device, size: int | None = None) -> None:
    """Resize device's zones to the given size

    size defaults the the number of leds on the device
    """
    if size is None:
        size = len(device.leds)

    for zone in device.zones:
        zone.resize(size)
