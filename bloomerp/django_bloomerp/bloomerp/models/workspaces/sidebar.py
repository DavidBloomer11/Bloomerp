from django.utils.translation import gettext_lazy as _
from django.db import models, transaction
from django.db.models import Q

from bloomerp.models.users.base_preference import BasePreference


class Sidebar(BasePreference):
    """A named sidebar configuration belonging to a user."""
    class Meta:
        verbose_name = _("Sidebar")
        verbose_name_plural = _("Sidebars")
        db_table = "bloomerp_sidebar"
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(selected=True),
                name="unique_selected_sidebar_preference",
            ),
        ]

    @classmethod
    def create_default_for_user(cls, user, **scope):
        return cls.objects.create(
            user=user,
            name="My Sidebar",
            selected=True,
        )

    @classmethod
    def copy_preference_for_user(
        cls,
        *,
        user,
        source: "Sidebar",
        name: str,
        scope: dict | None = None,
    ) -> "Sidebar":
        """Copy a sidebar and its complete item tree."""
        from bloomerp.models.workspaces.sidebar_item import SidebarItem

        with transaction.atomic():
            sidebar = cls._create_preference_copy(
                user=user,
                source=source,
                name=name,
                scope=scope,
            )
            pending = list(source.items.order_by("position", "id"))
            copied_by_source_id: dict[int, SidebarItem] = {}

            while pending:
                remaining: list[SidebarItem] = []
                for item in pending:
                    if (
                        item.parent_id is not None
                        and item.parent_id not in copied_by_source_id
                    ):
                        remaining.append(item)
                        continue

                    copied_by_source_id[item.pk] = SidebarItem.objects.create(
                        sidebar=sidebar,
                        parent=copied_by_source_id.get(item.parent_id),
                        name=item.name,
                        icon=item.icon,
                        url=item.url,
                        is_folder=item.is_folder,
                        position=item.position,
                        color=item.color,
                    )

                if len(remaining) == len(pending):
                    raise ValueError("Sidebar item tree contains an invalid parent cycle.")
                pending = remaining

        return sidebar

    @property
    def items(self):
        from bloomerp.models.workspaces.sidebar_item import SidebarItem

        return SidebarItem.objects.filter(sidebar=self).order_by("position")
    
    @property
    def root_items(self):
        from bloomerp.models.workspaces.sidebar_item import SidebarItem

        return SidebarItem.objects.filter(sidebar=self, parent=None).order_by("position")

    @property
    def item_tree(self):
        """Return the complete sidebar tree after loading its items once."""
        from bloomerp.models.workspaces.sidebar_item import SidebarItem

        items = list(
            SidebarItem.objects.filter(sidebar=self).order_by("position", "id")
        )
        children_by_parent_id = {item.id: [] for item in items}
        root_items = []

        for item in items:
            item.tree_children = children_by_parent_id[item.id]
            if item.parent_id is None:
                root_items.append(item)
            else:
                parent_children = children_by_parent_id.get(item.parent_id)
                if parent_children is not None:
                    parent_children.append(item)

        return root_items
