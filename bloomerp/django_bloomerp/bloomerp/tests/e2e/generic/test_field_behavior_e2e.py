from urllib.parse import urlencode

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from playwright.sync_api import expect

from bloomerp.form_fields.behavior import (
    BehaviorCondition,
    BehaviorConfig,
    BehaviorEvent,
    BehaviorOperator,
    BehaviorRule,
    ClearValueAction,
    CopyValueFromOneToManyAction,
    PopulateRowsAction,
    SetValueAction,
)
from bloomerp.models.application_field import ApplicationField
from bloomerp.models import FieldLayout, LayoutItem, LayoutRow
from bloomerp.models.users.user_object_layout_preference import (
    UserObjectLayoutPreference,
)
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.tests.e2e.base import BaseE2ETestCase
from bloomerp.tests.e2e.generic.test_crud_mixin import TestCrudE2EMixin
from bloomerp.utils.models import get_create_view_url


def add_layout_behavior_to_preference(
    preference: UserObjectLayoutPreference,
    source_field: ApplicationField,
    behavior: BehaviorConfig,
) -> None:
    """Attach a behavior to a source field in a layout preference."""
    layout = preference.layout_obj.model_copy(deep=True)
    source_item = next(
        item
        for row in layout.rows
        for item in row.items
        if str(item.id) == str(source_field.pk)
    )
    source_item.config = {
        **source_item.config,
        "behaviors": behavior.to_storage(),
    }
    preference.layout = layout.model_dump()
    preference.save(update_fields=["layout"])


class TestFieldBehaviorE2E(TestCrudE2EMixin, BaseE2ETestCase):
    create_foreign_models = True

    def extendedE2ESetup(self) -> None:
        """Expose the Country fields shared by the behavior scenarios."""
        self.country_fields = ApplicationField.get_for_model(self.CountryModel)
        self.country_content_type = ContentType.objects.get_for_model(
            self.CountryModel
        )
        self.country_preference = PreferenceManager(
            self.admin_user
        ).get_or_create_selected(
            UserObjectLayoutPreference,
            scope={"content_type_id": self.country_content_type.pk},
        )
        self.country_preference.layout = FieldLayout(
            rows=[
                LayoutRow(
                    columns=1,
                    title="Country behavior fields",
                    items=[
                        LayoutItem(id=self.get_country_field("name").pk),
                        LayoutItem(id=self.get_country_field("planet").pk),
                        LayoutItem(
                            id=self.get_country_field("customers").pk,
                            config={"inline_fields": ["first_name", "age"]},
                        ),
                    ],
                )
            ]
        ).model_dump()
        self.country_preference.save(update_fields=["layout"])
        self.CustomerModel._meta.get_field("age").default = 42
        self.login_as_admin()

    def get_country_field(self, field_name: str) -> ApplicationField:
        """Return one application field from the dynamic Country model."""
        return self.country_fields.get(field=field_name)

    def configure_country_behavior(
        self,
        *,
        source_field_name: str,
        rules: list[BehaviorRule],
    ) -> None:
        """Attach behavior rules to a Country field in the active layout."""
        add_layout_behavior_to_preference(
            preference=self.country_preference,
            source_field=self.get_country_field(source_field_name),
            behavior=BehaviorConfig(rules=rules),
        )

    def get_country_create_url(
        self,
        query: dict[str, object] | None = None,
    ) -> str:
        """Build the Country create URL, optionally with initial form values."""
        url = reverse(get_create_view_url(model=self.CountryModel))
        return f"{url}?{urlencode(query)}" if query else url

    def select_foreign_value(self, field_name: str, label: str) -> None:
        """Select an object in a Country foreign-field widget by its label."""
        widget = self.locate_field(field_name)
        widget.locator('input[type="text"]').fill(label)
        widget.locator(".foreign-field-results").get_by_text(
            label,
            exact=True,
        ).click()

    def test_changing_one_field_clears_another_field(self):
        """
        Use case: Configure a Country field change to clear another field.
        Expected result: Changing the planet empties the Country name.
        """
        # 1. Configure planet changes to clear the name field.
        name_field = self.get_country_field("name")
        self.configure_country_behavior(
            source_field_name="planet",
            rules=[
                BehaviorRule(
                    name="Clear name when planet changes",
                    actions=[
                        ClearValueAction(target_field=str(name_field.pk)),
                    ],
                )
            ],
        )

        # 2. Enter a name, then change the source field.
        self.goto(self.get_country_create_url())
        name_input = self.locate_field("name")
        name_input.fill("Belgium")
        self.select_foreign_value("planet", "Earth")

        # 3. Verify the configured clear-value action ran.
        expect(name_input).to_have_value("")

    def test_condition_is_empty_works_on_one_to_many_field(self):
        """
        Use case: Evaluate an is-empty condition against a one-to-many field.
        Expected result: The action runs with zero rows and is skipped with a row.
        """
        # 1. Configure a behavior whose condition inspects Country.customers.
        customers_field = self.get_country_field("customers")
        name_field = self.get_country_field("name")
        self.configure_country_behavior(
            source_field_name="planet",
            rules=[
                BehaviorRule(
                    id="is_empty_condition",
                    conditions=[
                        BehaviorCondition(
                            field=str(customers_field.pk),
                            operator=BehaviorOperator.IS_EMPTY,
                        )
                    ],
                    actions=[
                        SetValueAction(
                            target_field=str(name_field.pk),
                            value="No customers",
                        ),
                    ],
                )
            ],
        )

        # 2. Verify the action runs when the one-to-many field has no rows.
        self.goto(self.get_country_create_url())
        self.select_foreign_value("planet", "Earth")
        expect(self.locate_field("name")).to_have_value("No customers")

        # 3. Verify the action is skipped when the field has one row.
        self.goto(
            self.get_country_create_url(
                {"customers__0__first_name": "Existing customer"}
            )
        )
        self.select_foreign_value("planet", "Mars")
        expect(self.locate_field("name")).to_have_value("")

    def test_reset_functionality_restores_form_after_action_changed_state(self):
        """
        Use case: Reset a Country form after a behavior changed its state.
        Expected result: Both user and behavior changes return to initial values.
        """
        # 1. Configure planet changes to set the Country name.
        name_field = self.get_country_field("name")
        self.configure_country_behavior(
            source_field_name="planet",
            rules=[
                BehaviorRule(
                    id="set_country_name",
                    actions=[
                        SetValueAction(
                            target_field=str(name_field.pk),
                            value="Behavior-updated country",
                        ),
                    ],
                )
            ],
        )

        # 2. Change the source field and verify the action changed the target.
        self.goto(self.get_country_create_url())
        self.select_foreign_value("planet", "Earth")
        expect(self.locate_field("name")).to_have_value(
            "Behavior-updated country"
        )

        # 3. Reset the form.
        self.page.get_by_role("button", name="Reset").click()

        # 4. Verify both values returned to their initial state.
        expect(self.locate_field("name")).to_have_value("")
        expect(
            self.locate_field("planet").locator('input[name="planet"]')
        ).to_have_count(0)

    def test_count_can_be_extracted_from_o2m_field(self):
        """
        Use case: Copy the number of Country.customer rows into a scalar field.
        Expected result: Two customer rows produce the value "2".
        """
        # 1. Configure the customers field as the behavior source.
        customers_field = self.get_country_field("customers")
        name_field = self.get_country_field("name")
        self.configure_country_behavior(
            source_field_name="customers",
            rules=[
                BehaviorRule(
                    events=[BehaviorEvent.CHANGE, BehaviorEvent.INITIAL],
                    actions=[
                        CopyValueFromOneToManyAction(
                            source_field=str(customers_field.pk),
                            target_field=str(name_field.pk),
                            aggregation="count",
                        )
                    ],
                )
            ],
        )

        # 2. Open a Country form with two initial customer rows.
        self.goto(
            self.get_country_create_url(
                {
                    "customers__0__first_name": "Ada",
                    "customers__1__first_name": "Grace",
                }
            )
        )

        # 3. Verify the target contains the row count.
        expect(self.locate_field("name")).to_have_value("2")

    def test_populate_related_rows_uses_column_defaults(self):
        """
        Use case: Populate blank related rows through a form behavior.
        Expected result: Each generated row uses the related model column default.
        """
        # 1. Configure the Planet change to create two Customer rows.
        customers_field = self.get_country_field("customers")
        self.configure_country_behavior(
            source_field_name="planet",
            rules=[
                BehaviorRule(
                    events=[BehaviorEvent.CHANGE],
                    actions=[
                        PopulateRowsAction(
                            target_field=str(customers_field.pk),
                            row_count=2,
                        )
                    ],
                )
            ],
        )

        # 2. Change the source field to trigger the populate-related-rows behavior.
        self.goto(self.get_country_create_url())
        self.select_foreign_value("planet", "Earth")

        # 3. Verify both generated Customer rows received the age default.
        customers_widget = self.page.locator('[data-one-to-many-name="customers"]')
        age_inputs = customers_widget.locator(
            '[data-one-to-many-cell="age"] input'
        )
        expect(age_inputs).to_have_count(2)
        self.assertEqual([input_.input_value() for input_ in age_inputs.all()], ["42", "42"])

    def test_sum_of_numeric_field_can_be_extracted_from_o2m_field(self):
        """
        Use case: Sum Customer.age values from Country.customer rows.
        Expected result: Customer ages 10 and 20 produce the value "30".
        """
        # 1. Configure the customers field as the behavior source.
        customers_field = self.get_country_field("customers")
        name_field = self.get_country_field("name")
        self.configure_country_behavior(
            source_field_name="customers",
            rules=[
                BehaviorRule(
                    events=[BehaviorEvent.CHANGE, BehaviorEvent.INITIAL],
                    actions=[
                        CopyValueFromOneToManyAction(
                            source_field=str(customers_field.pk),
                            target_field=str(name_field.pk),
                            aggregation="sum",
                            column_name="age",
                        )
                    ],
                )
            ],
        )

        # 2. Open a Country form with two customer ages.
        self.goto(
            self.get_country_create_url(
                {
                    "customers__0__first_name": "Ada",
                    "customers__0__age": 10,
                    "customers__1__first_name": "Grace",
                    "customers__1__age": 20,
                }
            )
        )

        # 3. Verify the target contains the sum of the age column.
        expect(self.locate_field("name")).to_have_value("30")

    def test_first_and_last_values_can_be_extracted_from_o2m_field(self):
        """
        Use case: Read the first and last values from an ordered O2M column.
        Expected result: Aggregation preserves the current customer row order.
        """
        # 1. Resolve the behavior fields and prepare two ordered customer rows.
        customers_field = self.get_country_field("customers")
        name_field = self.get_country_field("name")
        url = self.get_country_create_url(
            {
                "customers__0__first_name": "Ada",
                "customers__1__first_name": "Grace",
            }
        )

        # 2. Verify the first-value aggregation reads the first row.
        self.configure_country_behavior(
            source_field_name="customers",
            rules=[
                BehaviorRule(
                    events=[BehaviorEvent.CHANGE, BehaviorEvent.INITIAL],
                    actions=[
                        CopyValueFromOneToManyAction(
                            source_field=str(customers_field.pk),
                            target_field=str(name_field.pk),
                            aggregation="first",
                            column_name="first_name",
                        )
                    ],
                )
            ],
        )
        self.goto(url)
        expect(self.locate_field("name")).to_have_value("Ada")

        # 3. Verify the last-value aggregation reads the last row.
        self.configure_country_behavior(
            source_field_name="customers",
            rules=[
                BehaviorRule(
                    events=[BehaviorEvent.CHANGE, BehaviorEvent.INITIAL],
                    actions=[
                        CopyValueFromOneToManyAction(
                            source_field=str(customers_field.pk),
                            target_field=str(name_field.pk),
                            aggregation="last",
                            column_name="first_name",
                        )
                    ],
                )
            ],
        )
        self.goto(url)
        expect(self.locate_field("name")).to_have_value("Grace")
