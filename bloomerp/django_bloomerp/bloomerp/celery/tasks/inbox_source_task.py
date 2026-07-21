from typing import Any

from celery import shared_task


@shared_task
def execute_inbox_source_task(
    key: str,
    serialized_args: list[Any] | None = None,
    serialized_kwargs: dict[str, Any] | None = None,
) -> dict[str, int | str]:
    from bloomerp.communication.inbox_sources import execute_serialized_source

    deliveries = execute_serialized_source(
        key,
        serialized_args=serialized_args,
        serialized_kwargs=serialized_kwargs,
    )
    return {
        "source_key": key,
        "delivery_count": len(deliveries),
        "item_count": sum(len(delivery.items) for delivery in deliveries),
    }
