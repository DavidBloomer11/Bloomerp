from __future__ import annotations

from typing import Any, Mapping

from django.contrib.contenttypes.models import ContentType
from django.db import models

from bloomerp.models import ApplicationField
from bloomerp.models.base_bloomerp_model import FieldLayout


ROW_KEY_SEPARATOR = "__"
ROW_ID_KEY = "id"
ROW_DELETE_KEY = "DELETE"




def collect_submitted_one_to_many_data(
    *,
    parent_model: type[models.Model],
    layout: FieldLayout,
    submitted_data: Mapping[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Collect one-to-many inline table rows from submitted layout form data."""
    one_to_many_fields = _get_layout_one_to_many_application_fields(
        parent_model=parent_model,
        layout=layout,
    )
    collected_data: dict[str, list[dict[str, Any]]] = {}

    for application_field in one_to_many_fields:
        rows = _parse_submitted_rows(application_field.field, submitted_data)
        submitted_rows = [
            row_data
            for _, row_data in sorted(rows.items(), key=lambda item: _row_sort_key(item[0]))
            if not _is_blank_submitted_row(row_data)
        ]
        if submitted_rows:
            collected_data[application_field.field] = submitted_rows

    return collected_data



def _get_layout_one_to_many_application_fields(
    *,
    parent_model: type[models.Model],
    layout: FieldLayout,
) -> list[ApplicationField]:
    content_type = ContentType.objects.get_for_model(parent_model)
    item_ids = [
        item.id
        for row in layout.rows
        for item in row.items
        if str(item.id).isdigit()
    ]
    if not item_ids:
        return []

    application_fields = {
        field.pk: field
        for field in ApplicationField.objects.filter(content_type=content_type, id__in=item_ids)
    }

    one_to_many_fields: list[ApplicationField] = []
    seen: set[int] = set()
    for row in layout.rows:
        for item in row.items:
            if not str(item.id).isdigit():
                continue

            application_field = application_fields.get(int(item.id))
            if application_field is None or application_field.pk in seen:
                continue

            field_type = application_field.get_field_type_enum().value
            if field_type.id != "OneToManyField":
                continue

            one_to_many_fields.append(application_field)
            seen.add(application_field.pk)

    return one_to_many_fields



def _parse_submitted_rows(prefix: str, submitted_data: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    prefix_with_separator = f"{prefix}{ROW_KEY_SEPARATOR}"

    for key in submitted_data.keys():
        if not key.startswith(prefix_with_separator):
            continue

        parts = key.split(ROW_KEY_SEPARATOR, 2)
        if len(parts) != 3:
            continue

        _, row_index, field_name = parts
        rows.setdefault(row_index, {})[field_name] = _get_submitted_value(submitted_data, key)

    return rows


def _get_submitted_value(submitted_data: Mapping[str, Any], key: str) -> Any:
    if hasattr(submitted_data, "getlist"):
        values = submitted_data.getlist(key)
        if len(values) > 1:
            return values
    return submitted_data.get(key)


def _row_sort_key(row_index: str) -> tuple[int, int | str]:
    if str(row_index).isdigit():
        return (0, int(row_index))
    return (1, str(row_index))


def _is_blank_submitted_row(row_data: dict[str, Any]) -> bool:
    for field_name, value in row_data.items():
        if field_name in (ROW_ID_KEY, ROW_DELETE_KEY):
            continue
        if value not in (None, "", []):
            return False
    return False if row_data.get(ROW_DELETE_KEY) else True

