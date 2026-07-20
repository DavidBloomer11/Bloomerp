from collections.abc import Iterable

from django import forms


class DatalistTextInput(forms.TextInput):
    """A reusable text input backed by labelled HTML datalist options."""

    template_name = "widgets/datalist_text_input.html"

    def __init__(
        self,
        *,
        options: Iterable[tuple[str, str]],
        attrs: dict | None = None,
    ) -> None:
        attrs = dict(attrs or {})
        attrs.setdefault("list", "datalist-options")
        super().__init__(attrs=attrs)
        self.options = list(options)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        datalist_id = context["widget"]["attrs"]["list"]
        context["widget"]["datalist_id"] = datalist_id
        context["widget"]["options"] = [
            {"value": option_value, "label": option_label}
            for option_value, option_label in self.options
        ]
        return context
