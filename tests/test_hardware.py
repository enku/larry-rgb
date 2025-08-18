"""Tests for larry_rgb.hardware"""

# pylint: disable=missing-docstring,unused-argument
import unittest
from unittest import mock

import larry
from openrgb import OpenRGBClient
from openrgb.orgb import Device
from openrgb.utils import RGBColor
from unittest_fixtures import FixtureContext, Fixtures, fixture, given

from larry_rgb import hardware as hw

from . import lib


def make_client_fixture(_: Fixtures) -> FixtureContext[mock.Mock]:
    with mock.patch.object(hw, "make_client", autospec=True) as mocked:
        yield mocked


def create_mock_openrgb(devices: int, leds=1, zones=1) -> OpenRGBClient:
    mock_devices = []
    for i in range(devices):
        if isinstance(leds, int):
            mock_leds = [mock.Mock() for _ in range(leds)]
        else:
            mock_leds = [mock.Mock() for _ in range(leds[i])]

        if isinstance(zones, int):
            mock_zones = [mock.Mock() for _ in range(zones)]
        else:
            mock_zones = [mock.Mock() for _ in range(zones[i])]

        mock_devices.append(mock.Mock(leds=mock_leds, zones=mock_zones))

    return mock.Mock(spec=OpenRGBClient, ee_devices=mock_devices)


@given(lib.device)
class ColorDeviceTestCAse(unittest.TestCase):
    def test_sets_color_on_the_device(self, fixtures: Fixtures) -> None:
        blue = larry.Color("blue")
        device = fixtures.device

        hw.color_device(device, blue)

        device.set_color.assert_called_once_with(RGBColor(0, 0, 255))


@given(d1=lib.device, d2=lib.device, d3=lib.device)
class ColorAllDevicesTestCase(unittest.TestCase):
    def test_calls_color_device_on_all_devices(self, fixtures: Fixtures) -> None:
        red = larry.Color("red")
        mock_client = mock.Mock(spec=OpenRGBClient)
        mock_client.ee_devices = [fixtures.d1, fixtures.d2, fixtures.d3]

        hw.color_all_devices(mock_client, red)

        rgb_red = RGBColor(red=255, green=0, blue=0)
        for device in mock_client.ee_devices:
            device.set_color.assert_called_once_with(rgb_red)


@mock.patch.object(hw, "OpenRGBClient", autospec=True)
class MakeClientTestCase(unittest.TestCase):
    """Tests for the make_client() function"""

    def test_instantiates_client(self, mock_openrgb_client_cls) -> None:
        client = hw.make_client("polaris.invalid", 1234)

        mock_openrgb_client_cls.assert_called_once_with("polaris.invalid", 1234)

        self.assertIsInstance(client, OpenRGBClient)

    def test_puts_devices_in_direct_mode(self, mock_openrgb_client_cls) -> None:
        mock_openrgb_client_cls.return_value = create_mock_openrgb(3)

        client = hw.make_client("polaris.invalid", 1234)

        for device in client.ee_devices:
            device.set_mode.assert_called_with("Direct")

    def test_resizes_zones(self, mock_openrgb_client_cls) -> None:
        mock_openrgb_client_cls.return_value = create_mock_openrgb(
            3, leds=[3, 2, 1], zones=[1, 2, 3]
        )

        client = hw.make_client("polaris.invalid")

        client.ee_devices[0].zones[0].resize.assert_called_once_with(3)
        client.ee_devices[1].zones[0].resize.assert_called_once_with(2)
        client.ee_devices[1].zones[1].resize.assert_called_once_with(2)
        client.ee_devices[2].zones[0].resize.assert_called_once_with(1)
        client.ee_devices[2].zones[1].resize.assert_called_once_with(1)
        client.ee_devices[2].zones[2].resize.assert_called_once_with(1)


@given(make_client_fixture)
class RGBDataclassTestCase(unittest.TestCase):
    """Tests for the RGB dataclass"""

    def test_instantiates_client(self, fixtures: Fixtures) -> None:
        rgb = hw.RGB(address="polaris.invalid")
        mock_client = fixtures.make_client.return_value

        self.assertEqual(rgb.openrgb_client, mock_client)
        fixtures.make_client.assert_called_once_with("polaris.invalid", 6742)

    def test_set_color(self, fixtures: Fixtures) -> None:
        rgb = hw.RGB(address="polaris.invalid")
        blue = larry.Color("blue")

        rgb.openrgb_client.ee_devices = [mock.Mock(), mock.Mock(), mock.Mock()]

        rgb.set_color(blue)

        rgb_blue = RGBColor(red=0, green=0, blue=255)
        for device in rgb.openrgb_client.ee_devices:
            device.set_color.assert_called_once_with(rgb_blue)


class ResizeDeviceZonesTestCase(unittest.TestCase):
    def test(self) -> None:
        Mock = mock.Mock
        device = Mock(leds=[Mock(), Mock(), Mock()], zones=[Mock(), Mock(), Mock()])

        hw.resize_device_zones(device)

        device.zones[0].resize.assert_called_once_with(3)
        device.zones[1].resize.assert_called_once_with(3)
        device.zones[2].resize.assert_called_once_with(3)
