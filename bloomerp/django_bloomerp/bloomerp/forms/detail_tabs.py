from django import forms
from django.core.exceptions import ValidationError

from bloomerp.services.detail_tab_services import validate_tab_url


class DetailTabItemForm(forms.Form):
    """Validate the shared create/edit modal for folders and URL tabs."""

    item_type = forms.ChoiceField(
        choices=(("folder", "Folder"), ("url", "URL")),
        widget=forms.HiddenInput,
    )
    item_id = forms.UUIDField(required=False, widget=forms.HiddenInput)
    name = forms.CharField(max_length=255)
    url = forms.CharField(max_length=2048, required=False)

    def clean(self) -> dict:
        cleaned_data = super().clean()
        item_type = cleaned_data.get("item_type")
        url = cleaned_data.get("url", "")

        if item_type == "folder":
            cleaned_data["url"] = None
        elif item_type == "url":
            try:
                cleaned_data["url"] = validate_tab_url(url)
            except ValidationError as exc:
                self.add_error("url", exc)
        return cleaned_data
