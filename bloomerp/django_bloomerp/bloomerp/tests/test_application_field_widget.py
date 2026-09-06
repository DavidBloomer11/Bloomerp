from types import SimpleNamespace
from unittest.mock import Mock

from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.test import SimpleTestCase

from bloomerp.field_types.registry import FieldTypeDefinition
from bloomerp.models.application_field import ApplicationField


class ApplicationFieldWidgetTests(SimpleTestCase):
    def application_field(self, model_field=None, **definition_kwargs):
        definition = FieldTypeDefinition(id="Test", label="Test", **definition_kwargs)
        return SimpleNamespace(
            meta={"placeholder": "Enter value"},
            get_field_type=lambda: definition,
            _get_model_field=Mock(return_value=model_field),
        )

    def test_django_default_widgets_and_choices_are_preserved(self):
        for model_field, widget_class in (
            (models.IntegerField(), forms.NumberInput),
            (models.CharField(max_length=20), forms.TextInput),
            (models.CharField(choices=[("a", "Alpha")]), forms.Select),
        ):
            with self.subTest(field=type(model_field).__name__):
                field = self.application_field(model_field)
                widget = ApplicationField.get_widget(field)
                self.assertIsInstance(widget, widget_class)
                self.assertEqual(widget.attrs["placeholder"], "Enter value")
                self.assertIsNot(widget, ApplicationField.get_widget(field))
                if isinstance(widget, forms.Select):
                    self.assertIn(("a", "Alpha"), list(widget.choices))

    def test_factory_receives_context_and_takes_precedence(self):
        factory = Mock(side_effect=lambda context: forms.Textarea(attrs=context.attrs))
        field = self.application_field(widget_factory=factory)
        widget = ApplicationField.get_widget(field, {"page_size": 20})
        self.assertIsInstance(widget, forms.Textarea)
        context = factory.call_args.args[0]
        self.assertIs(context.application_field, field)
        self.assertEqual(context.layout_config, {"page_size": 20})
        field._get_model_field.assert_not_called()

    def test_virtual_form_can_supply_its_widget(self):
        factory = Mock(return_value=forms.CharField(widget=forms.Textarea))
        field = self.application_field(form_factory=factory)
        field._get_model_field.side_effect = FieldDoesNotExist
        self.assertIsInstance(ApplicationField.get_widget(field), forms.Textarea)
        self.assertEqual(factory.call_args.args[0].layout_config, {})
        self.assertIsNone(factory.call_args.args[1])

    def test_missing_or_non_editable_fields_have_a_text_fallback(self):
        for model_field in (None, models.AutoField(primary_key=True), object()):
            field = self.application_field(model_field)
            self.assertIsInstance(ApplicationField.get_widget(field), forms.TextInput)
        field._get_model_field.side_effect = FieldDoesNotExist
        self.assertIsInstance(ApplicationField.get_widget(field), forms.TextInput)
