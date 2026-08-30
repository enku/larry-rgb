"""Tests for the stream effect

The stream effect takes the dominant colors, creates a gradient for them, and "streams"
the gradients across the devices.
"""

# pylint: disable=missing-docstring,protected-access
import asyncio
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import Mock, call, patch

from larry.color import Color
from openrgb.utils import RGBColor  # type: ignore
from unittest_fixtures import Fixtures, given

from larry_rgb.config import Config
from larry_rgb.effects import stream

from .lib import BLUE, GREEN, IMAGE_COLORS, RED, make_config, rgb_client


class EffectStartTests(IsolatedAsyncioTestCase):
    async def test_when_cold(self) -> None:
        effect = stream.Effect()
        config = Config(make_config())

        with patch.object(effect, "reset") as reset:
            await effect.start([RED, GREEN, BLUE], config)

        reset.assert_called_once_with([RED, GREEN, BLUE], config)

    async def test_when_warm(self) -> None:
        effect = stream.Effect()
        effect._running = True
        config = Config(make_config())

        with patch.object(effect, "reset") as reset:
            await effect.start([RED, GREEN, BLUE], config)

        reset.assert_not_called()


class EffectResetTests(IsolatedAsyncioTestCase):
    async def test_stops_current_task(self) -> None:
        effect = stream.Effect()
        current_task = effect._task
        config = Config(make_config())

        self.assertEqual(current_task.done(), False)

        with patch.object(asyncio, "create_task", wraps=asyncio.create_task):
            with patch.object(effect, "hw_update", return_value="called"):
                await effect.reset(IMAGE_COLORS, config)

        self.assertNotEqual(effect._task, current_task)
        self.assertEqual(current_task.done(), True)

    async def test_sets_config_attr(self) -> None:
        effect = stream.Effect()
        config = Config(
            make_config(
                **{
                    "effect": "stream",
                    "effect.stream.interval": "9.0",
                    "effect.stream.dominant_color_count": "9",
                }
            )
        )

        with patch.object(asyncio, "create_task", wraps=asyncio.create_task):
            with patch.object(effect, "hw_update", return_value="called"):
                await effect.reset(IMAGE_COLORS, config)

        self.assertEqual(effect.config, config)

    async def test_sets_running_attr(self) -> None:
        effect = stream.Effect()
        config = Config(make_config())

        with patch.object(asyncio, "create_task", wraps=asyncio.create_task):
            with patch.object(effect, "hw_update", return_value="called"):
                await effect.reset(IMAGE_COLORS, config)

        self.assertEqual(effect._running, True)

    async def test_creates_new_task(self) -> None:
        effect = stream.Effect()

        for reverse in (False, True):
            with self.subTest(reverse=reverse):
                config = Config(
                    make_config(
                        **{
                            "effect": "stream",
                            "effect.stream.interval": "9.0",
                            "effect.stream.dominant_color_count": "9",
                            "effect.stream.direction": (
                                "backward" if reverse else "forward"
                            ),
                        }
                    )
                )

                with patch.object(
                    asyncio, "create_task", wraps=asyncio.create_task
                ) as create:
                    with patch.object(
                        effect, "hw_update", return_value="called"
                    ) as hw_update:
                        await effect.reset(IMAGE_COLORS, config)

                hw_update.assert_called_once_with(
                    Color.dominant(IMAGE_COLORS, 9), 9.0, reverse
                )
                create.assert_called_once()
                result = await effect._task  # type: ignore[func-returns-value]
                self.assertEqual(result, "called")


class EffectIsAliveTests(IsolatedAsyncioTestCase):
    async def test_true(self) -> None:
        effect = stream.Effect()

        with patch.object(effect, "hw_update"):
            await effect.start(
                IMAGE_COLORS, Config(make_config(address="host.invalid"))
            )

        try:
            self.assertEqual(effect.is_alive(), True)
        finally:
            await effect.stop()

    async def test_false(self) -> None:
        effect = stream.Effect()

        await effect.stop()

        self.assertEqual(effect.is_alive(), False)


class EffectStopTests(IsolatedAsyncioTestCase):
    async def test(self) -> None:
        effect = stream.Effect()
        effect.config = Config(make_config())
        effect._running = True

        self.assertEqual(effect._task.done(), False)

        await effect.stop()

        self.assertEqual(effect._running, False)
        self.assertEqual(effect._task.done(), True)


@given(rgb_client)
class EffectHWUpdateTests(IsolatedAsyncioTestCase):
    # pylint: disable=unused-argument
    async def test(self, *, fixtures: Fixtures) -> None:
        effect = stream.Effect()
        effect.config = Config(make_config())
        effect._running = True
        colors = [RED, GREEN, BLUE]

        with patch.object(effect, "color_device") as color_device:
            client = effect.config.rgb.openrgb_client
            client.ee_devices = [
                Mock(colors=rgbcolors("#000 #000 #000")) for _ in range(3)
            ]
            task = asyncio.create_task(effect.hw_update(colors, 0.01, False))
            await asyncio.sleep(0)
            effect._running = False
            await task

        self.assertEqual(color_device.call_count, 3)
        devices = client.ee_devices
        expected_calls = [
            call(devices[0], colors, 0, reverse=False),
            call(devices[1], colors, 0, reverse=False),
            call(devices[2], colors, 0, reverse=False),
        ]
        self.assertEqual(color_device.mock_calls, expected_calls)
        client.show.assert_called_once_with()

    async def test_stops_when_running_is_false(self, fixtures: Fixtures) -> None:
        effect = stream.Effect()
        effect.config = Config(make_config())
        effect._running = True
        colors = [RED, GREEN, BLUE]

        with patch.object(effect, "color_device"):
            client = effect.config.rgb.openrgb_client
            client.ee_devices = [
                Mock(colors=rgbcolors("#000 #000 #000")) for _ in range(3)
            ]
            task = asyncio.create_task(effect.hw_update(colors, 0.01, False))
            await asyncio.sleep(0)
            await asyncio.sleep(0.01)
            effect._running = False
            await task

        self.assertGreaterEqual(client.show.call_count, 2)


class EffectColorDeviceTests(IsolatedAsyncioTestCase):
    async def test(self) -> None:
        effect = stream.Effect()
        effect.config = Config(make_config())
        device = Mock(colors=[RGBColor(0, 0, 0) for _ in range(9)])

        for reverse in (False, True):
            with self.subTest(reverse=reverse):
                effect.color_device(device, [RED, GREEN, BLUE], 0, reverse=reverse)

                expected = rgbcolors(
                    "#ff0000 #aa5500 #00ff00 #00aa55 #0000ff #0055aa #00ff00 #55aa00 #ff0000"
                )
                self.assertEqual(device.colors, expected[::-1] if reverse else expected)


class ParseEffectTests(TestCase):
    def test_empty_dict(self) -> None:
        effect_config = stream.parse_effect_config({})

        self.assertEqual(
            effect_config,
            stream.EffectConfig(
                direction=stream.Direction.FORWARD,
                dominant_color_count=10,
                interval=0.1,
            ),
        )

    def test_dominant_color_count(self) -> None:
        effect_config = stream.parse_effect_config({"dominant_color_count": "1000"})

        self.assertEqual(effect_config.dominant_color_count, 1000)

    def test_interval(self) -> None:
        effect_config = stream.parse_effect_config({"interval": "3.1"})

        self.assertEqual(effect_config.interval, 3.1)


def rgbcolors(s: str) -> list[RGBColor]:
    return [RGBColor(c.red, c.green, c.blue) for i in s.split() for c in [Color(i)]]
