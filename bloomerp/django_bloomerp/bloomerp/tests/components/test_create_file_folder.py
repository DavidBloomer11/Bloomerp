from types import SimpleNamespace

from django.test import TestCase
from django.urls import reverse

from bloomerp.models import FileFolder
from bloomerp.models.files.file import _create_folder_endpoint
from bloomerp.tests.utils.users import create_admin, create_normal_user


class CreateFileFolderComponentTests(TestCase):
    def setUp(self) -> None:
        self.admin_user = create_admin()
        self.normal_user = create_normal_user()
        self.url = reverse("components_create_folder")

    def test_get_renders_create_folder_modal_form(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{self.url}"', html=False)
        self.assertContains(response, 'name="name"', html=False)

    def test_post_creates_folder_and_refreshes_page(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(self.url, {"name": "Contracts"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("HX-Refresh"), "true")
        folder = FileFolder.objects.get(name="Contracts")
        self.assertIsNone(folder.parent)
        self.assertEqual(folder.created_by, self.admin_user)

    def test_post_creates_child_in_submitted_browser_folder(self):
        parent = FileFolder.objects.create(
            name="Parent",
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        self.client.force_login(self.admin_user)

        response = self.client.post(
            self.url,
            {"name": "Child", "folder_id": parent.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            FileFolder.objects.filter(name="Child", parent=parent).exists()
        )

    def test_post_rejects_user_without_add_folder_permission(self):
        self.client.force_login(self.normal_user)

        response = self.client.post(self.url, {"name": "Forbidden"})

        self.assertEqual(response.status_code, 403)
        self.assertFalse(FileFolder.objects.filter(name="Forbidden").exists())

    def test_dataview_action_preserves_browser_querystring(self):
        endpoint = _create_folder_endpoint(
            SimpleNamespace(querystring="folder=12&object_id=34")
        )

        self.assertEqual(endpoint, f"{self.url}?folder=12&object_id=34")

    def test_folder_model_action_renames_folder_through_modal(self):
        folder = FileFolder.objects.create(
            name="Before",
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        self.client.force_login(self.admin_user)
        url = reverse(
            "components_files_rename_folder",
            kwargs={"folder_id": folder.pk},
        )

        get_response = self.client.get(url)
        post_response = self.client.post(url, {"name": "After"})

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(post_response.headers.get("HX-Refresh"), "true")
        folder.refresh_from_db()
        self.assertEqual(folder.name, "After")

    def test_folder_model_action_deletes_folder_through_modal(self):
        folder = FileFolder.objects.create(
            name="Disposable",
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        self.client.force_login(self.admin_user)
        url = reverse(
            "components_files_delete_folder",
            kwargs={"folder_id": folder.pk},
        )

        get_response = self.client.get(url)
        post_response = self.client.post(url)

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(post_response.headers.get("HX-Refresh"), "true")
        self.assertFalse(FileFolder.objects.filter(pk=folder.pk).exists())
