# pylint: disable=missing-docstring,unused-argument
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import patch

from unittest_fixtures import Fixtures, given

import larry_rgb
from larry_rgb.config import Config
from larry_rgb.effects import colorfade

from .lib import clear_cache, make_config, np_random_seed


@given(clear_cache, np_random_seed)
class PluginTestCase(IsolatedAsyncioTestCase):
    """Tests for the plugin method"""

    async def test_instantiates_and_runs_effect(self, fixtures: Fixtures) -> None:
        config = make_config()

        with patch.object(colorfade.Effect, "run") as mock_run:
            await larry_rgb.plugin([], config)

        larry_rgb.get_effect()
        mock_run.assert_called_once_with([], Config(config))

    async def test_when_running_resets_config(self, fixtures: Fixtures) -> None:
        config = make_config(interval="500")
        effect = larry_rgb.get_effect()

        # Mock running state
        with patch.object(effect, "is_alive", return_value=True):
            with patch.object(colorfade.Effect, "reset") as mock_reset:
                await larry_rgb.plugin([], config)

        mock_reset.assert_called_once_with([], Config(config))

    def test_get_effect_when_effect_not_exists(self, fixtures: Fixtures) -> None:
        with patch.object(colorfade, "Effect", autospec=True) as mock_effect_cls:
            larry_rgb.get_effect()

        mock_effect_cls.assert_called_once_with()

    def test_get_effect_when_effect_does_exist(self, fixtures: Fixtures) -> None:
        with patch.object(larry_rgb, "Effect", autospec=True) as mock_effect_cls:
            original_effect = larry_rgb.get_effect()
            mock_effect_cls.reset_mock()
            effect = larry_rgb.get_effect()

        self.assertIs(effect, original_effect)
        mock_effect_cls.assert_not_called()


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
