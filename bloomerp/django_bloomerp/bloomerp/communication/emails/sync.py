"""Email synchronization policy and inbox-source handlers.

Celery tasks are transport adapters for these functions. Keeping the source
logic here makes email synchronization usable and testable without a worker.
"""

from datetime import timedelta
from typing import Any

from django.db.models import Q, QuerySet
from django.utils import timezone

from bloomerp.communication.emails import actions as email_actions
from bloomerp.communication.emails.email_providers import (
    EmailProvider,
    EmailProviderDefinition,
    EmailSyncMode,
)
from bloomerp.models.communication.email_account import EmailAccount


DEFAULT_SYNC_LIMIT = 50
SYNC_LOCK_MINUTES = 15


def _provider_sync_interval_minutes(email_account: EmailAccount) -> int:
    provider = EmailProvider.from_key(email_account.provider)
    if provider is None:
        return email_account.sync_interval_minutes or 5
    provider_definition: EmailProviderDefinition = provider.value
    return (
        email_account.sync_interval_minutes
        or provider_definition.sync_capabilities.default_poll_interval_minutes
    )


def _account_sync_mode(email_account: EmailAccount) -> str | None:
    provider = EmailProvider.from_key(email_account.provider)
    if provider is None:
        return email_account.sync_mode or None
    provider_definition: EmailProviderDefinition = provider.value
    return email_account.sync_mode or provider_definition.sync_capabilities.default_mode.value


def _next_sync_at(email_account: EmailAccount):
    return timezone.now() + timedelta(minutes=_provider_sync_interval_minutes(email_account))


def _acquire_sync_lock(email_account_id: str) -> bool:
    now = timezone.now()
    lock_until = now + timedelta(minutes=SYNC_LOCK_MINUTES)
    updated = (
        EmailAccount.objects
        .filter(id=email_account_id)
        .filter(Q(sync_locked_until__isnull=True) | Q(sync_locked_until__lt=now))
        .update(
            sync_locked_until=lock_until,
            last_sync_started_at=now,
            last_sync_error="",
        )
    )
    return updated == 1


def _release_sync_lock(email_account: EmailAccount) -> None:
    email_account.sync_locked_until = None
    email_account.save(update_fields=["sync_locked_until", "datetime_updated"])


def resolve_email_folders(
    *,
    email_account_id: str | None = None,
    **kwargs,
) -> QuerySet:
    """Resolve email folders, optionally scoped to one account."""
    from bloomerp.communication.inbox_folder_definition import InboxFolderType
    from bloomerp.models.communication.inbox.inbox_folder import InboxFolder

    folders = InboxFolder.objects.filter(type=InboxFolderType.EMAIL.value.key)
    if email_account_id is not None:
        folders = folders.filter(related_object_id=str(email_account_id))
    return folders


def _sync_email_account_to_folders(
    email_account: EmailAccount,
    folders,
    *,
    from_date=None,
    to_date=None,
    limit: int = DEFAULT_SYNC_LIMIT,
    mailboxes: list[str] | None = None,
):
    from bloomerp.communication.inbox_sources import InboxSourceDelivery

    folders = list(folders)
    if not folders:
        return ()

    emails = []
    for mailbox in email_actions._normalize_mailboxes(mailboxes, email_account):
        emails.extend(
            email_actions._fetch_synced_emails_for_account(
                email_account,
                from_date=from_date,
                to_date=to_date,
                limit=limit,
                mailbox=mailbox,
            )
        )

    deliveries = []
    for folder in folders:
        created_items = email_actions._upsert_new_emails_to_folder(emails, folder)
        if created_items:
            deliveries.append(InboxSourceDelivery(folder=folder, items=created_items))
    return tuple(deliveries)


def handle_email_account_sync(
    folders,
    *,
    email_account_id: str,
    from_date=None,
    to_date=None,
    limit: int = DEFAULT_SYNC_LIMIT,
    mailboxes: list[str] | None = None,
    **kwargs,
):
    """Inbox event-source handler for synchronizing one email account."""
    email_account = EmailAccount.objects.get(pk=email_account_id)
    return _sync_email_account_to_folders(
        email_account,
        folders,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        mailboxes=mailboxes,
    )


def dispatch_due_email_syncs() -> int:
    """Queue an isolated synchronization task for every due polling account."""
    from bloomerp.celery.tasks.email_sync_task import sync_email_account

    now = timezone.now()
    due_accounts = (
        EmailAccount.objects
        .filter(status=EmailAccount.Status.ACTIVE, sync_enabled=True)
        .filter(Q(next_sync_at__isnull=True) | Q(next_sync_at__lte=now))
        .only("id", "provider", "sync_mode")
    )

    queued_count = 0
    for email_account in due_accounts:
        if _account_sync_mode(email_account) != EmailSyncMode.POLLING.value:
            continue
        sync_email_account.delay(str(email_account.id))
        queued_count += 1
    return queued_count


def dispatch_due_email_syncs_source(folders, *args, **kwargs):
    """Scheduled inbox-source handler that fans out work per due account."""
    dispatch_due_email_syncs()
    return ()


def synchronize_email_account(
    email_account_id: str,
    limit: int = DEFAULT_SYNC_LIMIT,
) -> dict[str, Any]:
    """Run one locked account synchronization and persist its lifecycle state."""
    from bloomerp.communication.inbox_sources import execute_registered_source

    if not _acquire_sync_lock(email_account_id):
        return {
            "email_account_id": email_account_id,
            "status": "skipped",
            "reason": "locked",
        }

    email_account = EmailAccount.objects.get(id=email_account_id)
    try:
        if _account_sync_mode(email_account) != EmailSyncMode.POLLING.value:
            _release_sync_lock(email_account)
            return {
                "email_account_id": email_account_id,
                "status": "skipped",
                "reason": "not_polling",
            }

        deliveries = execute_registered_source(
            "email.sync.account",
            email_account_id=str(email_account.id),
            limit=limit,
        )
        synced_count = max((len(delivery.items) for delivery in deliveries), default=0)
    except Exception as exc:
        email_account.refresh_from_db()
        email_account.last_sync_error = str(exc)
        email_account.next_sync_at = _next_sync_at(email_account)
        email_account.sync_locked_until = None
        email_account.save(
            update_fields=[
                "last_sync_error",
                "next_sync_at",
                "sync_locked_until",
                "datetime_updated",
            ]
        )
        raise

    email_account.refresh_from_db()
    email_account.last_sync_finished_at = timezone.now()
    email_account.last_sync_error = ""
    email_account.next_sync_at = _next_sync_at(email_account)
    email_account.sync_locked_until = None
    email_account.save(
        update_fields=[
            "last_sync_finished_at",
            "last_sync_error",
            "next_sync_at",
            "sync_locked_until",
            "datetime_updated",
        ]
    )
    return {
        "email_account_id": email_account_id,
        "status": "synced",
        "synced_count": synced_count,
    }
