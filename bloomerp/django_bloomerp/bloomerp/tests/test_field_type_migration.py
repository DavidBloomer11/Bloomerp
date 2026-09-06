from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from django import forms
from django.core.management import call_command
from django.db import models
from django.test import SimpleTestCase
from django.test.utils import isolate_apps

from bloomerp.field_types import FieldTypeDefinition
from bloomerp.field_types.display_options import FieldDisplayOption
from bloomerp.field_types.lookups import TEXT_LOOKUPS
from bloomerp.field_types.registry import FIELD_TYPE_REGISTRY, field_type_choices
from bloomerp.management.commands.save_application_fields import (
    get_registered_field_type_id,
)
from bloomerp.models.application_field import ApplicationField


class FieldTypeMigrationTests(SimpleTestCase):
    def test_public_definition_is_the_registered_definition(self):
        self.assertIsInstance(FIELD_TYPE_REGISTRY.CHAR_FIELD, FieldTypeDefinition)

    def test_late_registration_updates_choices_filters_and_exports(self):
        from bloomerp.components.application_fields.filters import (
            filterable_field_type_ids,
        )

        # Import consumers before registering, as an extension app may do.
        before = filterable_field_type_ids()
        FIELD_TYPE_REGISTRY.register(
            "TEST_EXTENSION",
            FieldTypeDefinition(
                id="TestExtension", label="Extension", lookups=tuple(TEXT_LOOKUPS)
            ),
        )
        try:
            self.assertNotIn("TestExtension", before)
            self.assertIn("TestExtension", filterable_field_type_ids())
            self.assertIn(("TestExtension", "Extension"), field_type_choices())
            choices = ApplicationField._meta.get_field("field_type").choices
            self.assertIn(("TestExtension", "Extension"), list(choices))
            with TemporaryDirectory() as directory:
                output = Path(directory) / "fieldTypes.ts"
                call_command("export_field_types", str(output), stdout=StringIO())
                self.assertIn('["TEST_EXTENSION"]', output.read_text())
                self.assertIn(
                    'new FieldTypeDefinition("TestExtension")', output.read_text()
                )
        finally:
            FIELD_TYPE_REGISTRY.unregister("TEST_EXTENSION")

    def test_template_flags_use_symbolic_keys(self):
        flags = FIELD_TYPE_REGISTRY.template_context("ForeignKey")
        self.assertTrue(flags["foreign_key"])
        self.assertFalse(flags["boolean_field"])
        self.assertFalse(any(FIELD_TYPE_REGISTRY.template_context("Missing").values()))

    def test_sync_recognizes_subclasses_reverse_relations_and_files(self):
        class CustomText(models.CharField):
            pass

        field = CustomText(max_length=10)
        field.set_attributes_from_name("title")
        self.assertEqual(get_registered_field_type_id(field), "CharField")
        reverse = SimpleNamespace(
            name="lines",
            auto_created=True,
            is_relation=True,
            one_to_many=True,
            one_to_one=False,
        )
        self.assertEqual(get_registered_field_type_id(reverse), "OneToManyField")
        reverse.name = "files"
        self.assertEqual(get_registered_field_type_id(reverse), "FilesRelationField")
        self.assertIsNone(FIELD_TYPE_REGISTRY.get_from_model_field_cls(object))

    def test_workspace_filters_do_not_hash_definitions(self):
        from bloomerp.components.workspaces.filter_workspace import (
            _render_workspace_filter_lookup_value,
        )

        field = SimpleNamespace(field="active")
        html = _render_workspace_filter_lookup_value(
            field, FIELD_TYPE_REGISTRY.BOOLEAN_FIELD, "equals"
        )
        self.assertIn("<select", html)
        html = _render_workspace_filter_lookup_value(
            field, FIELD_TYPE_REGISTRY.CHAR_FIELD, "equals"
        )
        self.assertIn("<input", html)

    def test_display_options_use_the_new_definition(self):
        from bloomerp.components.objects.field_display_options import create_form

        definition = FieldTypeDefinition(
            id="TestDisplay",
            label="Display",
            display_options=(
                FieldDisplayOption(
                    id="label", label="Label", form_field_cls=forms.CharField
                ),
            ),
        )
        form_class = create_form(definition, SimpleNamespace())
        self.assertIn("label", form_class.base_fields)

    @isolate_apps("bloomerp_modules")
    def test_module_reader_uses_registry_construction_defaults(self):
        from bloomerp.modules.definition import ModuleConfig
        from bloomerp_modules.utils.reader import (
            FieldConfig,
            ModelConfig,
            create_model_from_config,
        )

        module = ModuleConfig(id="test", name="Test", code="test")
        config = ModelConfig(
            id="record",
            name="Registry Record",
            fields=[
                FieldConfig(id="title", name="Title", type="CharField"),
                FieldConfig(id="amount", name="Amount", type="IntegerField"),
            ],
        )
        model = create_model_from_config(config, module)
        self.assertEqual(model._meta.get_field("title").max_length, 255)
        self.assertIsInstance(model._meta.get_field("amount"), models.IntegerField)
