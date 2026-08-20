from urllib.parse import urlencode

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from playwright.sync_api import Locator, expect

from bloomerp.models import ApplicationField
from bloomerp.models.base_bloomerp_model import FieldLayout, LayoutItem, LayoutRow
from bloomerp.models.users.user_object_layout_preference import (
    UserObjectLayoutPreference,
)
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.tests.e2e.base import BaseE2ETestCase
from bloomerp.tests.e2e.generic.test_crud_mixin import TestCrudE2EMixin
from bloomerp.utils.models import get_create_view_url


class TestOneToManyWidgetE2E(TestCrudE2EMixin, BaseE2ETestCase):
    create_foreign_models = True
    inline_fields = [
        "first_name",
        "customer_type",
        "age",
        "date_joined",
        "description",
    ]

    def extendedE2ESetup(self) -> None:
        """Expose Country.customers as an editable one-to-many test widget."""
        content_type = ContentType.objects.get_for_model(self.CountryModel)
        customers_field = ApplicationField.get_for_model(self.CountryModel).get(
            field="customers"
        )
        name_field = ApplicationField.get_for_model(self.CountryModel).get(field="name")
        preference = PreferenceManager(self.admin_user).get_or_create_selected(
            UserObjectLayoutPreference,
            scope={"content_type_id": content_type.pk},
        )
        preference.layout = FieldLayout(
            rows=[
                LayoutRow(
                    columns=1,
                    title="Customers",
                    items=[
                        LayoutItem(
                            id=customers_field.pk,
                            config={
                                "inline_fields": self.inline_fields,
                                "show_totals": True,
                            },
                        ),
                        LayoutItem(id=name_field.pk, colspan=1),
                    ],
                )
            ]
        ).model_dump()
        preference.save(update_fields=["layout"])
        self.customer_type = self.CustomerTypeModel.objects.get(name="Retail")
        self.CustomerModel._meta.get_field("age").default = 42
        self.login_as_admin()

    def get_base_url(self) -> str:
        return reverse(get_create_view_url(model=self.CountryModel))

    def get_url_with_rows(self, rows: list[dict[str, object]]) -> str:
        query = {
            f"customers__{row_index}__{field_name}": value
            for row_index, row in enumerate(rows)
            for field_name, value in row.items()
        }
        return f"{self.get_base_url()}?{urlencode(query)}"

    def get_widget(self) -> Locator:
        return self.page.locator('[data-one-to-many-name="customers"]')

    def get_rows(self, *, visible: bool = False) -> Locator:
        selector = "[data-one-to-many-row]:not([data-one-to-many-deleted])"
        if visible:
            selector += ":visible"
        return self.get_widget().locator(selector)

    def get_column_values(self, field_name: str) -> list[str]:
        controls = self.get_rows().locator(
            f'[data-one-to-many-cell="{field_name}"] input'
        )
        return [control.input_value() for control in controls.all()]

    def open_column_actions(self, field_name: str) -> Locator:
        actions = self.get_widget().locator(
            f'[data-one-to-many-column-actions="{field_name}"]'
        )
        actions.get_by_role("button", name="Column actions").click()
        return actions

    # ---------------------------------------
    # Test row Actions
    # ---------------------------------------
    def test_trash_icon_removes_row(self):
        """
        Use case: Remove an individual row using its trash action.
        Expected result: The selected row disappears and the empty state is shown.
        """
        # 1. Open a country form with one unsaved customer row.
        self.goto(self.get_url_with_rows([{"first_name": "Ada"}]))
        expect(self.get_rows()).to_have_count(1)

        # 2. Verify row hover does not expose every action tooltip.
        row = self.get_rows().first
        remove_tooltip = row.get_by_text("Remove row", exact=True)
        row.locator('[data-one-to-many-cell="first_name"] input').hover()
        expect(remove_tooltip).to_be_hidden()

        # 3. Hover the trash icon, then remove the row.
        remove_button = row.get_by_role("button", name="Remove row")
        remove_button.hover()
        expect(remove_tooltip).to_be_visible()
        remove_button.click()

        # 4. Verify the row was removed and the empty state replaced it.
        expect(self.get_rows()).to_have_count(0)
        expect(self.get_widget().get_by_text("No related objects found.")).to_be_visible()

    def test_clone_icon_clones_row(self):
        """
        Use case: Clone an individual row using its clone action.
        Expected result: A new unsaved row preserves native and foreign-key values.
        """
        # 1. Open a country form with one complete customer row.
        self.goto(
            self.get_url_with_rows(
                [
                    {
                        "first_name": "Ada",
                        "customer_type": self.customer_type.pk,
                        "age": 30,
                        "date_joined": "2026-08-04",
                    }
                ]
            )
        )

        # 2. Clone the row.
        self.get_rows().get_by_role("button", name="Clone row").click()

        # 3. Verify a second row exists with copied values.
        expect(self.get_rows()).to_have_count(2)
        self.assertEqual(self.get_column_values("first_name"), ["Ada", "Ada"])
        self.assertEqual(self.get_column_values("age"), ["30", "30"])
        self.assertEqual(
            self.get_column_values("date_joined"),
            ["2026-08-04", "2026-08-04"],
        )
        customer_type_inputs = self.get_rows().locator(
            '[data-one-to-many-cell="customer_type"] '
            'input[type="hidden"][data-generated="true"]'
        )
        expect(customer_type_inputs).to_have_count(2)
        self.assertEqual(
            [control.input_value() for control in customer_type_inputs.all()],
            [str(self.customer_type.pk), str(self.customer_type.pk)],
        )
        expect(
            self.get_rows().nth(1).locator(
                '[data-one-to-many-cell="customer_type"] .foreign-field-selected'
            )
        ).to_contain_text("Retail")

    def test_add_and_clone_rows_use_column_defaults(self):
        """
        Use case: Add and clone rows when a related column has a model default.
        Expected result: New rows use the default while clones preserve explicit values.
        """
        # 1. Open a form with a prefilled row that omits the defaulted age.
        self.goto(self.get_url_with_rows([{"first_name": "Ada"}]))
        self.assertEqual(self.get_column_values("age"), ["42"])

        # 2. Add a row and verify the default is applied to it.
        self.get_widget().get_by_role("button", name="Add row").click()
        self.assertEqual(self.get_column_values("age"), ["42", "42"])

        # 3. Change the first value and clone the row.
        self.get_rows().nth(0).locator('[data-one-to-many-cell="age"] input').fill("30")
        self.get_rows().nth(0).get_by_role("button", name="Clone row").click()

        # 4. Verify cloning preserves the explicit value and does not replace it with the default.
        self.assertEqual(self.get_column_values("age"), ["30", "42", "30"])

    def test_text_editors_update_their_own_one_to_many_rows(self):
        """
        Use case: Edit text-editor fields in two server-rendered one-to-many rows.
        Expected result: Each editor updates only the hidden input in its own row.
        """
        # 1. Open a country form with two text-editor rows already rendered.
        self.goto(
            self.get_url_with_rows(
                [
                    {"description": "First customer description"},
                    {"description": "Second customer description"},
                ]
            )
        )
        expect(self.get_rows()).to_have_count(2)

        # 2. Enter different content in each row's text editor.
        first_editor = self.get_rows().nth(0).locator(
            '[data-one-to-many-cell="description"] .bloomerp-text-editor'
        )
        second_editor = self.get_rows().nth(1).locator(
            '[data-one-to-many-cell="description"] .bloomerp-text-editor'
        )
        first_editor.focus()
        expect(first_editor).to_be_focused()
        second_editor_wrapper = self.get_rows().nth(1).locator(
            '[data-one-to-many-cell="description"] '
            '[bloomerp-component="bloomerp-text-editor"]'
        )
        second_editor_wrapper.dispatch_event("click")
        expect(second_editor).to_be_focused()
        expect(first_editor).not_to_be_focused()
        first_editor.fill("Updated first customer description")
        second_editor.fill("Updated second customer description")

        # 3. Verify each editor synchronized its own row's form input.
        first_value = self.get_rows().nth(0).locator(
            '[data-one-to-many-cell="description"] [data-text-editor-input="true"]'
        ).input_value()
        second_value = self.get_rows().nth(1).locator(
            '[data-one-to-many-cell="description"] [data-text-editor-input="true"]'
        ).input_value()
        self.assertIn("Updated first customer description", first_value)
        self.assertNotIn("Updated second customer description", first_value)
        self.assertIn("Updated second customer description", second_value)
        self.assertNotIn("Updated first customer description", second_value)

    def test_preview_icon_previews_and_opens_persisted_row(self):
        """
        Use case: Hover and click the preview action for a saved related object.
        Expected result: Hovering loads its object preview and clicking opens its detail view.
        """
        # 1. Attach an existing customer to a country and open the country form.
        country = self.CountryModel.objects.get(name="Belgium")
        customer = self.CustomerModel.objects.first()
        customer.country = country
        customer.save(update_fields=["country"])
        self.goto(country.get_absolute_url())

        # 2. Hover the saved row's magnifying glass.
        preview_link = self.get_rows().first.get_by_role("link", name="View row")
        expect(preview_link).to_be_visible()
        preview_link.hover()

        # 3. Verify the shared object-preview component is loaded.
        preview = self.page.locator(".foreign-field-preview-tooltip")
        expect(preview).to_be_visible(timeout=5_000)
        expect(preview).to_contain_text(customer.first_name, timeout=5_000)

        # 4. Click the magnifying glass and verify navigation to the customer.
        expect(preview_link).to_have_attribute("href", customer.get_absolute_url())
        preview_link.click()
        self.assertTrue(
            self.page.url.endswith(customer.get_absolute_url()),
            self.page.url,
        )

    def test_navigate_button_when_one_to_many_row_has_id(self):
        """
        UC: We want to be able to navigate to a row when a one-to-many widget has a row with an ID
        
        Expected Result: 
            - Hovering over the row launches the object preview
            - Clicking the navigate button takes you to the object detail view
        """
        #1. step_1
    
    #---------------------------------------
    # Test Pagination
    #---------------------------------------
    def test_pagination(self):
        """
        Use case: Navigate a one-to-many widget containing more than ten rows.
        Expected result: Ten rows are shown per page and the next page is reachable.
        """
        # 1. Open a country form with twenty customer rows.
        rows = [{"first_name": f"Customer {index}"} for index in range(20)]
        self.goto(self.get_url_with_rows(rows))

        # 2. Verify the first page shows ten rows and the correct page status.
        expect(self.get_rows()).to_have_count(20)
        expect(self.get_rows(visible=True)).to_have_count(10)
        expect(self.get_widget().locator("[data-one-to-many-page-status]")).to_have_text(
            "1 / 2"
        )
        expect(
            self.get_rows(visible=True).first.locator(
                '[data-one-to-many-cell="first_name"] input'
            )
        ).to_have_value("Customer 0")

        # 3. Move to page two and verify the next ten rows are displayed.
        self.get_widget().locator("[data-one-to-many-next-page]").click()
        expect(self.get_rows(visible=True)).to_have_count(10)
        expect(self.get_widget().locator("[data-one-to-many-page-status]")).to_have_text(
            "2 / 2"
        )
        expect(
            self.get_rows(visible=True).first.locator(
                '[data-one-to-many-cell="first_name"] input'
            )
        ).to_have_value("Customer 10")

    #---------------------------------------
    # Test Sorting
    #---------------------------------------
    def test_sorting_on_non_numeric_column(self):
        """
        Use case: Sort a text column from its column actions menu.
        Expected result: Rows can be sorted ascending and then descending by text.
        """
        # 1. Open three rows in an intentionally unsorted order.
        self.goto(
            self.get_url_with_rows(
                [{"first_name": "B"}, {"first_name": "A"}, {"first_name": "C"}]
            )
        )

        # 2. Sort the first-name column ascending.
        self.open_column_actions("first_name").get_by_role(
            "button", name="Sort ascending"
        ).click()
        self.assertEqual(self.get_column_values("first_name"), ["A", "B", "C"])

        # 3. Sort the same column descending.
        self.open_column_actions("first_name").get_by_role(
            "button", name="Sort descending"
        ).click()
        self.assertEqual(self.get_column_values("first_name"), ["C", "B", "A"])

    def test_sorting_on_numeric_column(self):
        """
        Use case: Sort a numeric inline column from its column actions menu.
        Expected result: Numeric values are ordered by magnitude rather than as text.
        """
        # 1. Open three customer rows with unsorted ages.
        self.goto(self.get_url_with_rows([{"age": 30}, {"age": 20}, {"age": 40}]))

        # 2. Sort ages ascending and verify numeric order.
        self.open_column_actions("age").get_by_role(
            "button", name="Sort ascending"
        ).click()
        self.assertEqual(self.get_column_values("age"), ["20", "30", "40"])

        # 3. Sort ages descending and verify the reverse order.
        self.open_column_actions("age").get_by_role(
            "button", name="Sort descending"
        ).click()
        self.assertEqual(self.get_column_values("age"), ["40", "30", "20"])

    #---------------------------------------
    # Test Autofill
    #---------------------------------------
    def test_autofill_non_numeric_column(self):
        """
        Use case: Autofill a text column from the value in its first row.
        Expected result: Every subsequent row receives the first text value.
        """
        # 1. Open three rows where only the first name is populated.
        self.goto(
            self.get_url_with_rows(
                [{"first_name": "Ada"}, {"first_name": ""}, {"first_name": ""}]
            )
        )

        # 2. Use the direct Autofill action for the text column.
        self.open_column_actions("first_name").get_by_role(
            "button", name="Autofill", exact=True
        ).click()

        # 3. Verify the first value was copied to the remaining rows.
        self.assertEqual(self.get_column_values("first_name"), ["Ada", "Ada", "Ada"])

    def test_autofill_numeric_column_increment(self):
        """
        Use case: Autofill a numeric column by incrementing its first value.
        Expected result: Each subsequent row increases the first value by one.
        """
        # 1. Open three rows where only the first age is populated.
        self.goto(self.get_url_with_rows([{"age": 20}, {"age": ""}, {"age": ""}]))

        # 2. Open the numeric Autofill submenu and choose increment.
        actions = self.open_column_actions("age")
        actions.get_by_role("button", name="Autofill", exact=True).click()
        self.page.get_by_role("button", name="Increment first value").click()

        # 3. Verify the generated numeric sequence.
        self.assertEqual(self.get_column_values("age"), ["20", "21", "22"])

    def test_autofill_date_column_increment(self):
        """
        Use case: Autofill a date column by incrementing its first value.
        Expected result: Each subsequent row advances the first date by one day.
        """
        # 1. Open three rows where only the first join date is populated.
        self.goto(
            self.get_url_with_rows(
                [
                    {"date_joined": "2026-08-04"},
                    {"date_joined": ""},
                    {"date_joined": ""},
                ]
            )
        )

        # 2. Open the date Autofill submenu and choose increment.
        actions = self.open_column_actions("date_joined")
        actions.get_by_role("button", name="Autofill", exact=True).click()
        self.page.get_by_role("button", name="Increment first value").click()

        # 3. Verify the generated daily sequence.
        self.assertEqual(
            self.get_column_values("date_joined"),
            ["2026-08-04", "2026-08-05", "2026-08-06"],
        )

    #---------------------------------------
    # Test Totals
    #---------------------------------------
    def test_totals_on_numeric_column(self):
        """
        Use case: Display totals when the one-to-many layout enables them.
        Expected result: The footer shows the sum of every numeric column value.
        """
        # 1. Open three rows while show_totals is enabled in the field layout.
        self.goto(self.get_url_with_rows([{"age": 30}, {"age": 20}, {"age": 40}]))

        # 2. Verify the age total is rendered beneath the widget.
        expect(self.get_widget().locator('[data-one-to-many-total="age"]')).to_have_text(
            "90"
        )

    #---------------------------------------
    # Test Reset Button
    #---------------------------------------
    def test_reset_button_preserves_foreign_keys_if_initial_state(self):
        """
        Use case: Reset an edited one-to-many row containing a foreign key.
        Expected result: Native and foreign-key values return to their initial state.
        """
        # 1. Open a row containing both a native value and a foreign key.
        self.goto(
            self.get_url_with_rows(
                [
                    {
                        "first_name": "Ada",
                        "customer_type": self.customer_type.pk,
                    }
                ]
            )
        )

        # 2. Change a value inside the one-to-many row.
        first_name = self.get_rows().first.locator(
            '[data-one-to-many-cell="first_name"] input'
        )
        first_name.fill("Changed")
        expect(first_name).to_have_value("Changed")

        # 3. Click the reset button.
        self.press_reset_button()

        # 4. Verify both the native and foreign-key values were restored.
        expect(self.get_rows()).to_have_count(1)
        expect(
            self.get_rows().first.locator(
                '[data-one-to-many-cell="first_name"] input'
            )
        ).to_have_value("Ada")
        customer_type_cell = self.get_rows().first.locator(
            '[data-one-to-many-cell="customer_type"]'
        )
        expect(
            customer_type_cell.locator(
                'input[type="hidden"][data-generated="true"]'
            )
        ).to_have_value(str(self.customer_type.pk))
        expect(customer_type_cell.locator(".foreign-field-selected")).to_contain_text(
            "Retail"
        )
        
    #---------------------------------------
    # Test Reset Button
    #---------------------------------------
