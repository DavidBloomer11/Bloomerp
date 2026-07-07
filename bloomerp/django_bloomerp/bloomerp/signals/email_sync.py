from django.db.utils import OperationalError, ProgrammingError
from django_celery_beat.models import IntervalSchedule, PeriodicTask


EMAIL_SYNC_DISPATCHER_NAME = "bloomerp.email_sync.dispatch_due_email_syncs"
EMAIL_SYNC_DISPATCHER_TASK = "bloomerp.celery.tasks.email_sync_task.dispatch_due_email_syncs"


def ensure_email_sync_dispatcher_schedule(*args, **kwargs) -> None:
    try:
        interval, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )
        PeriodicTask.objects.update_or_create(
            name=EMAIL_SYNC_DISPATCHER_NAME,
            defaults={
                "task": EMAIL_SYNC_DISPATCHER_TASK,
                "interval": interval,
                "crontab": None,
                "solar": None,
                "clocked": None,
                "enabled": True,
                "description": "Dispatch due Bloomerp email account sync tasks.",
            },
        )
    except (OperationalError, ProgrammingError):
        pass
