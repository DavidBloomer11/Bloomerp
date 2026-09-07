from types import SimpleNamespace
from unittest.mock import patch

from django import forms
from django.db import models
from django.test import SimpleTestCase

from bloomerp.field_types.registry import FieldTypeDefinition, load_builtin_field_types
from bloomerp.forms.model_form import bloomerp_modelform_factory
from bloomerp.models.application_field import ApplicationField


class RegisteredFormModel(models.Model):
    name = models.CharField(max_length=12)
    created_by = models.CharField(max_length=30, blank=True)

    class Meta:
        app_label = "bloomerp"
        managed = False

    @property
    def summary(self):
        return self.name.upper()


class RegisteredModelFormTests(SimpleTestCase):
    def application_field(self, name, type_id):
        return SimpleNamespace(
            field=name,
            title=name.title(),
            meta={},
            _get_model_field=lambda: RegisteredFormModel._meta.get_field(name),
            get_field_type=lambda: load_builtin_field_types().from_id(type_id),
        )

    def build_form(self, *fields):
        with patch.object(ApplicationField, "get_for_model", return_value=list(fields)):
            return bloomerp_modelform_factory(RegisteredFormModel)

    def test_django_fields_validate_and_managed_fields_ignore_submissions(self):
        form_class = self.build_form(
            self.application_field("name", "CharField"),
            self.application_field("created_by", "CharField"),
        )
        self.assertEqual(form_class._meta.fields, ["name"])
        form = form_class(
            data={"name": "New", "created_by": "Changed"},
            instance=RegisteredFormModel(name="Old", created_by="Original"),
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save(commit=False)
        self.assertEqual(instance.name, "New")
        self.assertEqual(instance.created_by, "Original")
        self.assertTrue(form.fields["created_by"].disabled)
        self.assertEqual(form.fields["name"].max_length, 12)

    def test_properties_are_read_only(self):
        form_class = self.build_form(self.application_field("summary", "Property"))
        self.assertEqual(form_class._meta.fields, [])
        self.assertTrue(form_class.base_fields["summary"].disabled)
        self.assertIn("summary", form_class.bloomerp_non_model_field_names)

    def test_virtual_factory_needs_no_legacy_flags(self):
        registry = load_builtin_field_types()
        registry.register(
            "TEST_VIRTUAL",
            FieldTypeDefinition(
                id="TestVirtual",
                label="Virtual",
                form_factory=lambda context, default: forms.IntegerField(
                    required=False
                ),
                widget_factory=lambda context: forms.NumberInput(attrs=context.attrs),
            ),
        )
        try:
            form_class = self.build_form(
                self.application_field("summary", "TestVirtual")
            )
            self.assertEqual(form_class._meta.fields, [])
            self.assertIsInstance(form_class.base_fields["summary"], forms.IntegerField)
            self.assertFalse(form_class.base_fields["summary"].disabled)
            self.assertIsInstance(
                form_class.base_fields["summary"].widget, forms.NumberInput
            )
        finally:
            registry.unregister("TEST_VIRTUAL")

    def test_registry_resolution_preserves_variants_and_specific_types(self):
        registry = load_builtin_field_types()
        self.assertIs(
            registry.resolve("ChoiceField", models.CharField()), registry.CHOICE_FIELD
        )
        phone = registry.PHONE_NUMBER_FIELD.model_field_cls()
        self.assertIs(registry.resolve("CharField", phone), registry.PHONE_NUMBER_FIELD)
        self.assertIs(
            registry.resolve("Unknown", models.IntegerField()), registry.INTEGER_FIELD
        )
