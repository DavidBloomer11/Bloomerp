from __future__ import annotations

import re
import uuid
from collections import defaultdict
from typing import Any
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Model

from bloomerp.models.users.user_detail_view_tabs_preference import (
    UserDetailViewTabItem,
    UserDetailViewTabsPreference,
)
from bloomerp.router import router


PK_ROUTE_ARGUMENT = re.compile(r"<(?:[^:>]+:)?pk>")
TEMPLATE_ARGUMENT = re.compile(r"{{\s*([^{}]+?)\s*}}")
MAX_TAB_ITEMS = 250


def get_detail_route_options(model: type[Model] | None) -> list[dict[str, str]]:
    """Return one-primary-key detail routes as selectable URL templates."""
    if model is None:
        return []

    options: list[dict[str, str]] = []
    for route in router.filter(model=model, route_type="detail"):
        if route.nr_of_args() != 1 or not PK_ROUTE_ARGUMENT.search(route.path):
            continue
        options.append(
            {
                "name": route.name,
                "url": PK_ROUTE_ARGUMENT.sub("{{pk}}", route.path),
            }
        )
    return options


def create_default_tab_items(
    preference: UserDetailViewTabsPreference,
) -> None:
    """Populate a new preference from the model's current detail routes."""
    model = preference.content_type.model_class()
    UserDetailViewTabItem.objects.bulk_create(
        [
            UserDetailViewTabItem(
                preference=preference,
                name=option["name"],
                url=option["url"],
                position=position,
            )
            for position, option in enumerate(get_detail_route_options(model))
        ]
    )


def validate_tab_url(url: str) -> str:
    """Validate a root-relative or HTTP(S) URL with only a ``{{pk}}`` token."""
    normalized = url.strip()
    if not normalized:
        raise ValidationError("URL is required.")

    arguments = {argument.strip() for argument in TEMPLATE_ARGUMENT.findall(normalized)}
    if arguments - {"pk"}:
        raise ValidationError("Only the {{pk}} placeholder is supported.")

    parsed = urlsplit(normalized)
    is_internal = not parsed.scheme and not parsed.netloc and normalized.startswith("/")
    is_external = parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    if not is_internal and not is_external:
        raise ValidationError(
            "Enter an internal URL beginning with / or a complete http(s) URL."
        )
    return normalized


def resolve_tab_url(url: str, object_pk: Any) -> str:
    """Resolve the single supported object placeholder in a stored tab URL."""
    return url.replace("{{pk}}", str(object_pk))


def build_rendered_tab_items(
    preference: UserDetailViewTabsPreference,
    *,
    object_pk: Any,
    request_path: str,
) -> list[dict[str, Any]]:
    """Build the ordered tab/folder tree consumed by the detail template."""
    items = list(preference.items.select_related("parent").order_by("position", "id"))
    children_by_parent: dict[uuid.UUID, list[UserDetailViewTabItem]] = defaultdict(list)
    for item in items:
        if item.parent_id:
            children_by_parent[item.parent_id].append(item)

    def render_tab(item: UserDetailViewTabItem) -> dict[str, Any]:
        href = resolve_tab_url(item.url or "", object_pk)
        parsed = urlsplit(href)
        return {
            "id": str(item.id),
            "name": item.name,
            "url": item.url,
            "href": href,
            "is_external": bool(parsed.scheme and parsed.netloc),
            "is_active": parsed.path.rstrip("/") == request_path.rstrip("/"),
        }

    rendered: list[dict[str, Any]] = []
    for item in (item for item in items if item.parent_id is None):
        if item.is_folder:
            rendered.append(
                {
                    "id": str(item.id),
                    "name": item.name,
                    "is_folder": True,
                    "tabs": [render_tab(child) for child in children_by_parent[item.id]],
                }
            )
        else:
            rendered.append({**render_tab(item), "is_folder": False})
    return rendered


def sync_tab_items(
    preference: UserDetailViewTabsPreference,
    payload: Any,
) -> None:
    """Replace a preference's relational tree with a validated client snapshot."""
    if not isinstance(payload, list):
        raise ValidationError("Items must be a list.")
    if len(payload) > MAX_TAB_ITEMS:
        raise ValidationError(f"A layout can contain at most {MAX_TAB_ITEMS} items.")

    normalized: list[dict[str, Any]] = []
    seen_ids: set[uuid.UUID] = set()
    for raw_item in payload:
        if not isinstance(raw_item, dict):
            raise ValidationError("Every item must be an object.")
        try:
            item_id = uuid.UUID(str(raw_item.get("id")))
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValidationError("Every item requires a valid UUID.") from exc
        if item_id in seen_ids:
            raise ValidationError("Item IDs must be unique.")
        seen_ids.add(item_id)

        name = str(raw_item.get("name") or "").strip()
        if not name or len(name) > 255:
            raise ValidationError("Every item requires a name of at most 255 characters.")

        raw_url = raw_item.get("url")
        url = None if raw_url is None else validate_tab_url(str(raw_url))
        raw_parent_id = raw_item.get("parent_id")
        try:
            parent_id = uuid.UUID(str(raw_parent_id)) if raw_parent_id else None
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValidationError("Parent IDs must be valid UUIDs.") from exc

        try:
            position = int(raw_item.get("position", 0))
        except (TypeError, ValueError) as exc:
            raise ValidationError("Positions must be integers.") from exc
        if position < 0:
            raise ValidationError("Positions cannot be negative.")

        normalized.append(
            {
                "id": item_id,
                "name": name,
                "url": url,
                "parent_id": parent_id,
                "position": position,
            }
        )

    folder_ids = {item["id"] for item in normalized if item["url"] is None}
    for item in normalized:
        if item["url"] is None and item["parent_id"] is not None:
            raise ValidationError("Folders must remain at the top level.")
        if item["parent_id"] is not None and item["parent_id"] not in folder_ids:
            raise ValidationError("Tabs may only be placed inside a submitted folder.")

    foreign_ids = UserDetailViewTabItem.objects.filter(id__in=seen_ids).exclude(
        preference=preference
    )
    if foreign_ids.exists():
        raise ValidationError("An item belongs to a different tabs preference.")

    with transaction.atomic():
        preference.items.exclude(id__in=seen_ids).delete()
        existing = {item.id: item for item in preference.items.all()}
        saved: dict[uuid.UUID, UserDetailViewTabItem] = {}

        for data in sorted(normalized, key=lambda item: item["parent_id"] is not None):
            item = existing.get(data["id"]) or UserDetailViewTabItem(
                id=data["id"],
                preference=preference,
            )
            item.name = data["name"]
            item.url = data["url"]
            item.position = data["position"]
            item.parent = saved.get(data["parent_id"])
            item.full_clean()
            item.save()
            saved[item.id] = item
