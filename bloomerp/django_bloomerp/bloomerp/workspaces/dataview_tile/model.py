from typing import Self

from django.utils.translation import gettext_lazy as _
from pydantic import Field

from bloomerp.workspaces.base import (
    BaseTileConfig,
    TileOperationDefinition,
    TileOperationHandler,
    TileOperationHandlerRespone,
)
from bloomerp.workspaces.dataview_tile.form import DataViewTileForm


class DataViewTileConfig(BaseTileConfig):
    content_type_id: int | None = None
    list_view_preference_id: int | None = None
    actions: list[str] | None = None
    initial_query_params: dict[str, object] = Field(
        default_factory=dict,
        description="Query parameters applied when the data view tile is rendered.",
    )

    @classmethod
    def get_default(cls, *args, **kwargs) -> Self:
        return cls(
            content_type_id=kwargs.get("content_type_id"),
            list_view_preference_id=kwargs.get("list_view_preference_id"),
        )

    @classmethod
    def get_operation(cls, operation: str) -> TileOperationDefinition:
        return {
            "set_form": TileOperationDefinition(
                DataViewTileForm,
                SetDataViewHandler,
            ),
        }[operation]


class SetDataViewHandler(TileOperationHandler):
    @staticmethod
    def handle(
        config: DataViewTileConfig,
        data: DataViewTileForm,
    ) -> TileOperationHandlerRespone:
        if not data.is_valid():
            return TileOperationHandlerRespone(
                config,
                _("Please correct the data view configuration."),
                "warning",
            )

        content_type = data.cleaned_data["content_type_id"]
        preference = data.cleaned_data["list_view_preference_id"]
        actions = data.cleaned_data["actions"]
        initial_query_params = data.cleaned_data["initial_query_params"]

        config.content_type_id = content_type.pk
        config.list_view_preference_id = preference.pk if preference else None
        config.actions = actions
        config.initial_query_params = initial_query_params

        return TileOperationHandlerRespone(
            config,
            _("Data view updated"),
        )
