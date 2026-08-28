# pylint: disable=missing-docstring,unused-argument
from dataclasses import dataclass
from unittest import TestCase
from unittest.mock import Mock, patch

from unittest_fixtures import Fixtures, given

from larry_rgb.effects import get_effect, list_effects

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


class TestListEffects(TestCase):
    def test(self) -> None:
        @dataclass
        class MockEP:
            name: str

        names = ["foo", "bar", "baz", "random", "dummy", "candy"]
        entry_points = Mock()
        entry_points.select.return_value = [MockEP(name) for name in names]

        with patch("larry_rgb.effects.entry_points", return_value=entry_points):
            effect_names = list_effects()

        entry_points.select.assert_called_once_with(group="larry_rgb.effects")
        self.assertEqual(effect_names, names)
