import json

from bs4 import BeautifulSoup
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from bloomerp.field_types import Lookup
from bloomerp.models import (
    ApplicationField,
    FieldPolicy,
    Policy,
    RowPolicy,
    RowPolicyRule,
    File,
)
from bloomerp.models.project_management import Initiative, Todo
from bloomerp.models.users.user import DetailSidebarViewPreference
from bloomerp.models.workspaces.sidebar import Sidebar
from bloomerp.tests.views.crud_test_mixin import CrudViewTestMixin


class TestOverviewView(CrudViewTestMixin):
    create_foreign_models = True
    auto_create_customers = False

    def extendedSetup(self):
        self.customer = self.create_customer("Allowed", "Person", 30)
        self.content_type = ContentType.objects.get_for_model(self.CustomerModel)
        self._ensure_permissions_for_model(self.CustomerModel)
        self.fields_by_name = {
            field.field: field
            for field in ApplicationField.get_for_model(self.CustomerModel)
        }

    def get_url(self):
        return reverse(
            "customers_detail_overview",
            kwargs={"pk": self.customer.pk},
        )

    def _ensure_permissions_for_model(self, model):
        content_type = ContentType.objects.get_for_model(model)
        for perm in model._meta.default_permissions:
            Permission.objects.get_or_create(
                codename=f"{perm}_{model._meta.model_name}",
                content_type=content_type,
                defaults={"name": f"Can {perm} {model._meta.verbose_name}"},
            )

    def grant_page_access(self, user, permission_name: str):
        permission = Permission.objects.get(
            content_type=self.content_type,
            codename=f"{permission_name}_{self.CustomerModel._meta.model_name}",
        )
        user.user_permissions.add(permission)
        user.refresh_from_db()
        return permission

    def group_row_rule(self, row_rule):
        if "conditions" in row_rule:
            return row_rule
        return {
            "connector": "OR",
            "conditions": [row_rule],
        }

    def grant_policy(
        self,
        *,
        user,
        view_field_names,
        change_field_names=None,
        view_row_rules=None,
        change_row_rules=None,
        include_global_view=True,
        include_global_change=True,
    ):
        field_rule = {
            str(self.fields_by_name[field_name].pk): [f"view_{self.CustomerModel._meta.model_name}"]
            for field_name in view_field_names
        }
        for field_name in change_field_names or []:
            field_rule.setdefault(str(self.fields_by_name[field_name].pk), []).append(
                f"change_{self.CustomerModel._meta.model_name}"
            )

        field_policy = FieldPolicy.objects.create(
            content_type=self.content_type,
            name=f"Field policy for {user.username}",
            rule=field_rule,
        )
        row_policy = RowPolicy.objects.create(
            content_type=self.content_type,
            name=f"Row policy for {user.username}",
        )
        for row_rule in view_row_rules or []:
            created_rule = RowPolicyRule.objects.create(
                row_policy=row_policy,
                rule=self.group_row_rule(row_rule),
            )
            created_rule.add_permission(f"view_{self.CustomerModel._meta.model_name}")
        for row_rule in change_row_rules or []:
            created_rule = RowPolicyRule.objects.create(
                row_policy=row_policy,
                rule=self.group_row_rule(row_rule),
            )
            created_rule.add_permission(f"change_{self.CustomerModel._meta.model_name}")

        policy = Policy.objects.create(
            name=f"Policy for {user.username}",
            description="Overview view policy",
            row_policy=row_policy,
            field_policy=field_policy,
        )
        policy.assign_user(user)
        if include_global_view:
            policy.global_permissions.add(self.grant_page_access(user, "view"))
        if include_global_change:
            policy.global_permissions.add(self.grant_page_access(user, "change"))
        return policy

    def test_user_does_not_have_access_if_no_global_permission_to_object(self):
        self.grant_policy(
            user=self.normal_user,
            view_field_names=["first_name", "last_name", "age"],
            view_row_rules=[
                {
                    "application_field_id": str(self.fields_by_name["first_name"].pk),
                    "operator": Lookup.EQUALS.value.id,
                    "value": "Allowed",
                }
            ],
            include_global_view=False,
            include_global_change=False,
        )
        self.client.force_login(self.normal_user)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 403)

    def test_get_renders_only_viewable_fields(self):
        self.grant_policy(
            user=self.normal_user,
            view_field_names=["first_name", "last_name"],
            view_row_rules=[
                {
                    "application_field_id": str(self.fields_by_name["first_name"].pk),
                    "operator": Lookup.EQUALS.value.id,
                    "value": "Allowed",
                }
            ],
            change_row_rules=[
                {
                    "application_field_id": str(self.fields_by_name["first_name"].pk),
                    "operator": Lookup.EQUALS.value.id,
                    "value": "Allowed",
                }
            ],
            include_global_change=False,
        )
        self.client.force_login(self.normal_user)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'data-layout-item-id="{self.fields_by_name["first_name"].pk}"', html=False)
        self.assertContains(response, f'data-layout-item-id="{self.fields_by_name["last_name"].pk}"', html=False)
        self.assertNotContains(response, f'data-layout-item-id="{self.fields_by_name["age"].pk}"', html=False)

    def test_get_disables_view_only_fields(self):
        self.grant_policy(
            user=self.normal_user,
            view_field_names=["first_name", "age"],
            change_field_names=["first_name"],
            view_row_rules=[
                {
                    "application_field_id": str(self.fields_by_name["first_name"].pk),
                    "operator": Lookup.EQUALS.value.id,
                    "value": "Allowed",
                }
            ],
            change_row_rules=[
                {
                    "application_field_id": str(self.fields_by_name["first_name"].pk),
                    "operator": Lookup.EQUALS.value.id,
                    "value": "Allowed",
                }
            ],
        )
        self.client.force_login(self.normal_user)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="age"', html=False)
        self.assertContains(response, "disabled", html=False)

    def test_get_renders_system_fields_disabled_but_keeps_files_enabled(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.get_url())

        self.assertEqual(response.status_code, 200)
        layout_items = {
            str(item.id): item
            for row in response.context["layout"].rows
            for item in row.items
        }
        for field_name in {
            "id",
            "pk",
            "datetime_created",
            "datetime_updated",
            "created_by",
            "updated_by",
            "comments",
        }:
            item = layout_items[str(self.fields_by_name[field_name].pk)]
            self.assertTrue(item.is_visible, field_name)
            self.assertIn("disabled", item.content, field_name)

        files_item = layout_items[str(self.fields_by_name["files"].pk)]
        self.assertTrue(files_item.is_visible)
        self.assertNotIn("disabled", files_item.content)
        self.assertNotContains(response, "You don't have access to this field")

    def test_customer_detail_shows_create_todo_button(self):
        """
        Use case: A regular model detail page renders its side-section actions.
        Expected result: The create-todo action remains available.
        """
        # 1. Authenticate as an admin user with detail access.
        self.client.force_login(self.admin_user)

        # 2. Render a customer detail page.
        response = self.client.get(self.get_url())

        # 3. Verify the create-todo action is still rendered.
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/components/todo/create-todo-for-object/", html=False)

    def test_customer_detail_uses_persisted_sidebar_preference(self):
        """
        Use case: A user previously selected Comments in a detail view sidebar.
        Expected result: The detail view loads Comments before Activity.
        """
        # 1. Persist the user's preferred sidebar panel.
        self.admin_user.detail_sidebar_view_preference = (
            DetailSidebarViewPreference.COMMENTS
        )
        self.admin_user.save(update_fields=["detail_sidebar_view_preference"])
        self.client.force_login(self.admin_user)

        # 2. Render the customer detail page.
        response = self.client.get(self.get_url())

        # 3. Verify the initial sidebar request targets Comments.
        comments_url = reverse(
            "components_comments",
            kwargs={
                "content_type_id": self.content_type.pk,
                "object_id": self.customer.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        sidebar_loader = BeautifulSoup(response.content, "html.parser").select_one(
            "[data-detail-sidebar-loader]"
        )
        self.assertIsNotNone(sidebar_loader)
        self.assertEqual(sidebar_loader.get("hx-get"), comments_url)

    def test_customer_detail_defaults_to_activity_sidebar(self):
        """
        Use case: A user has not selected a detail sidebar panel.
        Expected result: The detail view initially loads Activity.
        """
        # 1. Authenticate as a user with the default sidebar preference.
        self.client.force_login(self.admin_user)

        # 2. Render the customer detail page.
        response = self.client.get(self.get_url())

        # 3. Verify the load-on-render container targets Activity specifically.
        activity_url = (
            f'{reverse("components_activity_log")}'
            f"?content_type_id={self.content_type.pk}&object_id={self.customer.pk}"
        )
        sidebar_loader = BeautifulSoup(response.content, "html.parser").select_one(
            "[data-detail-sidebar-loader]"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(sidebar_loader)
        self.assertEqual(sidebar_loader.get("hx-get"), activity_url)

    def test_todo_detail_hides_create_todo_button(self):
        """
        Use case: A Todo detail page renders its side-section actions.
        Expected result: The create-todo action is hidden to avoid self-referential to-dos.
        """
        # 1. Create a todo and authenticate as an admin user with detail access.
        todo = Todo.objects.create(title="Fix recursive todo action")
        self.client.force_login(self.admin_user)

        # 2. Render the todo detail page.
        response = self.client.get(reverse("todos_detail_overview", kwargs={"pk": todo.pk}))

        # 3. Verify the create-todo action is not rendered.
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "/components/todo/create-todo-for-object/", html=False)

    def test_initiative_detail_hides_create_todo_button(self):
        """
        Use case: An Initiative detail page renders its side-section actions.
        Expected result: The create-todo action is hidden to avoid recursive planning objects.
        """
        # 1. Create an initiative and authenticate as an admin user with detail access.
        initiative = Initiative.objects.create(name="Launch planning")
        self.client.force_login(self.admin_user)

        # 2. Render the initiative detail page.
        response = self.client.get(reverse("initiatives_detail_overview", kwargs={"pk": initiative.pk}))

        # 3. Verify the create-todo action is not rendered.
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "/components/todo/create-todo-for-object/", html=False)

    def test_POST_on_fields_user_has_no_access_to_gives_error_msg(self):
        self.grant_policy(
            user=self.normal_user,
            view_field_names=["first_name", "last_name", "age"],
            change_field_names=["first_name"],
            view_row_rules=[
                {
                    "application_field_id": str(self.fields_by_name["first_name"].pk),
                    "operator": Lookup.EQUALS.value.id,
                    "value": "Allowed",
                }
            ],
            change_row_rules=[
                {
                    "application_field_id": str(self.fields_by_name["first_name"].pk),
                    "operator": Lookup.EQUALS.value.id,
                    "value": "Allowed",
                }
            ],
        )
        self.client.force_login(self.normal_user)

        response = self.client.post(
            self.get_url(),
            {
                "first_name": "Allowed",
                "age": 31,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Permission denied for fields: age", html=False)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.age, 30)

    def test_POST_on_field_with_error_should_give_error_message(self):
        self.grant_policy(
            user=self.normal_user,
            view_field_names=["first_name", "last_name", "age"],
            change_field_names=["age"],
            view_row_rules=[
                {
                    "application_field_id": str(self.fields_by_name["first_name"].pk),
                    "operator": Lookup.EQUALS.value.id,
                    "value": "Allowed",
                }
            ],
            change_row_rules=[
                {
                    "application_field_id": str(self.fields_by_name["first_name"].pk),
                    "operator": Lookup.EQUALS.value.id,
                    "value": "Allowed",
                }
            ],
        )
        self.client.force_login(self.normal_user)

        response = self.client.post(
            self.get_url(),
            {
                "age": "not-a-number",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'data-layout-item-id="{self.fields_by_name["age"].pk}"', html=False)
        self.assertContains(response, "border-red-500", html=False)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.age, 30)

    def test_post_updates_object_when_permissions_allow_change(self):
        self.grant_policy(
            user=self.normal_user,
            view_field_names=["first_name", "last_name", "age"],
            change_field_names=["first_name"],
            view_row_rules=[
                {
                    "application_field_id": str(self.fields_by_name["first_name"].pk),
                    "operator": Lookup.EQUALS.value.id,
                    "value": "Allowed",
                }
            ],
            change_row_rules=[
                {
                    "application_field_id": str(self.fields_by_name["first_name"].pk),
                    "operator": Lookup.EQUALS.value.id,
                    "value": "Allowed",
                }
            ],
        )
        self.client.force_login(self.normal_user)

        response = self.client.post(
            self.get_url(),
            {
                "first_name": "Allowed Updated",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.first_name, "Allowed Updated")

    def test_shared_layout_available_fields_route_returns_detail_items(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(
            "/components/workspaces/detail_layout_available_fields/",
            {
                "content_type_id": self.content_type.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-layout-item-id", html=False)

    
