"""Tests for the stream effect

The stream effect takes the dominant colors, creates a gradient for them, and "streams"
the gradients across the devices.
"""

# pylint: disable=missing-docstring,protected-access
import asyncio
import random
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import ANY, Mock, call, patch

from larry.color import Color
from unittest_fixtures import Fixtures, given, where

from larry_rgb.effects import stream

from .lib import BLUE, GREEN, IMAGE_COLORS, RED
from .lib import config as config_f
from .lib import rgb_client, rgbcolors

TRANSFORMS = stream.TRANSFORMS


@given(config_f)
class EffectStartTests(IsolatedAsyncioTestCase):
    async def test_when_cold(self, *, fixtures: Fixtures) -> None:
        effect = stream.Effect()

        with patch.object(effect, "reset") as reset:
            await effect.start([RED, GREEN, BLUE], fixtures.config)

        reset.assert_called_once_with([RED, GREEN, BLUE], fixtures.config)

    async def test_when_warm(self, fixtures: Fixtures) -> None:
        effect = stream.Effect()
        effect._running = True

        with patch.object(effect, "reset") as reset:
            await effect.start([RED, GREEN, BLUE], fixtures.config)

        reset.assert_not_called()


@given(config_f)
@where(
    config={
        "effect": "stream",
        "effect.stream.interval": "9.0",
        "effect.stream.dominant_color_count": "9",
    }
)
class EffectResetTests(IsolatedAsyncioTestCase):
    async def test_stops_current_task(self, *, fixtures: Fixtures) -> None:
        effect = stream.Effect()
        current_task = effect._task

        self.assertEqual(current_task.done(), False)

        with patch.object(asyncio, "create_task", wraps=asyncio.create_task):
            with patch.object(effect, "hw_update", return_value="called"):
                await effect.reset(IMAGE_COLORS, fixtures.config)

        self.assertNotEqual(effect._task, current_task)
        self.assertEqual(current_task.done(), True)

    async def test_sets_config_attr(self, *, fixtures: Fixtures) -> None:
        effect = stream.Effect()

        with patch.object(asyncio, "create_task", wraps=asyncio.create_task):
            with patch.object(effect, "hw_update", return_value="called"):
                await effect.reset(IMAGE_COLORS, fixtures.config)

        self.assertEqual(effect.config, fixtures.config)

    async def test_sets_running_attr(self, *, fixtures: Fixtures) -> None:
        effect = stream.Effect()

        with patch.object(asyncio, "create_task", wraps=asyncio.create_task):
            with patch.object(effect, "hw_update", return_value="called"):
                await effect.reset(IMAGE_COLORS, fixtures.config)

        self.assertEqual(effect._running, True)

    async def test_creates_new_task(self, *, fixtures: Fixtures) -> None:
        effect = stream.Effect()
        Direction = stream.Direction

        for direction in Direction:
            with self.subTest(direction=direction.name):
                config = fixtures.config
                config.config["effect.stream.direction"] = str(direction)
                with patch.object(
                    asyncio, "create_task", wraps=asyncio.create_task
                ) as create:
                    with patch.object(
                        effect, "hw_update", return_value="called"
                    ) as hw_update:
                        with patch.object(stream, "random", random.Random(1)):
                            await effect.reset(IMAGE_COLORS, config)

                reverse = {
                    Direction.FORWARD: False,
                    Direction.BACKWARD: True,
                    Direction.RANDOM: True,
                }[direction]

                hw_update.assert_called_once_with(
                    Color.dominant(IMAGE_COLORS, 9), 9.0, reverse, "none"
                )
                create.assert_called_once()
                result = await effect._task  # type: ignore[func-returns-value]
                self.assertEqual(result, "called")

    async def test_with_transform_from_config(self, *, fixtures: Fixtures) -> None:
        config = fixtures.config
        config.config["effect.stream.transform"] = "random"
        effect = stream.Effect()

        with patch.object(stream, "random", random.Random(1)):
            with patch.object(effect, "hw_update") as hw_update:
                await effect.reset(IMAGE_COLORS, config)

        hw_update.assert_called_once_with(ANY, 9.0, False, "fade")


@given(config_f)
class EffectIsAliveTests(IsolatedAsyncioTestCase):
    async def test_true(self, *, fixtures: Fixtures) -> None:
        effect = stream.Effect()

        with patch.object(effect, "hw_update"):
            await effect.start(IMAGE_COLORS, fixtures.config)

        try:
            self.assertEqual(effect.is_alive(), True)
        finally:
            await effect.stop()

    async def test_false(self, *, fixtures: Fixtures) -> None:
        # pylint: disable=unused-argument
        effect = stream.Effect()

        await effect.stop()

        self.assertEqual(effect.is_alive(), False)


@given(config_f)
class EffectStopTests(IsolatedAsyncioTestCase):
    # pylint: disable=unused-argument
    async def test(self, *, fixtures: Fixtures) -> None:
        effect = stream.Effect()
        effect._running = True

        self.assertEqual(effect._task.done(), False)

        await effect.stop()

        self.assertEqual(effect._running, False)
        self.assertEqual(effect._task.done(), True)


@given(rgb_client, config_f)
class EffectHWUpdateTests(IsolatedAsyncioTestCase):
    async def test(self, *, fixtures: Fixtures) -> None:
        effect = stream.Effect()
        effect.config = fixtures.config
        effect._running = True
        colors = [RED, GREEN, BLUE]

        with patch.object(effect, "color_device") as color_device:
            client = effect.config.rgb.openrgb_client
            client.ee_devices = [
                Mock(colors=rgbcolors("#000 #000 #000")) for _ in range(3)
            ]
            task = asyncio.create_task(effect.hw_update(colors, 0.01, False, "none"))
            await asyncio.sleep(0)
            effect._running = False
            await task

        self.assertEqual(color_device.call_count, 3)
        devices = client.ee_devices
        expected_calls = [
            call(devices[0], colors, 0, reverse=False, transform="none"),
            call(devices[1], colors, 0, reverse=False, transform="none"),
            call(devices[2], colors, 0, reverse=False, transform="none"),
        ]
        self.assertEqual(color_device.mock_calls, expected_calls)
        client.show.assert_called_once_with()

    async def test_stops_when_running_is_false(self, fixtures: Fixtures) -> None:
        effect = stream.Effect()
        effect.config = fixtures.config
        effect._running = True
        colors = [RED, GREEN, BLUE]

        with patch.object(effect, "color_device"):
            client = effect.config.rgb.openrgb_client
            client.ee_devices = [
                Mock(colors=rgbcolors("#000 #000 #000")) for _ in range(3)
            ]
            task = asyncio.create_task(effect.hw_update(colors, 0.01, False, "none"))
            await asyncio.sleep(0)
            await asyncio.sleep(0.01)
            effect._running = False
            await task

        self.assertGreaterEqual(client.show.call_count, 2)


@given(config_f)
class EffectColorDeviceTests(IsolatedAsyncioTestCase):
    async def test(self, *, fixtures: Fixtures) -> None:
        effect = stream.Effect()
        effect.config = fixtures.config
        device = Mock(colors=rgbcolors("#000") * 9)

        for reverse in (False, True):
            with self.subTest(reverse=reverse):
                effect.color_device(
                    device, [RED, GREEN, BLUE], 0, reverse=reverse, transform="none"
                )

                expected = rgbcolors(
                    "#ff0000 #aa5500 #55aa00 #00ff00 #00aa54 #0054aa #0000ff #5500a9 #a90055"
                )
                self.assertEqual(device.colors, expected[::-1] if reverse else expected)

    async def test_long_device(self, *, fixtures: Fixtures) -> None:
        effect = stream.Effect()
        device = Mock(colors=rgbcolors("#000") * 255)
        effect.config = fixtures.config

        effect.color_device(
            device, [RED, GREEN, BLUE], 182, reverse=False, transform="none"
        )

        expected = rgbcolors("""
            #2300db #2600d8 #2900d5 #2c00d2 #2f00cf #3200cc #3600c8 #3900c5 #3c00c3
            #3f00c0 #4100bd #4400ba #4700b7 #4a00b4 #4e00b0 #5100ad #5400aa #5700a7
            #5a00a4 #5d00a2 #60009f #62009c #660098 #690095 #6c0092 #6f008f #72008c
            #750089 #780086 #7b0083 #7e0081 #81007e #83007b #860078 #890075 #8c0072
            #8f006f #92006c #960068 #990065 #9c0062 #9f0060 #a2005d #a4005a #a70057
            #aa0054 #ae0050 #b1004d #b4004a #b70047 #ba0044 #bd0041 #c0003f #c3003c
            #c50039 #c80036 #cb0033 #ce0030 #d1002d #d4002a #d70027 #da0024 #de0020
            #e1001e #e3001b #e60018 #e90015 #ec0012 #ef000f #f2000c #f60008 #f90005
            #fc0002 #ff0000 #fc0300 #f90600 #f60900 #f30c00 #f00f00 #ed1200 #ea1500
            #e71800 #e41b00 #e11e00 #de2000 #db2400 #d82700 #d52a00 #d22c00 #cf3000
            #cc3300 #c93600 #c63800 #c33c00 #c03f00 #bd4100 #ba4500 #b74800 #b34b00
            #b14e00 #ae5100 #ab5400 #a85700 #a55900 #a25d00 #9f6000 #9b6300 #996600
            #956900 #936c00 #906f00 #8d7100 #8a7500 #877800 #837b00 #817e00 #7e8100
            #7b8300 #788700 #758a00 #718d00 #6f9000 #6b9300 #699600 #659900 #629c00
            #609f00 #5da200 #59a500 #57a800 #53ab00 #51ae00 #4eb100 #4bb300 #48b700
            #45ba00 #41bd00 #3fc000 #3cc300 #38c600 #35c900 #32cc00 #30cf00 #2cd200
            #29d500 #27d800 #24db00 #20de00 #1ee100 #1be300 #18e600 #14ea00 #11ed00
            #0ff000 #0cf300 #08f600 #05f900 #02fc00 #00ff00 #00fc02 #00f905 #00f608
            #00f30b #00f00f #00ed11 #00ea14 #00e717 #00e31b #00e11e #00de20 #00db23
            #00d727 #00d42a #00d22d #00cf30 #00cb33 #00c836 #00c539 #00c33c #00c03f
            #00bd41 #00ba44 #00b747 #00b34b #00b14e #00ae51 #00ab53 #00a757 #00a45a
            #00a25d #009f60 #009c62 #009965 #009668 #00936b #00906f #008d71 #008a74
            #008777 #00837b #00817e #007e81 #007b83 #007886 #007589 #00718d #006e90
            #006b93 #006896 #006599 #00629c #00609f #005da2 #0059a5 #0056a8 #0053ab
            #0051ae #004eb1 #004bb3 #0048b6 #0045b9 #0041bd #003fc0 #003cc3 #0039c5
            #0036c8 #0033cb #0030ce #002dd1 #0029d5 #0026d8 #0023db #0020de #001ee1
            #001be3 #0018e6 #0015e9 #0011ed #000ef0 #000bf3 #0008f6 #0005f9 #0002fc
            #0000ff #0200fc #0500f9 #0800f6 #0b00f3 #0e00f0 #1100ed #1400ea #1700e7
            #1a00e4 #1e00e1 #2000de
        """)
        self.assertEqual(device.colors, expected)


@given(config_f)
@where(config={"effect": "stream"})
class EffectConfigTests(TestCase):
    def test_empty_dict(self, *, fixtures: Fixtures) -> None:
        effect_config = stream.EffectConfig.from_config(fixtures.config)

        self.assertEqual(effect_config.direction, stream.Direction.FORWARD)
        self.assertEqual(effect_config.dominant_color_count, 10)
        self.assertEqual(effect_config.interval, 0.1)
        self.assertEqual(effect_config.transform, "none")

    def test_dominant_color_count(self, *, fixtures: Fixtures) -> None:
        config = fixtures.config
        config.config["effect.stream.dominant_color_count"] = "1000"
        effect_config = stream.EffectConfig.from_config(config)

        self.assertEqual(effect_config.dominant_color_count, 1000)

    def test_interval(self, *, fixtures: Fixtures) -> None:
        config = fixtures.config
        config.config["effect.stream.interval"] = "3.1"
        effect_config = stream.EffectConfig.from_config(config)

        self.assertEqual(effect_config.interval, 3.1)

    def test_transform(self, *, fixtures: Fixtures) -> None:
        config = fixtures.config
        config.config["effect.stream.transform"] = "random"
        effect_config = stream.EffectConfig.from_config(config)

        self.assertEqual(effect_config.transform, "random")


class TransformTests(TestCase):
    def test_all(self) -> None:
        for name, transform in TRANSFORMS.items():
            with self.subTest(transform=name):
                color = transform(Color("#ffc0cb"), 5, 16)
                self.assertIsInstance(color, Color)

    def test_none(self) -> None:
        color = TRANSFORMS["none"](Color("#ffc0cb"), 5, 16)

        self.assertEqual(color, Color("#ffc0cb"))

    def test_fade(self) -> None:
        color = TRANSFORMS["fade"](Color("#ffc0cb"), 5, 16)

        self.assertEqual(color, Color("#a07980"))

    def test_twinkle(self) -> None:
        with patch.object(stream, "random", random.Random(1)):
            color = TRANSFORMS["twinkle"](Color("#ffc0cb"), 5, 16)

        self.assertEqual(color, Color("#22191b"))


class LogarithmicCurve(TestCase):
    def test(self) -> None:
        total = 30
        data = []

        for i in range(total):
            data.append(stream.logarithmic_curve(i, total))

        self.assertEqual(
            "\n".join(f"{i:02d} {'█' * round(d * 78)}" for i, d in enumerate(data)),
            """\
00 ██████████████████████████████████████████████████████████████████████████████
01 ████████████████████████████████████████████████████████████████████████████
02 ██████████████████████████████████████████████████████████████████████████
03 ████████████████████████████████████████████████████████████████████████
04 ██████████████████████████████████████████████████████████████████████
05 ███████████████████████████████████████████████████████████████████
06 █████████████████████████████████████████████████████████████████
07 ██████████████████████████████████████████████████████████████
08 ██████████████████████████████████████████████████████████
09 ███████████████████████████████████████████████████████
10 ██████████████████████████████████████████████████
11 █████████████████████████████████████████████
12 ███████████████████████████████████████
13 ███████████████████████████████
14 ████████████████████
15 
16 ████████████████████
17 ████████████████████████████████
18 ████████████████████████████████████████
19 ██████████████████████████████████████████████
20 ████████████████████████████████████████████████████
21 ████████████████████████████████████████████████████████
22 ████████████████████████████████████████████████████████████
23 ███████████████████████████████████████████████████████████████
24 ██████████████████████████████████████████████████████████████████
25 █████████████████████████████████████████████████████████████████████
26 ████████████████████████████████████████████████████████████████████████
27 ██████████████████████████████████████████████████████████████████████████
28 ████████████████████████████████████████████████████████████████████████████
29 ██████████████████████████████████████████████████████████████████████████████""",
        )
