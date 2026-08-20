import re

from django.contrib.contenttypes.models import ContentType
from playwright.sync_api import expect

from bloomerp.models import ApplicationField
from bloomerp.models.project_management.todo import Todo
from bloomerp.models.users.user_list_view_preference import UserListViewPreference
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.tests.e2e.dataview.test_dataview_e2e_mixin import TestDataviewE2EMixin


class TestDataviewDisplayOptionsE2E(TestDataviewE2EMixin):
    def extendedE2ESetup(self) -> None:
        content_type = ContentType.objects.get_for_model(Todo)
        self.title_field = ApplicationField.get_by_field(Todo, "title")
        self.status_field = ApplicationField.get_by_field(Todo, "status")
        self.priority_field = ApplicationField.get_by_field(Todo, "priority")

        preference = PreferenceManager(self.admin_user).get_or_create_selected(
            UserListViewPreference,
            scope={"content_type_id": content_type.id},
        )
        preference.view_type = "table"
        preference.set_visible_field_ids(
            "table",
            [self.title_field.id, self.status_field.id],
        )
        preference.save(update_fields=["view_type", "display_fields"])
        Todo.objects.create(title="Display options regression")
        self.login_as_admin()

    def test_field_buttons_and_columns_update_on_first_click(self):
        """
        Use case: A user changes visible fields from the Todo table display options.
        Expected result: Button colors and table columns reflect every click immediately.
        """
        # 1. Open a Todo table where Title is visible and Priority is hidden.
        self.goto_todo_page()
        table_header = self.page.locator("#data-view-data-section table thead")
        expect(table_header.get_by_role("button", name="Title", exact=True)).to_have_count(1)
        expect(table_header.get_by_role("button", name="Priority", exact=True)).to_have_count(0)

        # 2. Open display options and confirm both buttons' initial colors.
        self.page.get_by_role("button", name="Display").click()
        display_menu = self.page.locator("div[role='menu']:visible").filter(
            has=self.page.locator("button[data-display-options-values*='\"view_type\": \"table\"']")
        )
        title_option = display_menu.get_by_role("button", name="Title", exact=True)
        priority_option = display_menu.get_by_role("button", name="Priority", exact=True)
        expect(title_option).to_have_class(re.compile(r"\bbg-primary-100\b"))
        expect(priority_option).to_have_class(re.compile(r"\bbg-white\b"))

        # 3. Hide Title and verify its button and column change on the first response.
        with self.expect_response_for(
            f"/components/change_data_view_preference/{ContentType.objects.get_for_model(Todo).id}/",
            method="POST",
        ):
            title_option.click()
        expect(title_option).to_have_class(re.compile(r"\bbg-white\b"))
        expect(title_option).not_to_have_class(re.compile(r"\bbg-primary-100\b"))
        expect(table_header.get_by_role("button", name="Title", exact=True)).to_have_count(0)

        # 4. Show Priority and verify its button and column change on the first response.
        with self.expect_response_for(
            f"/components/change_data_view_preference/{ContentType.objects.get_for_model(Todo).id}/",
            method="POST",
        ):
            priority_option.click()
        expect(priority_option).to_have_class(re.compile(r"\bbg-primary-100\b"))
        expect(priority_option).not_to_have_class(re.compile(r"\bbg-white\b"))
        expect(table_header.get_by_role("button", name="Priority", exact=True)).to_have_count(1)
