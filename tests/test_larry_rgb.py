# pylint: disable=missing-docstring,unused-argument
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from unittest_fixtures import Fixtures, given, where

import larry_rgb
from larry_rgb.config import Config
from larry_rgb.effects import get_effect

from .lib import clear_cache, config_t, np_random_seed


@given(clear_cache, np_random_seed, config_t)
@where(config={"effect": "dummy"})
class PluginTestCase(IsolatedAsyncioTestCase):
    """Tests for the plugin method"""

    async def test_instantiates_and_starts_effect(self, fixtures: Fixtures) -> None:
        config = fixtures.config_t
        effect = get_effect("dummy")

        with patch.object(effect, "start") as mock_start:
            await larry_rgb.plugin([], config)

        mock_start.assert_called_once_with([], Config(config))

    async def test_when_running_resets_config(self, fixtures: Fixtures) -> None:
        effect = get_effect("dummy")

        # Mock running state
        with patch.object(effect, "is_alive", return_value=True):
            with patch.object(effect, "reset") as mock_reset:
                await larry_rgb.plugin([], fixtures.config_t)

        mock_reset.assert_called_once_with([], Config(fixtures.config_t))
