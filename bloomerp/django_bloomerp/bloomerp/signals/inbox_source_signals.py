from django.db.utils import OperationalError, ProgrammingError


def ensure_inbox_source_schedules(*args, **kwargs) -> None:
    try:
        from bloomerp.communication.inbox_sources import synchronize_job_schedules

        synchronize_job_schedules()
    except (OperationalError, ProgrammingError):
        # Migrations and first-time setup can run before celery-beat tables exist.
        pass
