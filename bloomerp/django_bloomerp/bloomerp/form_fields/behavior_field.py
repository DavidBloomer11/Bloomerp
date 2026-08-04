from typing import Any

from django import forms
from pydantic import ValidationError as PydanticValidationError

from bloomerp.form_fields.behavior import BehaviorConfig
from bloomerp.widgets.behavior_builder_widget import BehaviorBuilderWidget


class BehaviorField(forms.JSONField):
    """Stores UI-authored behaviors without executing them."""

    widget = BehaviorBuilderWidget

    def clean(self, value: Any) -> dict[str, Any] | None:
        cleaned = super().clean(value)
        if cleaned in self.empty_values:
            return None
        if isinstance(cleaned, list):
            cleaned = {"rules": cleaned}
        if not isinstance(cleaned, dict):
            raise forms.ValidationError("Behaviors must be a structured object.")

        try:
            config = BehaviorConfig.model_validate(cleaned)
        except PydanticValidationError as exc:
            raise forms.ValidationError(
                f"Invalid behavior configuration: {exc}",
            ) from exc

        if not config.rules:
            return None

        return config.to_storage()
