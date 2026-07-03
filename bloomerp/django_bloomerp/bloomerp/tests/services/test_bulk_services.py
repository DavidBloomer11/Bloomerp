from unittest.mock import patch

from bloomerp.services.bulk_services import BulkCrudService
from bloomerp.tests.base import BaseBloomerpModelTestCase


class TestBulkCrudService(BaseBloomerpModelTestCase):
    auto_create_customers = False

    def test_process_rows_sends_completion_message_to_user(self):
        """
        Use case: A prepared bulk upload finishes processing rows for a user.
        Expected result: The user receives a success toast over the realtime channel.
        """
        # 1. Process a prepared bulk upload row for the initiating user.
        service = BulkCrudService(model=self.CustomerModel, user=self.admin_user)
        rows = [
            {
                "first_name": "Alice",
                "last_name": "Example",
                "age": "35",
            }
        ]

        with patch("bloomerp.utils.realtime.send_user_message") as send_user_message:
            created_count = service._process_rows_impl(
                rows=rows,
                fields=["first_name", "last_name", "age"],
            )

        # 2. Confirm the user receives a websocket toast after the upload completes.
        self.assertEqual(created_count, 1)
        send_user_message.assert_called_once_with(
            self.admin_user.pk,
            payload={
                "type": "toast",
                "message": "Bulk upload completed. Created 1 object(s).",
                "level": "success",
            },
        )
