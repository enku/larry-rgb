# pylint: disable=missing-docstring,unused-argument
from unittest import TestCase
from unittest.mock import patch

from unittest_fixtures import Fixtures, given, where

from larry_rgb.effects import get_effect, list_effects

from .lib import clear_cache, effects_entry_points


@given(clear_cache)
class GetEffectTests(TestCase):
    def test_get_effect_when_effect_not_exists(self, *, fixtures: Fixtures) -> None:
        with patch("larry_rgb.effects.dummy.Effect", autospec=True) as mock_effect_cls:
            get_effect("dummy")

        mock_effect_cls.assert_called_once_with()

    def test_get_effect_when_effect_does_exist(self, *, fixtures: Fixtures) -> None:
        effect = get_effect("dummy")
        with patch("larry_rgb.effects.dummy.Effect", autospec=True) as mock_effect_cls:
            original_effect = get_effect("dummy")
            mock_effect_cls.reset_mock()
            effect = get_effect("dummy")

        self.assertIs(effect, original_effect)
        mock_effect_cls.assert_not_called()

    def test_nonexistent_effect(self, *, fixtures: Fixtures) -> None:
        with self.assertRaises(LookupError) as context:
            get_effect("bogus")

        self.assertEqual(str(context.exception), "'bogus'")


@given(effects_entry_points)
@where(effects_entry_points__names=["foo", "bar", "baz", "random", "dummy", "candy"])
class TestListEffects(TestCase):
    def test(self, *, fixtures: Fixtures) -> None:
        names = list_effects()

        self.assertEqual(names, ["foo", "bar", "baz", "random", "dummy", "candy"])
