from copy import copy
from dataclasses import dataclass
from typing import Any, Optional, Type

from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html

from bloomerp.models.base_bloomerp_model import LayoutItem
from bloomerp.models.workspaces.workspace import Workspace
from bloomerp.models.workspaces.tile import Tile
from bloomerp.modules.definition import module_registry
from bloomerp.services.permission_services import UserPermissionManager, create_permission_str
from bloomerp.utils.models import get_list_view_url
from bloomerp.workspaces.analytics_tile.model import AnalyticsTileConfig, AnalyticsTileType
from bloomerp.workspaces.analytics_tile.utils import TileFieldType
from bloomerp.workspaces.base import TileTypeDefinition
from bloomerp.workspaces.dataview_tile.model import DataViewTileConfig
from bloomerp.workspaces.links_tile.model import Link, LinkTileConfig
from bloomerp.workspaces.tiles import TileType
from bloomerp.models.users import User
from bloomerp.services.sectioned_layout_services import AvailableLayoutItem
from django.db.models import Q
from django.forms import Form
from django import forms
from bloomerp.field_types.types import FieldType
from django.contrib.contenttypes.models import ContentType

PRIMITIVE_FIELD_TYPE_MAP = {
    TileFieldType.TEXT.value.key: FieldType.CHAR_FIELD,
    TileFieldType.NUMERIC.value.key: FieldType.DECIMAL_FIELD,
    TileFieldType.DATE.value.key: FieldType.DATE_FIELD,
    TileFieldType.DATETIME.value.key: FieldType.DATE_TIME_FIELD,
    TileFieldType.BOOL.value.key: FieldType.BOOLEAN_FIELD,
}



def select_workspace(workspace: Workspace, user: User) -> Workspace:
    """Select an owned or shared workspace for the user's module scope."""
    from bloomerp.services.preference_services import PreferenceManager

    return PreferenceManager(user).select(workspace)


def ensure_default_workspace_tiles_for_module(user, module_id: str) -> None:
    module = module_registry.get(module_id)
    if not module:
        return

    child_modules = module_registry.get_children(module.full_id or module.id)
    if child_modules:
        for child_module in child_modules:
            links = [
                Link(url=f"/{child_module.route_path}/", name=child_module.name, is_internal=True)
            ]
            config = LinkTileConfig(links=links).model_dump()
            description = f"Navigate to the '{child_module.name}' module."

            Tile.objects.get_or_create(
                created_by=user,
                updated_by=user,
                name=child_module.name,
                type=TileType.LINKS_TILE.name,
                description=description,
                schema=config,
                auto_generated=True,
            )
        return

    links = []
    for model in module_registry.get_models_for_module(module_id):
        links.append(
            Link(
                url=reverse(get_list_view_url(model)),
                name=model._meta.verbose_name_plural,
                is_internal=True,
            )
        )

    if not links:
        return

    config = LinkTileConfig(links=links).model_dump()
    description = f"Links to the different models of the '{module.name}' module."
    Tile.objects.get_or_create(
        created_by=user,
        updated_by=user,
        name=module.name,
        type=TileType.LINKS_TILE.name,
        description=description,
        schema=config,
        auto_generated=True,
    )


def create_default_sidebar(
        user,
):
    modules = module_registry.get_enabled()
    

def render_tile_to_string(
    tile:Tile, 
    request:HttpRequest
    ) -> str:
    """Renders a tile to a string, given the tile and the user object

    Args:
        tile (Tile): the tile object
        user (User): the user object

    Returns:
        str: the html string
    """
    # 1. Get the tile type
    tile_type = TileType.from_key(tile.type)

    # 2. Get the config object
    config = tile_type.value.model( 
        **tile.schema
    )

    # 3. Get the render class. Saved canvases receive their persistence context;
    # previews call the renderer directly without a Tile instance.
    render_kwargs = {"tile": tile} if tile_type == TileType.CANVAS_TILE else {}
    return tile_type.value.render_cls.render(config=config, request=request, **render_kwargs)


def build_workspace_layout_item(
    *,
    tile: Tile,
    request: HttpRequest,
    colspan: int = 1,
    config: dict | None = None,
) -> LayoutItem:
    """Transform a tile into the shared layout item rendered by every layout."""
    render_request = copy(request)
    render_request.GET = request.GET.copy()
    for transport_param in ("colspan", "max_cols"):
        render_request.GET.pop(transport_param, None)
    render_request.GET["tile_id"] = str(tile.pk)

    try:
        content = render_tile_to_string(tile, render_request)
    except Exception as exc:
        content = format_html('<div class="alert alert-danger">{}</div>', exc)

    return LayoutItem(
        id=str(tile.pk),
        colspan=colspan,
        config=config or {},
        icon=tile.icon,
        label=tile.name,
        content=content,
        component_name="workspace-tile",
        border=True,
        edit_url=(
            f"{reverse('tiles_detail_update_tile', kwargs={'pk': tile.pk})}"
            "?reset_wizard=true"
        ),
        search_keywords=tile.get_type_display(),
    )


@dataclass
class WorkspaceFilter:
    field:str
    type:str
    label:str

class WorkspaceManager:
    def __init__(self, workspace:Workspace):
        self.workspace = workspace
        
    def get_filter_form(self) -> Type[Form]:
        """Returns the filter form for a particular workspace.

        Returns:
            Type[Form]: the form
        """
        attrs = {}
        
        for tile in self.workspace.get_tiles():
            match TileType.from_key(tile.type):
                case TileType.ANALYTICS_TILE:
                    config = AnalyticsTileConfig(**tile.schema)
            
                    if not config.filters:
                        continue
                    
                    for filter_config in config.filters.values():
                        match filter_config.type:
                            case "text":
                                field_type = FieldType.CHAR_FIELD
                                
                                attrs
                                
                
        return type("FilterForm", (Form,), attrs)
 
    def get_filter_fields(self, user:User) -> dict[str, WorkspaceFilter]:
        """Returns all the filterable fields for a particular 

        Args:
            user (User): the user object. Some filters are not accessible to users

        Returns:
            dict[str, WorkspaceFilter]:
        """
        result = {}
        # TODO: no collision management right now
        
        for tile in self.workspace.get_tiles():
            match TileType.from_key(tile.type):
                case TileType.ANALYTICS_TILE:
                    config = AnalyticsTileConfig(**tile.schema)
            
                    if not config.filters:
                        continue
                    
                    for filter_config in config.filters.values():
                        result[filter_config.field] = WorkspaceFilter(
                            field=filter_config.field,
                            type=PRIMITIVE_FIELD_TYPE_MAP[filter_config.type].value.id,
                            label=filter_config.field.replace("_", " ").title()
                        )
                # case TileType.DATAVIEW_TILE:
                #     config = DataViewTileConfig(**tile.schema)
                #     manager = UserPermissionManager(user)
                #     content_type = ContentType.objects.get(id=config.content_type_id)
                #     fields = manager.get_accessible_fields(
                #         content_type,
                #         create_permission_str(
                #             content_type.model_class(),
                #             "view"
                #         )
                #     )
                #     for field in fields:
                #         result[field.field] = WorkspaceFilter(
                #             field=field.field,
                #             type=field.field_type,
                #             label=field.title
                #         )
                           
        return result


class UserWorkspaceService:
    def __init__(self, user:User):
        self.user = user

    def get_available_workspace_tiles(self) -> list[dict[str, Any]]:
        """Returns the available workspace tiles for a particular user

        Returns:
            list[dict[str, Any]]: the list of dictionaries containing the workspace tiles
        """
        # Or created by user OR auto generated
        
        tiles = Tile.objects.filter(
            Q(created_by=self.user) | Q(auto_generated=True)
        )
        return [
            AvailableLayoutItem(
                id=tile.id,
                title=tile.name,
                description=tile.description,
                icon=tile.icon,
                search_keywords=tile.get_type_display(),
            )
            for tile in tiles
        ]

        
