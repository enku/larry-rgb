# pylint: disable=missing-docstring,unused-argument
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import patch

from unittest_fixtures import Fixtures, given

import larry_rgb
from larry_rgb.config import Config
from larry_rgb.effects import get_effect

from .lib import clear_cache, make_config, np_random_seed


@given(clear_cache, np_random_seed)
class PluginTestCase(IsolatedAsyncioTestCase):
    """Tests for the plugin method"""

    async def test_instantiates_and_runs_effect(self, fixtures: Fixtures) -> None:
        config = make_config(effect="dummy")
        effect = get_effect("dummy")

        with patch.object(effect, "run") as mock_run:
            await larry_rgb.plugin([], config)

        mock_run.assert_called_once_with([], Config(config))

    async def test_when_running_resets_config(self, fixtures: Fixtures) -> None:
        config = make_config(effect="dummy", interval="500")
        effect = get_effect("dummy")

        # Mock running state
        with patch.object(effect, "is_alive", return_value=True):
            with patch.object(effect, "reset") as mock_reset:
                await larry_rgb.plugin([], config)

        mock_reset.assert_called_once_with([], Config(config))


class EnsureRangeTests(TestCase):
    def test(self) -> None:
        larry_rgb.ensure_range("l", ("a", "z"))

        with self.assertRaises(ValueError) as ctx:
            larry_rgb.ensure_range("z", ("a", "l"))

        expected = "Value 'z' is out of range ('a', 'l')"
        self.assertEqual(ctx.exception.args, (expected,))

    def test_with_error_message(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            larry_rgb.ensure_range(19, (1, 10), "This is a test")

        self.assertEqual(ctx.exception.args, ("This is a test",))
