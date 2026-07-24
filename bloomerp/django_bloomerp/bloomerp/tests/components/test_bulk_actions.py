from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from bloomerp.tests.base import BaseBloomerpModelTestCase


class TestBulkActionsComponent(BaseBloomerpModelTestCase):
    auto_create_customers = False

    def test_bulk_actions_modal_offers_delete_for_permitted_objects(self):
        """
        Use case: A permitted user opens bulk actions for a selected object.
        Expected result: The modal offers to delete that object.
        """
        # 1. Create an object and sign in as a superuser.
        customer = self.create_customer("Selected", "Customer", 30)
        self.client.force_login(self.admin_user)
        content_type = ContentType.objects.get_for_model(self.CustomerModel)

        # 2. Open bulk actions for the selected object.
        url = reverse(
            "components_bulk_actions",
            kwargs={"content_type_id": content_type.pk},
        )
        response = self.client.get(
            url,
            {
                "selection": "selected",
                "object_ids": str(customer.pk),
            },
        )

        # 3. Confirm the destructive action reflects the selected count.
        self.assertContains(response, "Delete 1 object(s)")
        self.assertContains(
            response,
            'name="action" value="bulk_delete"',
            html=False,
        )

    @patch(
        "bloomerp.utils.async_utils.is_celery_available",
        return_value=False,
    )
    def test_bulk_delete_post_deletes_selected_objects(self, _is_celery_available):
        """
        Use case: A permitted user submits bulk delete for a selected object.
        Expected result: The selected object is deleted and the dataview refresh event is returned.
        """
        # 1. Create selected and unselected objects and sign in as a superuser.
        selected = self.create_customer("Selected", "Customer", 30)
        unselected = self.create_customer("Unselected", "Customer", 31)
        self.client.force_login(self.admin_user)
        content_type = ContentType.objects.get_for_model(self.CustomerModel)
        base_url = reverse(
            "components_bulk_actions",
            kwargs={"content_type_id": content_type.pk},
        )
        url = f"{base_url}?selection=selected&object_ids={selected.pk}"

        # 2. Submit the destructive bulk action.
        response = self.client.post(
            url,
            {"action": "bulk_delete"},
            HTTP_HX_REQUEST="true",
        )

        # 3. Confirm only the selected object was deleted and refresh was requested.
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.CustomerModel.objects.filter(pk=selected.pk).exists())
        self.assertTrue(self.CustomerModel.objects.filter(pk=unselected.pk).exists())
        self.assertIn("bloomerp:bulk-action-complete", response["HX-Trigger-After-Swap"])

    def test_bulk_delete_requires_a_bulk_permission_action(self):
        """
        Use case: A bulk-action POST omits its action or supplies a non-bulk permission.
        Expected result: Each request is rejected without deleting objects.
        """
        # 1. Create a selected object and sign in as a superuser.
        selected = self.create_customer("Selected", "Customer", 30)
        self.client.force_login(self.admin_user)
        content_type = ContentType.objects.get_for_model(self.CustomerModel)
        base_url = reverse(
            "components_bulk_actions",
            kwargs={"content_type_id": content_type.pk},
        )
        url = f"{base_url}?selection=selected&object_ids={selected.pk}"

        # 2. Submit without a permission and with a non-bulk permission.
        for action in (None, "view"):
            with self.subTest(action=action):
                response = self.client.post(
                    url,
                    {"action": action} if action else {},
                    HTTP_HX_REQUEST="true",
                )
                self.assertEqual(response.status_code, 400)

        # 3. Confirm the object remains.
        self.assertTrue(self.CustomerModel.objects.filter(pk=selected.pk).exists())
