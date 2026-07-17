from django.http import HttpRequest

from bloomerp.components.objects.dataviews.dataview import data_view
from bloomerp.models.users.user_list_view_preference import UserListViewPreference
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.workspaces.base import BaseTileRenderer
from bloomerp.workspaces.dataview_tile.model import DataViewTileConfig


class DataViewTileRenderer(BaseTileRenderer):
    @classmethod
    def render(cls, config: DataViewTileConfig, request: HttpRequest) -> str:
        """Render a permission-aware data view from the tile configuration."""
        if config.content_type_id is None:
            return ""

        preference = None
        if config.list_view_preference_id is not None:
            preference = (
                PreferenceManager(request.user)
                .get_available(
                    UserListViewPreference,
                    {"content_type_id": config.content_type_id},
                )
                .filter(pk=config.list_view_preference_id)
                .first()
            )
            if preference is not None:
                preference = preference.effective_preference

        return data_view(
            request,
            content_type_id=config.content_type_id,
            preference=preference,
        ).content.decode("utf-8")
