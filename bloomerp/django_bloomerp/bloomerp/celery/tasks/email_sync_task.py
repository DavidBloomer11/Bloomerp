from datetime import timedelta
from typing import Any

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from bloomerp.communication.emails.email_providers import EmailProvider, EmailProviderDefinition, EmailSyncMode
from bloomerp.models.communication.email_account import EmailAccount


DEFAULT_SYNC_LIMIT = 50
SYNC_LOCK_MINUTES = 15


def _provider_sync_interval_minutes(email_account: EmailAccount) -> int:
    """Returns sync interval in minutes

    Args:
        email_account (EmailAccount): The email account for which to determine the sync interval.

    Returns:
        int: The sync interval in minutes.
    """
    provider : EmailProviderDefinition = EmailProvider.from_key(email_account.provider).value
    if provider is None:
        return email_account.sync_interval_minutes or 5
    return (
        email_account.sync_interval_minutes
        or provider.sync_capabilities.default_poll_interval_minutes
    )


def _account_sync_mode(email_account: EmailAccount) -> str | None:
    """Returns the sync capability mode for the given email account.

    Args:
        email_account (EmailAccount): The email account for which to determine the sync mode.

    Returns:
        str | None: The sync mode.
    """
    provider : EmailProviderDefinition = EmailProvider.from_key(email_account.provider).value
    if provider is None:
        return email_account.sync_mode or None
    return email_account.sync_mode or provider.sync_capabilities.default_mode.value


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


@shared_task
def dispatch_due_email_syncs() -> int:
    now = timezone.now()
    due_account_ids = (
        EmailAccount.objects
        .filter(
            status=EmailAccount.Status.ACTIVE,
            sync_enabled=True,
        )
        .filter(Q(next_sync_at__isnull=True) | Q(next_sync_at__lte=now))
        .only("id", "provider", "sync_mode")
    )

    queued_count = 0
    for email_account in due_account_ids:
        if _account_sync_mode(email_account) != EmailSyncMode.POLLING.value:
            continue
        sync_email_account.delay(str(email_account.id))
        queued_count += 1

    return queued_count


@shared_task(bind=True, max_retries=3)
def sync_email_account(self, email_account_id: str, limit: int = DEFAULT_SYNC_LIMIT) -> dict[str, Any]:
    from bloomerp.communication.emails.actions import sync_emails_for_account

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
        synced_count = sync_emails_for_account(email_account, limit=limit)
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
        raise self.retry(exc=exc, countdown=60)

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
