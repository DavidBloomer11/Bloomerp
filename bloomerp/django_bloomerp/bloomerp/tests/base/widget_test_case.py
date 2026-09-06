from django import forms
from django.test import SimpleTestCase


class BloomerpWidgetTestCase(SimpleTestCase):
    """Base class providing common validity checks for a Django widget."""

    widget_class: type[forms.Widget] | None = None

    def get_widget_kwargs(self) -> dict:
        """Return constructor arguments for widgets that need custom setup."""
        return {}

    def test_widget_is_valid(self) -> None:
        """
        Use case: An app exposes a custom Django widget.
        Expected result: The widget is instantiable and declares a template.
        """
        # 1. Do not execute the reusable base class itself.
        if self.widget_class is None:
            return

        # 2. Validate and instantiate the configured widget.
        self.assertTrue(issubclass(self.widget_class, forms.Widget))
        widget = self.widget_class(**self.get_widget_kwargs())

        # 3. Ensure Django can identify the template used to render it.
        self.assertIsInstance(widget, forms.Widget)
        self.assertTrue(widget.template_name)
