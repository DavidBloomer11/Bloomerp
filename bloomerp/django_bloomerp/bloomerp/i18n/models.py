from __future__ import annotations

from django.apps import AppConfig
from django.utils.encoding import force_str
from django.utils.translation import override


def model_messages(app: AppConfig, source_language: str) -> list[dict]:
    """Expose model and field display metadata, including Django's fallbacks."""

    messages: list[dict] = []
    with override(source_language):
        for model in app.get_models():
            model_location = f"{app.label}.{model._meta.model_name}"
            for label in (model._meta.verbose_name, model._meta.verbose_name_plural):
                value = force_str(label)
                if value:
                    messages.append(
                        {"message": value, "locations": [(model_location, None)]}
                    )
            for field in model._meta.get_fields():
                label = getattr(field, "verbose_name", None)
                if label:
                    declared_label = getattr(field, "_verbose_name", None)
                    display_label = (
                        force_str(declared_label)
                        if declared_label is not None
                        else field.name.replace("_", " ").title()
                    )
                    messages.append(
                        {
                            "message": display_label,
                            "locations": [(f"{model_location}.{field.name}", None)],
                        }
                    )
                help_text = getattr(field, "help_text", None)
                if help_text:
                    messages.append(
                        {
                            "message": force_str(help_text),
                            "locations": [(f"{model_location}.{field.name}", None)],
                        }
                    )
                for choice in getattr(field, "choices", None) or []:
                    if len(choice) >= 2 and choice[1]:
                        messages.append(
                            {
                                "message": force_str(choice[1]),
                                "locations": [(f"{model_location}.{field.name}", None)],
                            }
                        )
    return messages
