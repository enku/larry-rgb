"""Tests lib"""

# pylint: disable=missing-docstring,redefined-outer-name

from configparser import ConfigParser
from itertools import cycle
from pathlib import Path
from typing import Iterable
from unittest import mock

import numpy as np
from larry import Color
from larry.config import ConfigType
from larry.image import RasterImage
from openrgb.orgb import Device
from unittest_fixtures import FixtureContext, Fixtures, fixture

from larry_rgb import effects

TEST_DIR = Path(__file__).resolve().parent
IMAGE = TEST_DIR / "input.jpeg"
IMAGE_COLORS = list(RasterImage(IMAGE.read_bytes()).colors)

RED = Color("red")
GREEN = Color("green")
BLUE = Color("blue")


def make_config(**kwargs: str) -> ConfigType:
    parser = ConfigParser()
    parser.add_section("rgb")
    config = ConfigType(parser, "rgb")

    config.update(kwargs)

    return config


@fixture()
def clear_cache(_: Fixtures) -> None:
    """Clear the get_effect cache"""
    effects.get_effect.cache_clear()


@fixture()
def color_cycle(
    _: Fixtures, colors: Iterable[Color] = (RED, GREEN, BLUE)
) -> Iterable[Color]:
    """Return an endless cycle of colors"""
    return cycle(colors)


@fixture()
def device(_: Fixtures, leds: int = 1, zones: int = 1) -> mock.Mock:
    return mock.Mock(
        spec=Device,
        leds=[mock.Mock() for _ in range(leds)],
        zones=[mock.Mock() for _ in range(zones)],
    )


@fixture()
def np_random_seed(_: Fixtures, np_random_seed: int = 1) -> None:
    """Seed numpy's RNG"""
    np.random.seed(np_random_seed)


@fixture()
def effects_entry_points(
    _: Fixtures, names: list[str] | None = None
) -> FixtureContext[list[str]]:
    """Mock larry_rgb.effects entry points"""
    if names is None:
        names = ["fade", "dummy", "gradient", "random"]

    with mock.patch("larry_rgb.effects.entry_points") as mocked:
        values: list[mock.Mock] = []
        for name in names:
            ep = mock.Mock()
            config = {
                "name": name,
                "load.return_value.return_value.start": mock.AsyncMock(),
            }
            ep.configure_mock(**config)
            values.append(ep)

        mocked.return_value.select.return_value = values

        yield names


@fixture()
def rgb_client(_: Fixtures, where: str = "larry_rgb.config.hardware.OpenRGBClient"):
    with mock.patch(where) as client:
        yield client.return_value
