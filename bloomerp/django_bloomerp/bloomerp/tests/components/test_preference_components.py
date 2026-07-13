from django.test import TestCase
from django.urls import reverse

from bloomerp.models import Sidebar, User


class DeletePreferenceComponentTests(TestCase):
    def setUp(self) -> None:
        self.owner = User.objects.create_user(
            username="preference-owner",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            username="preference-other",
            password="testpass123",
        )
        self.selected = Sidebar.objects.create(
            user=self.owner,
            name="Primary",
            selected=True,
        )
        self.deletable = Sidebar.objects.create(
            user=self.owner,
            name="Temporary",
            selected=False,
        )
        self.delete_url = reverse(
            "components_delete_preference",
            kwargs={"model": "Sidebar", "preference_id": self.deletable.pk},
        )

    def test_select_preference_renders_owner_delete_button(self) -> None:
        self.client.force_login(self.owner)

        response = self.client.get(
            reverse(
                "components_select_preference",
                kwargs={"model": "Sidebar"},
            ),
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'data-delete-preference="{self.deletable.pk}"',
            html=False,
        )
        self.assertContains(
            response,
            reverse(
                "components_delete_preference",
                kwargs={"model": "Sidebar", "preference_id": "REPLACE_WITH_ID"},
            ),
            html=False,
        )

    def test_delete_preference_get_renders_confirmation_form(self) -> None:
        self.client.force_login(self.owner)

        response = self.client.get(self.delete_url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'action="{self.delete_url}"', html=False)
        self.assertContains(response, 'hx-post="', html=False)
        self.assertContains(response, "Temporary")
        self.assertContains(response, "This action cannot be undone.")
        self.assertContains(response, "Delete")
        self.assertTrue(Sidebar.objects.filter(pk=self.deletable.pk).exists())

    def test_delete_preference_rejects_unsupported_method(self) -> None:
        self.client.force_login(self.owner)

        response = self.client.put(self.delete_url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Sidebar.objects.filter(pk=self.deletable.pk).exists())

    def test_owner_can_delete_preference(self) -> None:
        self.client.force_login(self.owner)

        response = self.client.post(self.delete_url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["HX-Refresh"], "true")
        self.assertFalse(Sidebar.objects.filter(pk=self.deletable.pk).exists())

    def test_other_user_cannot_delete_preference(self) -> None:
        self.client.force_login(self.other_user)

        response = self.client.post(self.delete_url, HTTP_HX_REQUEST="true")

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Sidebar.objects.filter(pk=self.deletable.pk).exists())

    def test_owner_cannot_delete_derived_reference(self) -> None:
        source = Sidebar.objects.create(
            user=self.other_user,
            name="Shared",
        )
        reference = Sidebar.objects.create(
            user=self.owner,
            name="Reference",
            source_object=source,
        )
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse(
                "components_delete_preference",
                kwargs={"model": "Sidebar", "preference_id": reference.pk},
            ),
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Sidebar.objects.filter(pk=reference.pk).exists())
