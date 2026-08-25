from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from bloomerp.models import User, Workspace


class HomeViewTests(TestCase):
    def setUp(self) -> None:
        self.owner = User.objects.create_user(
            username="home-workspace-owner",
            password="testpass123",
            is_staff=True,
        )
        self.user = User.objects.create_user(
            username="home-workspace-user",
            password="testpass123",
            is_staff=True,
        )
        self.client.force_login(self.user)
        self.url = reverse("bloomerp_home_view")
        self.module = SimpleNamespace(
            id="staff",
            name="Staff",
            description="Staff module",
            icon="fa-users",
        )

    def create_workspace(self, **kwargs) -> Workspace:
        return Workspace.objects.create(
            layout={"rows": [{"title": "Home", "columns": 4, "items": []}]},
            **kwargs,
        )

    def get_home(self, query: str = ""):
        return self.client.get(
            f"{self.url}{query}",
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="main-content",
        )

    @patch("bloomerp.views.workspaces.home.module_registry.get_root_modules")
    def test_home_without_general_workspace_shows_modules(self, get_root_modules) -> None:
        """
        Use case: A user without a general workspace opens the home view.
        Expected result: The existing module selector remains available.
        """
        # 1. Configure a visible root module for the selector.
        get_root_modules.return_value = [self.module]

        # 2. Open the home view and verify the fallback module selector.
        response = self.get_home()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Staff module")
        self.assertNotContains(response, "Select module")

    @patch("bloomerp.views.workspaces.home.module_registry.get_root_modules")
    def test_module_workspace_does_not_replace_home_view(self, get_root_modules) -> None:
        """
        Use case: A user has a selected workspace scoped to the Staff module.
        Expected result: Home still shows modules because module and home selections are independent.
        """
        # 1. Create a selected workspace in the Staff module scope only.
        self.create_workspace(
            user=self.user,
            name="Staff workspace",
            module_id="staff",
            selected=True,
        )
        get_root_modules.return_value = [self.module]

        # 2. Open home and verify the Staff module card is rendered instead.
        response = self.get_home()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Staff module")
        self.assertNotContains(response, "Staff workspace")

    @patch("bloomerp.views.workspaces.home.module_registry.get_root_modules")
    def test_selected_general_workspace_replaces_module_selector(self, get_root_modules) -> None:
        """
        Use case: A user has selected a general workspace as their home preference.
        Expected result: Home renders that workspace with an option to select a module.
        """
        # 1. Create the user's selected general workspace.
        self.create_workspace(
            user=self.user,
            name="My home workspace",
            module_id=None,
            selected=True,
        )
        get_root_modules.return_value = [self.module]

        # 2. Open home and verify the workspace replaces the module cards.
        response = self.get_home()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My home workspace")
        self.assertContains(response, "Select module")
        self.assertNotContains(response, "Staff module")

    def test_shared_initial_default_becomes_user_home_workspace(self) -> None:
        """
        Use case: An administrator shares a general workspace as an initial default.
        Expected result: The recipient sees it at home and receives a selected live reference.
        """
        # 1. Create and share an initial-default general workspace.
        shared = self.create_workspace(
            user=self.owner,
            name="Timesheet home",
            module_id=None,
            initial_default=True,
        )
        shared.shared_with_users.add(self.user)

        # 2. Open home and verify the shared workspace is selected and rendered.
        response = self.get_home()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Timesheet home")
        reference = Workspace.objects.get(user=self.user, source_object=shared)
        self.assertTrue(reference.selected)

    @patch("bloomerp.views.workspaces.home.module_registry.get_root_modules")
    def test_select_module_query_temporarily_shows_modules(self, get_root_modules) -> None:
        """
        Use case: A user with a home workspace chooses Select module.
        Expected result: The module selector is rendered without changing their preference.
        """
        # 1. Create the user's selected general workspace.
        workspace = self.create_workspace(
            user=self.user,
            name="My home workspace",
            module_id=None,
            selected=True,
        )
        get_root_modules.return_value = [self.module]

        # 2. Request the module-selector override and verify selection is preserved.
        response = self.get_home("?modules=1")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Staff module")
        self.assertNotContains(response, "My home workspace")
        workspace.refresh_from_db()
        self.assertTrue(workspace.selected)

    @patch("bloomerp.views.workspaces.home.module_registry.get_root_modules")
    def test_revoked_shared_workspace_falls_back_to_modules(self, get_root_modules) -> None:
        """
        Use case: Access to a previously selected shared home workspace is revoked.
        Expected result: Home no longer renders it and safely falls back to modules.
        """
        # 1. Select a shared initial-default workspace, then revoke its sharing.
        shared = self.create_workspace(
            user=self.owner,
            name="Revoked home",
            module_id=None,
            initial_default=True,
        )
        shared.shared_with_users.add(self.user)
        self.get_home()
        shared.shared_with_users.remove(self.user)
        get_root_modules.return_value = [self.module]

        # 2. Reopen home and verify inaccessible workspace content is not rendered.
        response = self.get_home()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Staff module")
        self.assertNotContains(response, "Revoked home")
