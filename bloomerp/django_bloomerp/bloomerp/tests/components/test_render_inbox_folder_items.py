from unittest.mock import Mock, patch

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase
from django.utils import timezone

from bloomerp.components.communication.render_inbox_folder_items import (
    INBOX_PAGE_SIZE,
    render_inbox_folder,
)


class RenderInboxFolderItemsTests(SimpleTestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.folder = Mock()
        self.folder.query_items.return_value = list(range(205))

    @patch(
        "bloomerp.components.communication.render_inbox_folder_items.render"
    )
    @patch(
        "bloomerp.components.communication.render_inbox_folder_items.get_object_or_404"
    )
    @patch(
        "bloomerp.components.communication.render_inbox_folder_items."
        "accessible_inbox_folders"
    )
    def test_returns_at_most_one_hundred_items_per_page(
        self,
        accessible_inbox_folders,
        get_object_or_404,
        render,
    ):
        accessible_inbox_folders.return_value = Mock()
        get_object_or_404.return_value = self.folder
        render.return_value = HttpResponse()

        request = self.request_factory.get("/inbox-items/", {"page": 2})
        request.user = Mock(is_authenticated=True)
        render_inbox_folder(request, "folder-id")

        context = render.call_args.args[2]
        self.assertEqual(INBOX_PAGE_SIZE, 100)
        self.assertEqual(context["items"], list(range(100, 200)))
        self.assertEqual(context["page_obj"].number, 2)
        self.assertTrue(context["page_obj"].has_next())

    @patch(
        "bloomerp.components.communication.render_inbox_folder_items.render"
    )
    @patch(
        "bloomerp.components.communication.render_inbox_folder_items.get_object_or_404"
    )
    @patch(
        "bloomerp.components.communication.render_inbox_folder_items."
        "accessible_inbox_folders"
    )
    def test_last_page_contains_remaining_items_and_preserves_filters(
        self,
        accessible_inbox_folders,
        get_object_or_404,
        render,
    ):
        accessible_inbox_folders.return_value = Mock()
        get_object_or_404.return_value = self.folder
        render.return_value = HttpResponse()

        request = self.request_factory.get(
            "/inbox-items/",
            {"page": 3, "q": "invoice", "status": "unread"},
        )
        request.user = Mock(is_authenticated=True)
        render_inbox_folder(request, "folder-id")

        context = render.call_args.args[2]
        self.assertEqual(context["items"], list(range(200, 205)))
        self.assertFalse(context["page_obj"].has_next())
        self.assertEqual(
            context["pagination_querystring"],
            "q=invoice&status=unread",
        )

    def test_inbox_item_renders_received_datetime_with_user_preference(self):
        request = self.request_factory.get("/inbox-items/")
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
