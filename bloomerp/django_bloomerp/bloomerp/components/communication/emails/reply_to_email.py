from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from typing import TYPE_CHECKING

from bloomerp.router import router
from bloomerp.utils.requests import render_message

if TYPE_CHECKING:
    from bloomerp.models.communication.inbox.inbox_item import InboxItem

def resolve_inbox_item(request: HttpRequest, inbox_item_or_id: "InboxItem | str | None") -> "InboxItem | None":
    """
    Resolves an email InboxItem that belongs to the requesting user.

    Args:
        request: The current request.
        inbox_item_or_id: An InboxItem instance, its ID, or None.

    Returns:
        The resolved InboxItem when it exists and is accessible.
    """
    from bloomerp.models.communication.inbox.inbox_item import InboxItem

    if isinstance(inbox_item_or_id, InboxItem):
        return inbox_item_or_id

    item_id = inbox_item_or_id or request.GET.get("item_id") or request.POST.get("item_id")
    if not item_id:
        return None

    return get_object_or_404(
        InboxItem.objects.filter(
            Q(folder__inbox__owner=request.user) | Q(folder__inbox__members=request.user),
            item_type="email",
        ).distinct(),
        id=item_id,
    )


@router.register(
    path="components/communication/emails/reply_to_email",
    url_name="components_reply_to_email"
)
@login_required
def reply_to_email(request: HttpRequest, inbox_item_or_id: "InboxItem | str | None" = None) -> HttpResponse:
    """
    Renders the reusable email composer with reply-oriented defaults.

    Args:
        request: The current HTTP request.
        inbox_item_or_id: Optional inbox item instance or ID.

    Returns:
        A rendered email composer snippet.
    """
    inbox_item = resolve_inbox_item(request, inbox_item_or_id)
    if inbox_item is None:
        return render_message(request, _("Select an email before replying."), "warning")

    subject = inbox_item.title or ""
    if subject and not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"

    inbox_folder = inbox_item.folder if hasattr(inbox_item, "folder") else None
    email_account = inbox_folder.related_object() if inbox_folder else None

    return render(
        request,
        "components/communication/emails/email_editor.html",
        {
            "mode": "reply",
            "title": _("Reply"),
            "submit_label": _("Send reply"),
            "inbox_item": inbox_item,
            "inbox_folder": inbox_folder,
            "email_account": email_account,
            "from_email": getattr(email_account, "email_address", ""),
            "to": inbox_item.actor or "",
            "cc": "",
            "bcc": "",
            "subject": subject,
            "body": "",
            "form_action": "",
            "send_enabled": False,
            "parent_email" : inbox_item.render(request)
        },
    )
