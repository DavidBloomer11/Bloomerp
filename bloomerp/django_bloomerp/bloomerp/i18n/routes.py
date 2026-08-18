from __future__ import annotations

from django.apps import AppConfig

from bloomerp.router import router


def route_messages(app: AppConfig) -> list[dict]:
    """Expose translatable route metadata owned by an installed app."""

    messages: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for route in router.get_routes():
        if not route.translatable or route.owner_app_label != app.label:
            continue

        values = (
            (route.name_message, "name"),
            (route.description_message, "description"),
        )
        for message, field in values:
            if not message:
                continue
            context = route._translation_context(field)
            key = (context, message)
            if key in seen:
                continue
            seen.add(key)
            messages.append(
                {
                    "message": message,
                    "context": context,
                    "locations": [(f"route:{route.url_name}", None)],
                }
            )
    return messages
