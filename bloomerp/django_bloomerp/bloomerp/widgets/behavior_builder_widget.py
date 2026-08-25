import json
from typing import Any

from django import forms

from bloomerp.form_fields.behavior import BehaviorConfig


class BehaviorBuilderWidget(forms.Widget):
    """Visual editor for form-behavior configuration."""

    template_name = "widgets/behavior_builder_widget.html"

    def __init__(
        self,
        attrs=None,
        *,
        source_field: dict[str, str] | None = None,
        field_catalog: list[dict[str, object]] | None = None,
    ):
        super().__init__(attrs)
        self.source_field = source_field or {}
        self.field_catalog = field_catalog or []

    def format_value(self, value: Any) -> str:
        if isinstance(value, BehaviorConfig):
            value = value.to_storage()
        elif value in (None, "", [], {}):
            value = {"rules": []}
        elif isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = {"rules": []}
        if isinstance(value, list):
            value = {"rules": value}
        if not isinstance(value, dict):
            value = {"rules": []}
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)

    def value_from_datadict(self, data, files, name):
        return data.get(name)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"].update(
            {
                "value": self.format_value(value),
                "source_field_id": str(self.source_field.get("id", "")),
                "source_field_label": self.source_field.get("label", "This field"),
                "source_field_type": self.source_field.get("fieldType", ""),
                "field_catalog_json": json.dumps(
                    self.field_catalog,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ),
            }
        )
        return context
