from unittest.mock import Mock

from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase
from django.utils import timezone


class InboxItemTemplateTests(SimpleTestCase):
    def test_received_datetime_uses_the_user_preference(self):
        request = RequestFactory().get("/inbox-items/")
        request.user = Mock(datetime_view_preference="Y-m-d H:i")
        item = Mock(
            id="item-id",
            icon="",
            is_read=True,
            actor="Sender",
            title="Subject",
            datetime_received=timezone.datetime(
                2026,
                8,
                25,
                14,
                30,
                tzinfo=timezone.get_current_timezone(),
            ),
            snippet="Preview",
        )

        html = render_to_string(
            "cotton/features/communication/inbox_item.html",
            {"item": item},
            request=request,
        )

        self.assertIn("2026-08-25 14:30", html)
