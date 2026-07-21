from celery import shared_task
from bloomerp.communication.emails.sync import (
    DEFAULT_SYNC_LIMIT,
    synchronize_email_account,
)


@shared_task(bind=True, max_retries=3)
def sync_email_account(self, email_account_id: str, limit: int = DEFAULT_SYNC_LIMIT):
    try:
        return synchronize_email_account(email_account_id, limit=limit)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
