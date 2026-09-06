from types import SimpleNamespace

from django import forms
from django.test import SimpleTestCase

from bloomerp.field_types.builtins import register_builtin_field_types
from bloomerp.field_types.registry import (
    FieldContext,
    FieldTypeDefinition,
    FieldTypeRegistry,
    load_builtin_field_types,
)
from bloomerp.field_types.lookups import Lookup
from bloomerp.model_fields.status_field import StatusField
from bloomerp.model_fields.file_field import BloomerpFileField
from bloomerp.form_fields.one_to_many_field import OneToManyField
from bloomerp.widgets.text_editor import BloomerpTextEditorWidget


class FieldTypeRegistryTests(SimpleTestCase):
    def setUp(self):
        self.registry = FieldTypeRegistry(FieldTypeDefinition)
        register_builtin_field_types(self.registry)

    def test_builtin_metadata(self):
        self.assertEqual(len(self.registry.values()), 49)
        for key, definition in self.registry.items():
            with self.subTest(field_type=key):
                self.assertIs(self.registry.from_id(definition.id), definition)
                self.assertEqual(
                    [option.id for option in definition.display_options][:1], ["label"]
                )
        self.assertEqual(
            self.registry.CHAR_FIELD.construction.defaults["max_length"], 255
        )
        self.assertEqual(
            self.registry.CHOICE_FIELD.construction.defaults["max_length"], 255
        )
        self.assertIn(Lookup.CONTAINS, self.registry.JSON_FIELD.lookups)
        self.assertIs(self.registry.STATUS_FIELD.model_field_cls, StatusField)
        self.assertIs(
            self.registry.BLOOMERP_FILE_FIELD.model_field_cls, BloomerpFileField
        )

    def test_factories_create_fresh_widgets(self):
        context = FieldContext(attrs={"class": "test"})
        for definition in self.registry.values():
            if definition.widget_factory is None:
                continue
            with self.subTest(field_type=definition.id):
                first = definition.widget_factory(context)
                self.assertIsInstance(first, forms.Widget)
                self.assertIsNot(first, definition.widget_factory(context))
                self.assertIn("test", first.attrs["class"].split())
        self.assertEqual(context.attrs, {"class": "test"})
        self.assertIsInstance(
            self.registry.TEXT_FIELD.widget_factory(context), BloomerpTextEditorWidget
        )
        self.assertEqual(
            self.registry.JSON_FIELD.widget_factory(context).language, "json"
        )

    def test_relation_context_and_virtual_forms(self):
        parent, related = object(), object()
        application_field = SimpleNamespace(
            get_related_model=lambda: related, get_model=lambda: parent, title="Lines"
        )
        context = FieldContext(
            application_field=application_field,
            layout_config={"inline_fields": ["amount"], "page_size": 20},
        )
        foreign = self.registry.FOREIGN_KEY.widget_factory(context)
        self.assertIs(foreign.model, related)
        self.assertFalse(foreign.is_m2m)
        self.assertTrue(self.registry.MANY_TO_MANY_FIELD.widget_factory(context).is_m2m)
        inline = self.registry.ONE_TO_MANY_FIELD.widget_factory(context)
        self.assertIs(inline.parent_model, parent)
        self.assertIs(inline.related_model, related)
        self.assertEqual(inline.fields, ["amount"])
        self.assertEqual(inline.page_size, 20)
        field = self.registry.ONE_TO_MANY_FIELD.form_factory(context, None)
        self.assertIsInstance(field, OneToManyField)
        self.assertIs(field.application_field, application_field)
        self.assertFalse(field.required)
        self.assertIsInstance(
            self.registry.FILES_RELATION_FIELD.form_factory(context, None), forms.Field
        )

    def test_form_factory_preserves_model_configuration(self):
        model_field = self.registry.PHONE_NUMBER_FIELD.model_field_cls(
            max_length=24, blank=True, help_text="Contact number"
        )
        context = FieldContext(
            application_field=SimpleNamespace(_get_model_field=lambda: model_field)
        )
        field = self.registry.PHONE_NUMBER_FIELD.form_factory(
            context, model_field.formfield()
        )
        self.assertEqual(field.max_length, 24)
        self.assertEqual(field.help_text, "Contact number")
        self.assertFalse(field.required)

    def test_loading_and_duplicate_ids(self):
        first = load_builtin_field_types()
        self.assertIs(load_builtin_field_types(), first)
        self.assertEqual(len(first.values()), 49)
        with self.assertRaises(ValueError):
            self.registry.register(
                "ALIAS", FieldTypeDefinition(id="CharField", label="Alias")
            )
