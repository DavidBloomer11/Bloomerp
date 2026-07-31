from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from bloomerp.models.application_field import ApplicationField
from bloomerp.models.project_management.todo import Todo
from bloomerp.models.users.user_list_view_preference import UserListViewPreference
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.tests.e2e.dataview.test_dataview_e2e_mixin import (
    TestDataviewE2EMixin,
)
from bloomerp.utils.models import get_detail_view_url


class TestDataviewSplitViewE2E(TestDataviewE2EMixin):
    def extendedE2ESetup(self):
        pass

    def test_saves_an_object_from_the_split_view(self):
        """
        Use case: An admin edits a Todo from the dataview split view.
        Expected result: Saving updates the Todo without an HTMX target error.
        """
        # 1. Enable split view and display the Todo title in the table.
        content_type = ContentType.objects.get_for_model(Todo)
        title_field = ApplicationField.get_by_field(Todo, "title")
        preference = PreferenceManager(self.admin_user).get_or_create_selected(
            UserListViewPreference,
            scope={"content_type_id": content_type.pk},
        )
        preference.view_type = "table"
        preference.split_view_enabled = True
        preference.display_fields = {
            **preference.display_fields,
            "table": [title_field.pk],
        }
        preference.save()
        todo = Todo.objects.create(title="Split view original")

        # 2. Open the Todo dataview and load the object into the detail pane.
        self.login_as_admin()
        self.goto_todo_page()
        detail_path = reverse(
            get_detail_view_url(Todo),
            kwargs={"pk": todo.pk},
        )
        title_cell = self.page.locator(
            f'td[data-object-id="{todo.pk}"][data-application-field-name="title"]'
        )
        with self.expect_response_for(detail_path, method="GET"):
            title_cell.dblclick()

        # 3. Change the title and save from inside the split-view detail pane.
        detail_pane = self.page.locator("[data-split-view-detail-pane]")
        detail_pane.locator("#id_title").fill("Split view updated")
        with self.expect_response_for(detail_path, method="POST"):
            detail_pane.get_by_role("button", name="Save", exact=True).click()

        # 4. Verify the object was persisted.
        todo.refresh_from_db()
        self.assertEqual(todo.title, "Split view updated")
