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

    async def test_with_tranform_from_config(self, *, fixtures: Fixtures) -> None:
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
                    "#ff0000 #8d7100 #1ce200 #00aa54 #0038c6 #0038c6 #00a955 #1ce200 #8d7100"
                )
                self.assertEqual(device.colors, expected[::-1] if reverse else expected)


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

        self.assertEqual(color, Color("#5f484c"))

    def test_twinkle(self) -> None:
        with patch.object(stream, "random", random.Random(1)):
            color = TRANSFORMS["twinkle"](Color("#ffc0cb"), 5, 16)

        self.assertEqual(color, Color("#22191b"))
