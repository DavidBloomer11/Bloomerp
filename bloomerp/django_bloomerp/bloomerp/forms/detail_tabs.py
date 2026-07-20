from django import forms
from django.core.exceptions import ValidationError

from bloomerp.models.users.user_detail_view_tabs_preference import (
    UserDetailViewTabsPreference,
)
from bloomerp.widgets.datalist_widget import DatalistTextInput


class DetailTabItemForm(forms.Form):
    """Validate the shared create/edit modal for folders and URL tabs."""

    item_type = forms.ChoiceField(
        choices=(("folder", "Folder"), ("url", "URL")),
        widget=forms.HiddenInput,
    )
    item_id = forms.UUIDField(required=False, widget=forms.HiddenInput)
    name = forms.CharField(max_length=255)
    url = forms.CharField(max_length=2048, required=False)

    def __init__(
        self,
        *args,
        item_type: str,
        route_options: list[dict] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update(
            {"autofocus": True, "data-detail-tab-name-input": ""}
        )
        if item_type == "folder":
            self.fields.pop("url")
            return

        self.fields["url"].help_text = (
            "Use {{pk}} where the current object's primary key belongs."
        )
        self.fields["url"].widget = DatalistTextInput(
            options=[(option["url"], option["name"]) for option in (route_options or [])],
            attrs={
                "data-detail-tab-url-input": "",
                "list": "detail-tab-route-options",
                "placeholder": "/module/objects/{{pk}}/overview/",
            },
        )

    def clean(self) -> dict:
        cleaned_data = super().clean()
        item_type = cleaned_data.get("item_type")
        url = cleaned_data.get("url", "")

        if item_type == "folder":
            cleaned_data["url"] = None
        elif item_type == "url":
            try:
                cleaned_data["url"] = (
                    UserDetailViewTabsPreference.validate_tab_url(url)
                )
            except ValidationError as exc:
                self.add_error("url", exc)
        return cleaned_data
