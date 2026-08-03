import json

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.test import SimpleTestCase, TestCase

from bloomerp.field_types.types import FieldType, get_behavior_form_field_kwargs
from bloomerp.form_fields.behavior_field import BehaviorField
from bloomerp.models import ApplicationField
from bloomerp.widgets.behavior_builder_widget import BehaviorBuilderWidget


class BehaviorBuilderWidgetTest(SimpleTestCase):
    def test_widget_renders_visual_builder_catalog_and_serialized_value(self):
        """
        Use case: Render a configured Behavior builder widget.
        Expected result: The field catalog and serialized rules are present in the widget HTML.
        """
        # 1. Configure a widget and a representative behavior value.
        widget = BehaviorBuilderWidget(
            source_field={"id": "12", "label": "Week", "fieldType": "WeekField"},
            field_catalog=[
                {"id": "12", "name": "week", "label": "Week", "fieldType": "WeekField"},
                {"id": "13", "name": "lines", "label": "Lines", "fieldType": "OneToManyField"},
            ],
        )
        value = {
            "version": 1,
            "rules": [
                {
                    "id": "weekdays",
                    "name": "Fill weekdays",
                    "enabled": True,
                    "events": ["initial", "change"],
                    "conditions": [],
                    "actions": [
                        {
                            "id": "populate-weekdays",
                            "type": "populate_rows",
                            "targetField": "13",
                            "resolver": "blank_rows",
                            "rowCount": 5,
                        }
                    ],
                }
            ],
        }

        # 2. Render the widget and verify its configuration contract.
        html = widget.render("behaviors", value, attrs={"id": "id_behaviors"})

        self.assertIn('bloomerp-component="behavior-builder"', html)
        self.assertIn('data-behavior-source-field-label="Week"', html)
        self.assertIn('data-behavior-source-field-type="WeekField"', html)
        self.assertIn('data-behavior-field-catalog=', html)
        self.assertIn('name="behaviors"', html)
        self.assertIn("Fill weekdays", html)
        self.assertIn("rowCount", html)
        self.assertEqual(json.loads(widget.value_from_datadict({"behaviors": json.dumps(value)}, {}, "behaviors")), value)

    def test_behavior_field_normalizes_and_validates_config(self):
        """
        Use case: Clean submitted Behavior builder JSON.
        Expected result: Valid rules are normalized and invalid rule collections are rejected.
        """
        # 1. Configure the form field and an input using a future version number.
        field = BehaviorField(required=False)
        config = {
            "version": 9,
            "rules": [{"id": "one", "conditions": [], "actions": []}],
        }

        # 2. Verify normalization, empty handling, and malformed input validation.
        self.assertEqual(
            field.clean(config),
            {
                "version": 1,
                "rules": [{"id": "one", "conditions": [], "actions": []}],
            },
        )
        self.assertIsNone(field.clean({"version": 1, "rules": []}))
        with self.assertRaises(forms.ValidationError):
            field.clean({"version": 1, "rules": {}})

    def test_editable_field_types_expose_behaviors_in_display_options(self):
        """
        Use case: Open display options for editable field types.
        Expected result: The shared Behaviors option is available without the legacy on_change option.
        """
        # 1. Read display option identifiers from representative field types.
        week_option_ids = [option.id for option in FieldType.WEEK_FIELD.value.field_display_options]
        char_option_ids = [option.id for option in FieldType.CHAR_FIELD.value.field_display_options]

        # 2. Verify the shared option is exposed consistently.
        self.assertIn("behaviors", week_option_ids)
        self.assertIn("behaviors", char_option_ids)
        self.assertNotIn("on_change", char_option_ids)


class BehaviorDisplayOptionDatabaseTest(TestCase):
    def test_behavior_field_catalog_is_built_using_database_fields(self):
        """
        Use case: Build the Behavior field catalog from ApplicationField records.
        Expected result: Catalog entries are ordered by a real database field without raising FieldError.
        """
        # 1. Create two application fields in reverse alphabetical order.
        content_type = ContentType.objects.get_for_model(ApplicationField)
        later_field = ApplicationField.objects.create(
            content_type=content_type,
            field="z_behavior_test",
            field_type=FieldType.CHAR_FIELD.value.id,
        )
        earlier_field = ApplicationField.objects.create(
            content_type=content_type,
            field="a_behavior_test",
            field_type=FieldType.CHAR_FIELD.value.id,
        )

        # 2. Build the widget using the database-backed catalog query.
        widget = get_behavior_form_field_kwargs(later_field)["widget"]

        # 3. Verify the relevant catalog entries use deterministic field-name ordering.
        catalog_names = [
            field["name"]
            for field in widget.field_catalog
            if field["id"] in {str(earlier_field.pk), str(later_field.pk)}
        ]
        self.assertEqual(catalog_names, ["a_behavior_test", "z_behavior_test"])
        self.assertEqual(widget.source_field["fieldType"], FieldType.CHAR_FIELD.value.id)
