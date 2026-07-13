from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Case, IntegerField, QuerySet, When
from django.urls import reverse

from bloomerp.models.base_bloomerp_model import BloomerpModel, FieldLayout, LayoutRow
from bloomerp.models.mixins.content_layout_model_mixin import ContentLayoutModelMixin
from bloomerp.models.users.base_preference import BasePreference
from bloomerp.models.users.user import AbstractBloomerpUser
from bloomerp.models.workspaces.tile import Tile


class Workspace(ContentLayoutModelMixin, BasePreference):
    """A selectable, shareable workspace preference scoped by module."""

    preference_scope_fields = ("module_id",)

    class Meta(BloomerpModel.Meta):
        managed = True
        db_table = "bloomerp_workspace"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "module_id"],
                condition=models.Q(selected=True, module_id__isnull=False),
                name="unique_selected_workspace_per_user_module",
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(selected=True, module_id__isnull=True),
                name="unique_selected_general_workspace_per_user",
            ),
            models.UniqueConstraint(
                fields=["user", "source_object"],
                condition=models.Q(source_object__isnull=False),
                name="unique_workspace_preference_reference",
            ),
        ]

    module_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default=None,
    )

    def __str__(self):
        return self.name

    @classmethod
    def create_default_for_user(
        cls,
        user: AbstractBloomerpUser,
        **scope,
    ) -> "Workspace":
        """Create the default workspace for a user's module scope.

        Example:
            workspace = Workspace.create_default_for_user(
                user,
                module_id="sales",
            )
        """
        return cls.objects.create(
            user=user,
            name="Default",
            module_id=scope.get("module_id"),
            layout=FieldLayout(
                rows=[LayoutRow(columns=4, title="My Workspace", items=[])]
            ).model_dump(),
            selected=True,
        )

    def get_absolute_url(self):
        return reverse("workspace", kwargs={"pk": self.pk})

    def get_tiles(self) -> QuerySet[Tile]:
        """Returns the tiles that are on this workspace

        Returns:
            QuerySet[Tile]: the tiles available on this
        """
        tile_ids: list[Any] = []
        seen_tile_ids: set[Any] = set()

        for row in self.layout_obj.rows:
            for item in row.items:
                try:
                    tile_id = Tile._meta.pk.to_python(item.id)
                except (TypeError, ValueError, ValidationError):
                    continue

                if tile_id in seen_tile_ids:
                    continue

                tile_ids.append(tile_id)
                seen_tile_ids.add(tile_id)

        if not tile_ids:
            return Tile.objects.none()

        preserved_order = Case(
            *[
                When(pk=tile_id, then=position)
                for position, tile_id in enumerate(tile_ids)
            ],
            output_field=IntegerField(),
        )

        return Tile.objects.filter(pk__in=tile_ids).order_by(preserved_order)
