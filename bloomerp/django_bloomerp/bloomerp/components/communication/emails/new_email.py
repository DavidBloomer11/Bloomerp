from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext as _
from email.utils import getaddresses
from typing import TYPE_CHECKING

from bloomerp.communication.emails.base_adapter import EmailAttachment
from bloomerp.communication.emails.email_providers import EmailProvider
from bloomerp.communication.utils.permissions import accessible_inbox_folders
from bloomerp.router import router
from bloomerp.utils.requests import render_message

if TYPE_CHECKING:
    from bloomerp.models.communication.inbox.inbox_folder import InboxFolder


# TODO: Refactor some of this logic

def resolve_inbox_folder(request: HttpRequest, inbox_folder_or_id: "InboxFolder | str | None") -> "InboxFolder | None":
    """
    Resolves an email InboxFolder that belongs to the requesting user.

    Args:
        request: The current request.
        inbox_folder_or_id: An InboxFolder instance, its ID, or None.

    Returns:
        The resolved InboxFolder when it exists and is accessible.
    """
    from bloomerp.models.communication.inbox.inbox_folder import InboxFolder

    if isinstance(inbox_folder_or_id, InboxFolder):
        return inbox_folder_or_id

    folder_id = inbox_folder_or_id or request.GET.get("folder_id") or request.POST.get("folder_id")
    if not folder_id:
        return None

    # TODO: Reusable 
    return get_object_or_404(
        accessible_inbox_folders(request.user).filter(type="email"),
        id=folder_id,
    )


@router.register(
    path="components/communication/emails/new_email",
    url_name="components_new_email"
)
@login_required
def new_email(request: HttpRequest, inbox_folder_or_id: "InboxFolder | str | None" = None) -> HttpResponse:
    """
    Renders the reusable email composer for a new outbound email.

    Args:
        request: The current HTTP request.
        inbox_folder_or_id: Optional folder instance or ID, supplied by inbox actions.

    Returns:
        A rendered email composer snippet.
    """
    inbox_folder = resolve_inbox_folder(request, inbox_folder_or_id)
    if inbox_folder is None:
        return render_message(request, _("Select an email folder before composing a message."), "warning")

    email_account = inbox_folder.related_object()
    if email_account is None:
        return render_message(request, _("This email folder is not connected to an email account."), "error")

    if request.method == "POST":
        return _send_new_email(request, inbox_folder, email_account)

    return _render_email_composer(
        request,
        inbox_folder=inbox_folder,
        email_account=email_account,
    )


def _send_new_email(request: HttpRequest, inbox_folder: "InboxFolder", email_account) -> HttpResponse:
    form_data = _get_form_data(request)
    errors = _validate_form_data(form_data)
    attachments = _get_attachments(request)

    if errors:
        return _render_email_composer(
            request,
            inbox_folder=inbox_folder,
            email_account=email_account,
            form_data=form_data,
            errors=errors,
        )

    provider = EmailProvider.from_key(email_account.provider)
    if provider is None:
        return render_message(request, _("This email account has an unsupported provider."), "error")

    adapter = provider.value.adapter_class(email_account)
    try:
        adapter.send_email(
            to=form_data["to"],
            cc=form_data["cc"],
            bcc=form_data["bcc"],
            subject=form_data["subject"],
            body_html=form_data["body"],
            attachments=attachments,
        )
    except ValidationError as exc:
        return _render_email_composer(
            request,
            inbox_folder=inbox_folder,
            email_account=email_account,
            form_data=form_data,
            errors=exc.messages,
        )
    finally:
        close = getattr(adapter, "close", None)
        if callable(close):
            close()

    return render_message(request, _("Email sent successfully."), "success")


def _render_email_composer(
    request: HttpRequest,
    *,
    inbox_folder: "InboxFolder",
    email_account,
    form_data: dict[str, object] | None = None,
    errors: list[str] | None = None,
) -> HttpResponse:
    form_data = form_data or {}
    ctx = {
        "mode": "new",
        "title": _("New email"),
        "submit_label": _("Send"),
        "inbox_folder": inbox_folder,
        "email_account": email_account,
        "from_email": getattr(email_account, "email_address", ""),
        "to": _join_recipients(form_data.get("to", [])),
        "cc": _join_recipients(form_data.get("cc", [])),
        "bcc": _join_recipients(form_data.get("bcc", [])),
        "subject": form_data.get("subject", ""),
        "body": form_data.get("body", ""),
        "form_action": reverse("components_new_email"),
        "send_enabled": True,
        "errors": errors or [],
    }
    
    return render(
        request,
        "components/communication/emails/email_editor.html",
        ctx,
    )


def _get_form_data(request: HttpRequest) -> dict[str, object]:
    return {
        "to": _parse_recipients(request.POST.get("to", "")),
        "cc": _parse_recipients(request.POST.get("cc", "")),
        "bcc": _parse_recipients(request.POST.get("bcc", "")),
        "subject": request.POST.get("subject", "").strip(),
        "body": request.POST.get("body", "").strip(),
    }


def _validate_form_data(form_data: dict[str, object]) -> list[str]:
    errors: list[str] = []
    recipients = form_data["to"]
    if not isinstance(recipients, list) or not recipients:
        errors.append(_("Add at least one recipient."))

    for field_name in ("to", "cc", "bcc"):
        for email_address in form_data[field_name]:
            try:
                validate_email(email_address)
            except ValidationError:
                errors.append(_("'%(email)s' is not a valid email address.") % {"email": email_address})

    if not form_data["subject"] and not form_data["body"]:
        errors.append(_("Add a subject or message body before sending."))

    return errors


def _parse_recipients(value: str) -> list[str]:
    normalized = value.replace(";", ",")
    return [email for _, email in getaddresses([normalized]) if email]


def _join_recipients(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value or "")


def _get_attachments(request: HttpRequest) -> list[EmailAttachment]:
    attachments: list[EmailAttachment] = []
    for uploaded_file in request.FILES.getlist("attachments"):
        attachments.append(
            EmailAttachment(
                filename=uploaded_file.name,
                content=uploaded_file.read(),
                content_type=uploaded_file.content_type or "application/octet-stream",
            )
        )
    return attachments
