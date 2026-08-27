# pylint: disable=missing-docstring,unused-argument
from unittest import TestCase
from unittest.mock import patch

from unittest_fixtures import Fixtures, given

from larry_rgb.effects import get_effect

from .lib import clear_cache


@given(clear_cache)
class GetEffectTests(TestCase):
    def test_get_effect_when_effect_not_exists(self, fixtures: Fixtures) -> None:
        with patch("larry_rgb.effects.dummy.Effect", autospec=True) as mock_effect_cls:
            get_effect("dummy")

        mock_effect_cls.assert_called_once_with()

    def test_get_effect_when_effect_does_exist(self, fixtures: Fixtures) -> None:
        effect = get_effect("dummy")
        with patch("larry_rgb.effects.dummy.Effect", autospec=True) as mock_effect_cls:
            original_effect = get_effect("dummy")
            mock_effect_cls.reset_mock()
            effect = get_effect("dummy")

        self.assertIs(effect, original_effect)
        mock_effect_cls.assert_not_called()
