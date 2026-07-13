from django.db import models
from django.db.models import Q

from bloomerp.models.users.base_preference import BasePreference


class Sidebar(BasePreference):
    """A named sidebar configuration belonging to a user."""
    class Meta:
        db_table = "bloomerp_sidebar"
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(selected=True),
                name="unique_selected_sidebar_preference",
            ),
        ]

    @property
    def items(self):
        from bloomerp.models.workspaces.sidebar_item import SidebarItem

        return SidebarItem.objects.filter(sidebar=self).order_by("position")
    
    @property
    def root_items(self):
        from bloomerp.models.workspaces.sidebar_item import SidebarItem

        return SidebarItem.objects.filter(sidebar=self, parent=None).order_by("position")
