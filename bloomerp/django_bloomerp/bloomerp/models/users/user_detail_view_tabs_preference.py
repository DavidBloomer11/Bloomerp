from __future__ import annotations

import re
import uuid
from collections import defaultdict
from typing import Any
from urllib.parse import urlsplit

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q

from bloomerp.models.definition import (
    ApiSettings,
    BloomerpModelConfig,
    UserAccessRule,
)
from bloomerp.models.users.base_preference import BasePreference
from bloomerp.router import router


PK_ROUTE_ARGUMENT = re.compile(r"<(?:[^:>]+:)?pk>")
TEMPLATE_ARGUMENT = re.compile(r"{{\s*([^{}]+?)\s*}}")
MAX_TAB_ITEMS = 250
RELATIONSHIPS_FOLDER_NAME = "Relationships"


class UserDetailViewTabsPreference(BasePreference):
    """An ordered detail-tab layout owned or shared through ``BasePreference``."""

    preference_scope_fields = ("content_type",)

    bloomerp_config = BloomerpModelConfig(
        is_internal=True,
        api_settings=ApiSettings(
            enable_auto_generation=True,
            user_access=[
                UserAccessRule(
                    through_field="user",
                    field_actions={
                        "id": ["view"],
                        "name": ["view", "change"],
                    },
                    row_actions=["view", "change"],
                ),
            ],
        ),
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="+",
    )

    class Meta:
        db_table = "bloomerp_user_detail_view_tabs_preference"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "content_type"],
                condition=Q(selected=True),
                name="unique_selected_detail_tabs_preference",
            ),
            models.UniqueConstraint(
                fields=["user", "source_object"],
                condition=Q(source_object__isnull=False),
                name="unique_detail_tabs_preference_reference",
            ),
        ]

    @classmethod
    def create_default_for_user(
        cls,
        user,
        **scope,
    ) -> "UserDetailViewTabsPreference":
        """Create and populate the default detail-tab layout for a model."""
        with transaction.atomic():
            preference = cls.objects.create(
                user=user,
                content_type_id=scope["content_type_id"],
            )
            preference.create_default_items()
        return preference

    @classmethod
    def get_detail_route_options(
        cls,
        model: type[models.Model] | None,
    ) -> list[dict[str, Any]]:
        """Return ordered, one-primary-key detail routes as URL templates."""
        if model is None:
            return []

        options: list[dict[str, Any]] = []
        for route in router.filter(model=model, route_type="detail"):
            if route.nr_of_args() != 1 or not PK_ROUTE_ARGUMENT.search(route.path):
                continue
            route_name = route.url_name
            options.append(
                {
                    "name": route.name,
                    "url": PK_ROUTE_ARGUMENT.sub("{{pk}}", route.path),
                    "is_relationship": route_name.endswith("_relationship"),
                    "priority": cls._default_route_priority(route_name),
                }
            )
        return sorted(options, key=lambda option: option["priority"])

    @staticmethod
    def _default_route_priority(route_name: str) -> int:
        """Keep the established detail-tab order around relationship routes."""
        if route_name.endswith("_detail_overview"):
            return 0
        if route_name.endswith("_detail_files"):
            return 1
        if route_name.endswith("_detail_comments"):
            return 2
        if route_name.endswith("_relationship"):
            return 4
        if route_name.endswith("_detail_delete"):
            return 5
        return 3

    @staticmethod
    def validate_tab_url(url: str) -> str:
        """Validate a root-relative or HTTP(S) URL using only ``{{pk}}``."""
        normalized = url.strip()
        if not normalized:
            raise ValidationError("URL is required.")

        arguments = {
            argument.strip()
            for argument in TEMPLATE_ARGUMENT.findall(normalized)
        }
        if arguments - {"pk"}:
            raise ValidationError("Only the {{pk}} placeholder is supported.")

        parsed = urlsplit(normalized)
        is_internal = (
            not parsed.scheme
            and not parsed.netloc
            and normalized.startswith("/")
        )
        is_external = parsed.scheme in {"http", "https"} and bool(parsed.netloc)
        if not is_internal and not is_external:
            raise ValidationError(
                "Enter an internal URL beginning with / or a complete http(s) URL."
            )
        return normalized

    @staticmethod
    def resolve_tab_url(url: str, object_pk: Any) -> str:
        """Resolve the supported object placeholder in a stored tab URL."""
        return url.replace("{{pk}}", str(object_pk))

    def create_default_items(self) -> None:
        """Populate default routes and group relationship routes in one folder."""
        options = self.get_detail_route_options(self.content_type.model_class())
        relationship_options = [
            option for option in options if option["is_relationship"]
        ]
        top_level_options: list[dict[str, Any] | None] = []
        relationship_marker_added = False
        for option in options:
            if option["is_relationship"]:
                if not relationship_marker_added:
                    top_level_options.append(None)
                    relationship_marker_added = True
                continue
            top_level_options.append(option)

        with transaction.atomic():
            for position, option in enumerate(top_level_options):
                if option is None:
                    folder = UserDetailViewTabItem.objects.create(
                        preference=self,
                        name=RELATIONSHIPS_FOLDER_NAME,
                        url=None,
                        position=position,
                    )
                    UserDetailViewTabItem.objects.bulk_create(
                        [
                            UserDetailViewTabItem(
                                preference=self,
                                parent=folder,
                                name=relationship["name"],
                                url=relationship["url"],
                                position=child_position,
                            )
                            for child_position, relationship in enumerate(
                                relationship_options
                            )
                        ]
                    )
                    continue
                UserDetailViewTabItem.objects.create(
                    preference=self,
                    name=option["name"],
                    url=option["url"],
                    position=position,
                )

    def build_rendered_items(
        self,
        *,
        object_pk: Any,
        request_path: str,
    ) -> list[dict[str, Any]]:
        """Build the ordered tab/folder tree consumed by the detail template."""
        items = list(self.items.select_related("parent").order_by("position", "id"))
        children_by_parent: dict[
            uuid.UUID,
            list[UserDetailViewTabItem],
        ] = defaultdict(list)
        for item in items:
            if item.parent_id:
                children_by_parent[item.parent_id].append(item)

        def render_tab(item: UserDetailViewTabItem) -> dict[str, Any]:
            href = self.resolve_tab_url(item.url or "", object_pk)
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
                        "tabs": [
                            render_tab(child)
                            for child in children_by_parent[item.id]
                        ],
                    }
                )
            else:
                rendered.append({**render_tab(item), "is_folder": False})
        return rendered

    def sync_items(self, payload: Any) -> None:
        """Replace this preference's tree with a validated client snapshot."""
        if not isinstance(payload, list):
            raise ValidationError("Items must be a list.")
        if len(payload) > MAX_TAB_ITEMS:
            raise ValidationError(
                f"A layout can contain at most {MAX_TAB_ITEMS} items."
            )

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
                raise ValidationError(
                    "Every item requires a name of at most 255 characters."
                )

            raw_url = raw_item.get("url")
            url = None if raw_url is None else self.validate_tab_url(str(raw_url))
            raw_parent_id = raw_item.get("parent_id")
            try:
                parent_id = (
                    uuid.UUID(str(raw_parent_id)) if raw_parent_id else None
                )
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
            if (
                item["parent_id"] is not None
                and item["parent_id"] not in folder_ids
            ):
                raise ValidationError(
                    "Tabs may only be placed inside a submitted folder."
                )

        foreign_ids = UserDetailViewTabItem.objects.filter(id__in=seen_ids).exclude(
            preference=self
        )
        if foreign_ids.exists():
            raise ValidationError("An item belongs to a different tabs preference.")

        with transaction.atomic():
            self.items.exclude(id__in=seen_ids).delete()
            existing = {item.id: item for item in self.items.all()}
            saved: dict[uuid.UUID, UserDetailViewTabItem] = {}

            for data in sorted(
                normalized,
                key=lambda item: item["parent_id"] is not None,
            ):
                item = existing.get(data["id"]) or UserDetailViewTabItem(
                    id=data["id"],
                    preference=self,
                )
                item.name = data["name"]
                item.url = data["url"]
                item.position = data["position"]
                item.parent = saved.get(data["parent_id"])
                item.full_clean()
                item.save()
                saved[item.id] = item

    def copy_configuration_to(
        self,
        target: "UserDetailViewTabsPreference",
    ) -> None:
        """Copy this preference's complete tab tree to ``target``."""
        source_items = list(self.items.order_by("parent_id", "position", "id"))
        copied_by_source_id: dict[uuid.UUID, UserDetailViewTabItem] = {}

        with transaction.atomic():
            for source in (item for item in source_items if item.parent_id is None):
                copied_by_source_id[source.id] = UserDetailViewTabItem.objects.create(
                    preference=target,
                    name=source.name,
                    url=source.url,
                    position=source.position,
                )

            for source in (item for item in source_items if item.parent_id is not None):
                UserDetailViewTabItem.objects.create(
                    preference=target,
                    parent=copied_by_source_id[source.parent_id],
                    name=source.name,
                    url=source.url,
                    position=source.position,
                )


class UserDetailViewTabItem(models.Model):
    """A top-level folder when ``url`` is null, otherwise a navigable tab."""

    bloomerp_config = BloomerpModelConfig(
        is_internal=True,
        api_settings=ApiSettings(enable_auto_generation=False),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    preference = models.ForeignKey(
        UserDetailViewTabsPreference,
        on_delete=models.CASCADE,
        related_name="items",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=2048, null=True, blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "bloomerp_user_detail_view_tab_item"
        ordering = ["position", "id"]
        indexes = [
            models.Index(
                fields=["preference", "parent", "position"],
                name="detail_tab_tree_order_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(url__isnull=True) | ~Q(url=""),
                name="detail_tab_url_null_or_nonempty",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def is_folder(self) -> bool:
        return self.url is None

    def clean(self) -> None:
        """Enforce one folder level and keep every tree inside one preference."""
        super().clean()
        errors: dict[str, str] = {}

        if self.url == "":
            self.url = None

        if self.parent_id:
            if self.parent.preference_id != self.preference_id:
                errors["parent"] = "Parent must belong to the same tabs preference."
            elif not self.parent.is_folder:
                errors["parent"] = "A tab cannot contain other items."

            if self.is_folder:
                errors["parent"] = "Folders must be top-level items."

        if self.pk and not self.is_folder and self.children.exists():
            errors["url"] = "An item with children must remain a folder."

        if errors:
            raise ValidationError(errors)
