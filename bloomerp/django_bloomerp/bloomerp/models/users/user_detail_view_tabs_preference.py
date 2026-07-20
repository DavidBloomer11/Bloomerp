from __future__ import annotations

import uuid

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
        from bloomerp.services.detail_tab_services import create_default_tab_items

        with transaction.atomic():
            preference = cls.objects.create(
                user=user,
                content_type_id=scope["content_type_id"],
            )
            create_default_tab_items(preference)
        return preference

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
