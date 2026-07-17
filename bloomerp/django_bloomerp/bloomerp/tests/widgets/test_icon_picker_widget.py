from django.test import SimpleTestCase

from bloomerp.widgets.icon_picker_widget import DEFAULT_ICON_CHOICES, get_icon_values


class IconPickerWidgetTests(SimpleTestCase):
    def test_default_icon_choices_include_expanded_general_purpose_set(self):
        """
        Use case: The icon picker is used for workspace and model icon fields.
        Expected result: The default icon list includes a broad unique set of choices.
        """
        # 1. Collect the default icon values.
        icon_values = get_icon_values(DEFAULT_ICON_CHOICES)

        # 2. Verify the expanded set is unique and contains representative new icons.
        self.assertEqual(len(icon_values), len(set(icon_values)))
        self.assertGreaterEqual(len(icon_values), 86)
        self.assertIn("fa-solid fa-house", icon_values)
        self.assertIn("fa-solid fa-chart-line", icon_values)
        self.assertIn("fa-solid fa-database", icon_values)
        self.assertIn("fa-solid fa-hand-holding-heart", icon_values)
