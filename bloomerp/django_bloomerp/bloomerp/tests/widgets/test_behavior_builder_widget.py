import json

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.test import SimpleTestCase, TestCase

from bloomerp.field_types import FIELD_TYPE_REGISTRY
from bloomerp.field_types.builtins.display import (
    build_behavior_catalog_entry,
    get_behavior_form_field_kwargs,
)
from bloomerp.form_fields.behavior import (
    BehaviorConfig,
    BehaviorRule,
    ClearValueAction,
    CopyValueFromOneToManyAction,
)
from bloomerp.form_fields.behavior_field import BehaviorField
from bloomerp.models import ApplicationField
from bloomerp.tests.base import BaseBloomerpTestCaseWithModels
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
                {
                    "id": "13",
                    "name": "lines",
                    "label": "Lines",
                    "fieldType": "OneToManyField",
                    "columns": [
                        {
                            "id": "31",
                            "name": "amount",
                            "label": "Amount",
                            "fieldType": "DecimalField",
                        }
                    ],
                },
            ],
        )
        value = {
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
        self.assertIn("Amount", html)
        self.assertEqual(json.loads(widget.value_from_datadict({"behaviors": json.dumps(value)}, {}, "behaviors")), value)

    def test_behavior_field_normalizes_and_validates_config(self):
        """
        Use case: Clean submitted Behavior builder JSON.
        Expected result: Valid rules are normalized and invalid rule collections are rejected.
        """
        # 1. Build a valid configuration through the typed Python interface.
        field = BehaviorField(required=False)
        config = BehaviorConfig(
            rules=[
                BehaviorRule(
                    name="Clear description",
                    actions=[ClearValueAction(target_field="13")],
                ),
            ],
        )

        # 2. Verify typed serialization, empty handling, and malformed input validation.
        self.assertEqual(field.clean(config.to_storage()), config.to_storage())
        self.assertIsNone(field.clean({"rules": []}))
        with self.assertRaises(forms.ValidationError):
            field.clean({"rules": {}})
        with self.assertRaises(forms.ValidationError):
            field.clean(
                {
                    "rules": [
                        {
                            "name": "Missing target",
                            "actions": [{"type": "clear_value"}],
                        },
                    ],
                },
            )

        # 3. Preserve compatibility with the frontend's current wide action payload.
        cleaned = field.clean(
            {
                "rules": [
                    {
                        "id": "rule-one",
                        "name": "Clear description",
                        "enabled": True,
                        "events": ["change"],
                        "connector": "all",
                        "conditions": [],
                        "actions": [
                            {
                                "id": "action-one",
                                "type": "clear_value",
                                "targetField": "13",
                                "value": "unused",
                                "sourceField": "12",
                                "resolver": "blank_rows",
                                "rowCount": 5,
                                "writePolicy": "replace_generated",
                                "messageTone": "info",
                            },
                        ],
                    },
                ],
            },
        )
        self.assertEqual(
            cleaned["rules"][0]["actions"][0],
            {
                "id": "action-one",
                "targetField": "13",
                "type": "clear_value",
            },
        )

    def test_one_to_many_aggregation_action_is_typed_and_validated(self):
        """
        Use case: Build row and column aggregations for a one-to-many field.
        Expected result: Count needs no column while the others require one.
        """
        # 1. Build a row-count action without selecting a column.
        count_action = CopyValueFromOneToManyAction(
            source_field="13",
            target_field="12",
            aggregation="count",
        )

        # 2. Build a numeric-column sum action.
        sum_action = CopyValueFromOneToManyAction(
            source_field="13",
            target_field="12",
            aggregation="sum",
            column_name="amount",
        )
        first_action = CopyValueFromOneToManyAction(
            source_field="13",
            target_field="12",
            aggregation="first",
            column_name="description",
        )
        last_action = CopyValueFromOneToManyAction(
            source_field="13",
            target_field="12",
            aggregation="last",
            column_name="description",
        )

        # 3. Verify both actions serialize to the frontend contract.
        self.assertEqual(count_action.model_dump(by_alias=True)["columnName"], "")
        self.assertEqual(sum_action.model_dump(by_alias=True)["columnName"], "amount")
        self.assertEqual(first_action.aggregation, "first")
        self.assertEqual(last_action.aggregation, "last")

        # 4. Verify a non-count aggregation cannot omit its column.
        with self.assertRaises(ValueError):
            CopyValueFromOneToManyAction(
                source_field="13",
                target_field="12",
                aggregation="sum",
            )

    def test_editable_field_types_expose_behaviors_in_display_options(self):
        """
        Use case: Open display options for editable field types.
        Expected result: The shared Behaviors option is available without the legacy on_change option.
        """
        # 1. Read display option identifiers from representative field types.
        week_option_ids = [option.id for option in FIELD_TYPE_REGISTRY.WEEK_FIELD.display_options]
        char_option_ids = [option.id for option in FIELD_TYPE_REGISTRY.CHAR_FIELD.display_options]

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
            field_type=FIELD_TYPE_REGISTRY.CHAR_FIELD.id,
        )
        earlier_field = ApplicationField.objects.create(
            content_type=content_type,
            field="a_behavior_test",
            field_type=FIELD_TYPE_REGISTRY.CHAR_FIELD.id,
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
        self.assertEqual(widget.source_field["fieldType"], FIELD_TYPE_REGISTRY.CHAR_FIELD.id)


class BehaviorOneToManyCatalogTest(BaseBloomerpTestCaseWithModels):
    create_foreign_models = True

    def test_catalog_exposes_configured_one_to_many_columns(self):
        """
        Use case: Configure behaviors for Country.customers.
        Expected result: Its catalog entry describes the selected customer columns.
        """
        # 1. Resolve the dynamic Country.customers application field.
        customers_field = ApplicationField.get_for_model(self.CountryModel).get(
            field="customers"
        )

        # 2. Build metadata using the field's inline layout configuration.
        entry = build_behavior_catalog_entry(
            customers_field,
            {"inline_fields": ["first_name", "age"]},
        )

        # 3. Verify action and condition definitions receive typed columns.
        self.assertEqual(entry["fieldType"], FIELD_TYPE_REGISTRY.ONE_TO_MANY_FIELD.id)
        self.assertEqual(
            [
                (column["name"], column["fieldType"])
                for column in entry["columns"]
            ],
            [
                ("first_name", FIELD_TYPE_REGISTRY.CHAR_FIELD.id),
                ("age", FIELD_TYPE_REGISTRY.INTEGER_FIELD.id),
            ],
        )
