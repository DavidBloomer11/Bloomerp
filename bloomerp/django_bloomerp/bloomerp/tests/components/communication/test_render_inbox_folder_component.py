from unittest.mock import Mock, patch

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from bloomerp.components.communication.render_inbox_folder_items import (
    INBOX_PAGE_SIZE,
    render_inbox_folder,
)
class TestRenderInboxFolderPagination(SimpleTestCase):
    """Tests pagination internals with a mocked inbox provider."""

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
