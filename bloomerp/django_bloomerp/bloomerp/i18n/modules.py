from __future__ import annotations

from django.apps import AppConfig

from bloomerp.modules.definition import module_registry


def module_messages(app: AppConfig) -> list[dict]:
    """Expose translatable module metadata owned by an installed app."""

    messages: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for module in module_registry.get_all().values():
        if module.owner_app_label != app.label:
            continue

        for message, field in (
            (module.name, "name"),
            (module.description, "description"),
        ):
            if not message:
                continue
            context = module._translation_context(field)
            key = (context, message)
            if key in seen:
                continue
            seen.add(key)
            messages.append(
                {
                    "message": message,
                    "context": context,
                    "locations": [(f"module:{module.full_id or module.id}", None)],
                }
            )
    return messages
