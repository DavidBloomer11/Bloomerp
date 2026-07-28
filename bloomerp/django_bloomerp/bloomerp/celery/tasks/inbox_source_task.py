from typing import Any

from celery import shared_task


@shared_task(bind=True, max_retries=3)
def execute_inbox_source_task(
    self,
    key: str,
    serialized_args: list[Any] | None = None,
    serialized_kwargs: dict[str, Any] | None = None,
    execution_id: str | None = None,
) -> dict[str, Any]:
    from bloomerp.communication.inbox_sources import (
        _deserialize_source_value,
        execute_registered_source,
    )

    try:
        result = execute_registered_source(
            key,
            *_deserialize_source_value(serialized_args or []),
            **_deserialize_source_value(serialized_kwargs or {}),
        )
        return {
            "execution_id": execution_id or self.request.id,
            "source_key": key,
            "outcome": result.outcome,
            "reason": result.reason,
            "delivery_count": result.delivery_count,
            "item_count": result.item_count,
            "metrics": dict(result.metrics),
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
