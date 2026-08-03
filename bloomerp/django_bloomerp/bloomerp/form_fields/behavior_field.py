from typing import Any

from django import forms

from bloomerp.widgets.behavior_builder_widget import BehaviorBuilderWidget


class BehaviorField(forms.JSONField):
    """Stores UI-authored behaviors without executing them."""

    widget = BehaviorBuilderWidget

    def clean(self, value: Any) -> dict[str, Any] | None:
        cleaned = super().clean(value)
        if cleaned in self.empty_values:
            return None
        if isinstance(cleaned, list):
            cleaned = {"version": 1, "rules": cleaned}
        if not isinstance(cleaned, dict):
            raise forms.ValidationError("Behaviors must be a structured object.")

        rules = cleaned.get("rules", [])
        if not isinstance(rules, list):
            raise forms.ValidationError("Behavior rules must be a list.")
        if not rules:
            return None
        if not all(isinstance(rule, dict) for rule in rules):
            raise forms.ValidationError("Each behavior rule must be an object.")

        return {"version": 1, "rules": rules}
