from unittest.mock import Mock, patch

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from bloomerp.components.communication.render_inbox_item import render_inbox_item


class RenderInboxItemTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get("/inbox-item/")
        self.request.user = Mock(is_authenticated=True)

    @patch("bloomerp.components.communication.render_inbox_item.Inbox")
    @patch("bloomerp.components.communication.render_inbox_item.render")
    @patch("bloomerp.components.communication.render_inbox_item.get_object_or_404")
    @patch(
        "bloomerp.components.communication.render_inbox_item."
        "accessible_inbox_items"
    )
    def test_already_read_item_does_not_repeat_provider_mark_as_read(
        self,
        accessible_inbox_items,
        get_object_or_404,
        render,
        inbox,
    ):
        item_type = Mock(actions=[])
        item_type.on_render.return_value = "Stored sent email"
        item = Mock(is_read=True)
        item.get_inbox_item_type.return_value = item_type
        get_object_or_404.return_value = item
        render.return_value = HttpResponse()
        inbox.get_unread_count_for_user.return_value = 0

        render_inbox_item(self.request, "item-id")

        item_type.on_render.assert_called_once_with(item, self.request)
        item_type.on_mark_as_read.assert_not_called()

    @patch("bloomerp.components.communication.render_inbox_item.Inbox")
    @patch("bloomerp.components.communication.render_inbox_item.render")
    @patch("bloomerp.components.communication.render_inbox_item.get_object_or_404")
    @patch(
        "bloomerp.components.communication.render_inbox_item."
        "accessible_inbox_items"
    )
    def test_unread_item_is_marked_as_read_after_rendering(
        self,
        accessible_inbox_items,
        get_object_or_404,
        render,
        inbox,
    ):
        item_type = Mock(actions=[])
        item_type.on_render.return_value = "Received email"
        item = Mock(is_read=False)
        item.get_inbox_item_type.return_value = item_type
        get_object_or_404.return_value = item
        render.return_value = HttpResponse()
        inbox.get_unread_count_for_user.return_value = 0

        render_inbox_item(self.request, "item-id")

        item_type.on_mark_as_read.assert_called_once_with(item, self.request)
