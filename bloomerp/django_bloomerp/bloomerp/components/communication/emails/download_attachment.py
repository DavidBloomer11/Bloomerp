from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from bloomerp.communication.emails.actions import fetch_email_attachment
from bloomerp.router import router


@router.register(
    path="components/communication/emails/download_attachment/<str:inbox_item_id>/<str:attachment_id>/",
    url_name="components_emails_download_attachment",
)
@login_required
def download_attachment(
    request: HttpRequest,
    inbox_item_id: str,
    attachment_id: str,
) -> HttpResponse:
    """Downloads an attachment of an email item

    Args:
        request (HttpRequest): The HTTP request object.
        inbox_item_id (str): The ID of the inbox item.
        attachment_id (str): The ID of the attachment.

    Returns:
        HttpResponse: The HTTP response containing the attachment.
    """
    from bloomerp.models.communication.inbox.inbox_item import InboxItem

    item = get_object_or_404(
        InboxItem.objects.filter(
            Q(folder__inbox__owner=request.user)
            | Q(folder__inbox__members=request.user),
            item_type="email",
        ).distinct(),
        id=inbox_item_id,
    )
    attachment = fetch_email_attachment(item, attachment_id)
    response = FileResponse(
        BytesIO(attachment.content),
        as_attachment=True,
        filename=attachment.filename,
        content_type=attachment.content_type,
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response
