import datetime
from typing import TYPE_CHECKING

from django.db import transaction
from django.db.models import Q, QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone

from bloomerp.communication.emails.base_adapter import BloomerpEmail
from bloomerp.communication.emails.email_providers import EmailProvider, EmailProviderDefinition
from bloomerp.models.communication.email_account import EmailAccount


if TYPE_CHECKING:
    from bloomerp.models.communication.inbox.inbox_folder import InboxFolder
    from bloomerp.models.communication.inbox.inbox_item import InboxItem
    from bloomerp.communication.emails.base_adapter import BaseEmailAdapter

DEEP_QUERY_LIMIT = 50


def _resolve_provider(email_account: EmailAccount) -> EmailProviderDefinition:
    provider = EmailProvider.from_key(email_account.provider)
    if provider is None:
        raise ValueError(f"Unsupported email provider: {email_account.provider}")
    return provider.value


def _resolve_email_adapter_for_account(email_account: EmailAccount) -> "BaseEmailAdapter":
    provider = _resolve_provider(email_account)
    return provider.adapter_class(email_account=email_account)


def _resolve_email_account_from_item(inbox_item: "InboxItem") -> EmailAccount:
    raw_meta_data = inbox_item.raw_meta_data or {}
    email_account_id = raw_meta_data.get("email_account_id")
    if email_account_id:
        return get_object_or_404(EmailAccount, id=email_account_id)

    email_folder = inbox_item.folder
    if email_folder:
        return get_object_or_404(EmailAccount, id=email_folder.related_object_id)

    raise EmailAccount.DoesNotExist("Unable to resolve email account for inbox item.")


def _resolve_email_account_from_folder(folder: "InboxFolder") -> EmailAccount:
    if not folder.related_object_id:
        raise EmailAccount.DoesNotExist("Email inbox folder is not connected to an email account.")
    return get_object_or_404(EmailAccount, id=folder.related_object_id)


def _resolve_email_adapter(inbox_item:"InboxItem", request: HttpRequest) -> "BaseEmailAdapter":
    """
    Resolve the appropriate email adapter for the given inbox item.

    Args:
        inbox_item (InboxItem): The inbox item for which to resolve the email adapter.
        request (HttpRequest): The HTTP request object.
    """
    email_account = _resolve_email_account_from_item(inbox_item)
    return _resolve_email_adapter_for_account(email_account)


def render_email(inbox_item:"InboxItem", request: HttpRequest) -> str:
    """_summary_

    Args:
        inbox_item (InboxItem): _description_
        request (HttpRequest): _description_

    Returns:
        str: _description_
    """
    adapter = _resolve_email_adapter(inbox_item, request)
    try:
        return adapter.fetch_email_content(email_id=inbox_item.related_item_id)
    finally:
        close = getattr(adapter, "close", None)
        if callable(close):
            close()


def mark_email_as_read(inbox_item:"InboxItem", request: HttpRequest):
    adapter = _resolve_email_adapter(inbox_item, request)
    adapter.mark_as_read(email_id=inbox_item.related_item_id)
    inbox_item.is_read = True
    inbox_item.save(update_fields=["is_read"])


def delete_email(inbox_item:"InboxItem", request: HttpRequest):
    adapter = _resolve_email_adapter(inbox_item, request)
    adapter.delete_email(email_id=inbox_item.related_item_id)


def _query_local_email_items(
    filters: dict[str, str] | None,
    folder: "InboxFolder",
) -> QuerySet["InboxItem"]:
    from bloomerp.communication.inbox_folder_definition import InboxFolderType
    from bloomerp.models.communication.inbox.inbox_item import InboxItem

    queryset = InboxItem.objects.filter(
        folder=folder,
        item_type=InboxFolderType.EMAIL.value.item_type.key,
    )

    search_string = (filters or {}).get("q")
    if search_string:
        queryset = queryset.filter(
            Q(title__icontains=search_string)
            | Q(snippet__icontains=search_string)
            | Q(actor__icontains=search_string)
        )

    return queryset.distinct().order_by("-datetime_received", "-datetime_created")


def _upsert_email_inbox_item(email: BloomerpEmail, folder: "InboxFolder") -> "InboxItem":
    from bloomerp.communication.inbox_folder_definition import InboxFolderType
    from bloomerp.models.communication.inbox.inbox_item import InboxItem

    item_type = InboxFolderType.EMAIL.value.item_type.key
    inbox_item = (
        InboxItem.objects
        .filter(
            item_type=item_type,
            folder=folder,
            related_item_id=email.provider_message_id,
            raw_meta_data__email_account_id=email.email_account_id,
        )
        .first()
    )

    if inbox_item is None:
        inbox_item = InboxItem(
            item_type=item_type,
            related_item_id=email.provider_message_id,
        )

    inbox_item.title = email.subject or "(No subject)"
    inbox_item.snippet = email.snippet
    inbox_item.actor = email.sender
    inbox_item.is_read = email.is_read
    inbox_item.raw_meta_data = email.retrieval_metadata()
    inbox_item.folder = folder
    inbox_item.datetime_received = email.date
    inbox_item.save()
    return inbox_item


def query_emails(
    filters: dict[str, str] | None,
    folder: "InboxFolder",
    deep_query: bool,
) -> QuerySet["InboxItem"]:
    """
    Query emails based on the provided filters.

    Args:
        filters (dict[str, str]): A dictionary of filter parameters.
        folder (InboxFolder): The email inbox folder to query.
        deep_query (bool): If True, perform a deep query; otherwise, perform a shallow query.

    Returns:
        QuerySet[InboxItem]: Matching email inbox items.
    """
    local_queryset = _query_local_email_items(filters, folder)
    if deep_query and not local_queryset.exists():
        email_account = _resolve_email_account_from_folder(folder)
        adapter = _resolve_email_adapter_for_account(email_account)
        search_string = (filters or {}).get("q")

        try:
            emails = adapter.search_emails(
                search_string,
                mailbox="INBOX",
                limit=DEEP_QUERY_LIMIT,
            )
        finally:
            close = getattr(adapter, "close", None)
            if callable(close):
                close()

        for email in emails:
            _upsert_email_inbox_item(email, folder)

        local_queryset = _query_local_email_items(filters, folder)

    return local_queryset
        

def _fetch_synced_emails_for_account(
    email_account: EmailAccount,
    *,
    from_date: datetime.date | datetime.datetime | None = None,
    to_date: datetime.date | datetime.datetime | None = None,
    limit: int = 50,
) -> list[BloomerpEmail]:
    adapter = _resolve_email_adapter_for_account(email_account)
    try:
        return adapter.sync_emails(
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            mailbox="INBOX",
        )
    finally:
        close = getattr(adapter, "close", None)
        if callable(close):
            close()


def _upsert_emails_to_folder(emails: list[BloomerpEmail], folder: "InboxFolder") -> int:
    with transaction.atomic():
        for email in emails:
            _upsert_email_inbox_item(email, folder)

    return len(emails)


def _sync_email_account_to_folder(
    email_account: EmailAccount,
    folder: "InboxFolder",
    *,
    from_date: datetime.date | datetime.datetime | None = None,
    to_date: datetime.date | datetime.datetime | None = None,
    limit: int = 50,
) -> int:
    emails = _fetch_synced_emails_for_account(
        email_account,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
    )
    return _upsert_emails_to_folder(emails, folder)


def sync_emails_for_account(
    email_account: EmailAccount,
    *,
    from_date: datetime.date | datetime.datetime | None = None,
    to_date: datetime.date | datetime.datetime | None = None,
    limit: int = 50,
) -> int:
    """
    Sync emails for every inbox folder connected to the email account.
    """
    from bloomerp.communication.inbox_folder_definition import InboxFolderType
    from bloomerp.models.communication.inbox.inbox_folder import InboxFolder

    folders = InboxFolder.objects.filter(
        type=InboxFolderType.EMAIL.value.key,
        related_object_id=str(email_account.pk),
    )

    folders = list(folders)
    if not folders:
        return 0

    emails = _fetch_synced_emails_for_account(
        email_account,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
    )

    synced_count = len(emails)
    for folder in folders:
        _upsert_emails_to_folder(emails, folder)
    
    return synced_count


def sync_emails_for_folder(
    folder: "InboxFolder",
    from_date: datetime.date | datetime.datetime | None = None,
    to_date: datetime.date | datetime.datetime | None = None,
    limit: int = 50,
) -> int:
    """
    Sync emails for the given inbox folder.

    Args:
        folder (InboxFolder): The email inbox folder to sync.
        from_date (datetime | None): The start date for email synchronization.
        to_date (datetime | None): The end date for email synchronization.
    """
    email_account = _resolve_email_account_from_folder(folder)
    started_at = timezone.now()
    email_account.last_sync_started_at = started_at
    email_account.last_sync_error = ""
    email_account.save(update_fields=["last_sync_started_at", "last_sync_error", "datetime_updated"])

    try:
        synced_count = _sync_email_account_to_folder(
            email_account,
            folder,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
        )
    except Exception as exc:
        email_account.last_sync_error = str(exc)
        email_account.save(update_fields=["last_sync_error", "datetime_updated"])
        raise

    email_account.last_sync_finished_at = timezone.now()
    email_account.last_sync_error = ""
    email_account.save(
        update_fields=[
            "last_sync_finished_at",
            "last_sync_error",
            "datetime_updated",
        ]
    )
    return synced_count
