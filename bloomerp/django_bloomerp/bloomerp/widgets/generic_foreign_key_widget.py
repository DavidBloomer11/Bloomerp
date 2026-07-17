from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.forms import widgets
from django.urls import reverse

from bloomerp.services.object_services import get_object_detail_url
from bloomerp.utils.labels import safe_object_label


class GenericForeignKeyWidget(widgets.Widget):
    """Select one permission-visible object and submit its generic relation keys."""

    template_name = "widgets/generic_foreign_key_widget.html"

    def __init__(self, attrs: dict[str, Any] | None = None):
        attrs = attrs.copy() if attrs else {}
        self.content_type_field_name = attrs.pop("content_type_field_name", "content_type")
        self.object_id_field_name = attrs.pop("object_id_field_name", "object_id")
        super().__init__(attrs)

    def get_context(self, name: str, value: Any, attrs: dict[str, Any] | None):
        context = super().get_context(name, value, attrs)
        selected_object = value if isinstance(value, Model) else None
        content_type_id = ""
        object_id = ""
        selected_label = ""
        selected_url = ""

        if selected_object is not None:
            content_type_id = str(ContentType.objects.get_for_model(selected_object).pk)
            object_id = str(selected_object.pk)
            selected_label = safe_object_label(selected_object)
            selected_url = get_object_detail_url(selected_object)
        elif isinstance(value, dict):
            content_type_id = str(value.get("content_type_id") or "")
            object_id = str(value.get("object_id") or "")
            selected_label = str(value.get("label") or object_id)
            selected_url = str(value.get("detail_url") or "")

        context.update(
            {
                "content_type_field_name": self.content_type_field_name,
                "object_id_field_name": self.object_id_field_name,
                "selected_content_type_id": content_type_id,
                "selected_object_id": object_id,
                "selected_label": selected_label,
                "selected_url": selected_url,
                "search_url": reverse("components_search_content_objects"),
            }
        )
        return context
