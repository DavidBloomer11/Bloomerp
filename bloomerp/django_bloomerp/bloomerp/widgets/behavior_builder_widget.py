import json
from typing import Any

from django import forms


class BehaviorBuilderWidget(forms.Widget):
    """Visual editor for versioned form-behavior configuration."""

    template_name = "widgets/behavior_builder_widget.html"

    def __init__(
        self,
        attrs=None,
        *,
        source_field: dict[str, str] | None = None,
        field_catalog: list[dict[str, str]] | None = None,
    ):
        super().__init__(attrs)
        self.source_field = source_field or {}
        self.field_catalog = field_catalog or []

    def format_value(self, value: Any) -> str:
        if value in (None, "", [], {}):
            value = {"version": 1, "rules": []}
        elif isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = {"version": 1, "rules": []}
        if isinstance(value, list):
            value = {"version": 1, "rules": value}
        if not isinstance(value, dict):
            value = {"version": 1, "rules": []}
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
