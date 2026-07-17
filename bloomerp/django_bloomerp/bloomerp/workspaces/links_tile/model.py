from collections.abc import Iterator
from typing import Literal, Optional, Self

from django.utils.translation import gettext_lazy as _
from pydantic import BaseModel, Field

from bloomerp.models.workspaces.sidebar_item import is_internal_sidebar_url
from bloomerp.workspaces.base import (
    BaseTileConfig,
    TileOperationDefinition,
    TileOperationHandler,
    TileOperationHandlerRespone,
)


class Link(BaseModel):
    url: str = ""
    name: str
    is_internal: bool = False
    is_folder: bool = False
    children: list["Link"] = Field(default_factory=list)


class LinkTileConfig(BaseTileConfig):
    links: list[Link]

    @classmethod
    def get_default(cls) -> Self:
        return cls(
            links=[
                Link(
                    url="/",
                    name="Home",
                    is_internal=True,
                )
            ]
        )

    @classmethod
    def get_operation(cls, operation):
        return {
            "add_link": TileOperationDefinition(AddLinkOperation, AddLinkHandler),
            "add_folder": TileOperationDefinition(AddFolderOperation, AddFolderHandler),
            "remove_link": TileOperationDefinition(RemoveLinkOperation, RemoveLinkHandler),
            "update_link": TileOperationDefinition(UpdateLinkOperation, UpdateLinkHandler),
            "move_link": TileOperationDefinition(MoveLinkOperation, MoveLinkHandler),
        }[operation]


def _get_items_at_path(config: LinkTileConfig, parent_path: list[int]) -> list[Link]:
    """Return the list of items contained by the folder at ``parent_path``."""
    items = config.links
    for index in parent_path:
        if index < 0 or index >= len(items):
            raise ValueError(_("The selected folder no longer exists"))
        folder = items[index]
        if not folder.is_folder:
            raise ValueError(_("Links can only be nested inside folders"))
        items = folder.children
    return items


def _get_item(config: LinkTileConfig, path: list[int]) -> Link:
    """Return one link or folder using its index path."""
    if not path:
        raise ValueError(_("No link was selected"))
    items = _get_items_at_path(config, path[:-1])
    index = path[-1]
    if index < 0 or index >= len(items):
        raise ValueError(_("The selected link no longer exists"))
    return items[index]


def _iter_links(items: list[Link]) -> Iterator[Link]:
    """Yield links and folders from a nested configuration."""
    for item in items:
        yield item
        yield from _iter_links(item.children)


class AddLinkOperation(BaseModel):
    url: str
    name: Optional[str] = None
    parent_path: list[int] = Field(default_factory=list)


class AddLinkHandler(TileOperationHandler):
    @staticmethod
    def handle(config: LinkTileConfig, data: AddLinkOperation) -> TileOperationHandlerRespone:
        """Add a validated link to the selected folder."""
        name = (data.name or "").strip()
        url = data.url.strip()
        if not name:
            return TileOperationHandlerRespone(config, _("Please add a name to the link"), "warning")
        if not url:
            return TileOperationHandlerRespone(config, _("Please add a URL to the link"), "warning")
        if any(not link.is_folder and link.url == url for link in _iter_links(config.links)):
            return TileOperationHandlerRespone(config, _("Link already existed"), "warning")

        items = _get_items_at_path(config, data.parent_path)
        items.append(Link(url=url, name=name, is_internal=is_internal_sidebar_url(url)))
        return TileOperationHandlerRespone(config, _("Link added"))


class AddFolderOperation(BaseModel):
    name: str
    parent_path: list[int] = Field(default_factory=list)


class AddFolderHandler(TileOperationHandler):
    @staticmethod
    def handle(config: LinkTileConfig, data: AddFolderOperation) -> TileOperationHandlerRespone:
        """Add a folder to the selected nesting level."""
        name = data.name.strip()
        if not name:
            return TileOperationHandlerRespone(config, _("Please add a name to the folder"), "warning")

        items = _get_items_at_path(config, data.parent_path)
        items.append(Link(name=name, is_folder=True))
        return TileOperationHandlerRespone(config, _("Folder added"))


class RemoveLinkOperation(BaseModel):
    path: list[int]


class RemoveLinkHandler(TileOperationHandler):
    @staticmethod
    def handle(config: LinkTileConfig, data: RemoveLinkOperation) -> TileOperationHandlerRespone:
        """Remove one link or folder subtree by index path."""
        if not data.path:
            raise ValueError(_("No link was selected"))
        items = _get_items_at_path(config, data.path[:-1])
        index = data.path[-1]
        if index < 0 or index >= len(items):
            raise ValueError(_("The selected link no longer exists"))
        items.pop(index)
        return TileOperationHandlerRespone(config, _("Item removed"))


class UpdateLinkOperation(BaseModel):
    path: list[int]
    url: str = ""
    name: str


class UpdateLinkHandler(TileOperationHandler):
    @staticmethod
    def handle(config: LinkTileConfig, data: UpdateLinkOperation) -> TileOperationHandlerRespone:
        """Update the selected link or folder without changing its position."""
        item = _get_item(config, data.path)
        name = data.name.strip()
        url = data.url.strip()
        if not name:
            return TileOperationHandlerRespone(config, _("Please add a name"), "warning")
        if not item.is_folder and not url:
            return TileOperationHandlerRespone(config, _("Please add a URL to the link"), "warning")

        item.name = name
        if not item.is_folder:
            item.url = url
            item.is_internal = is_internal_sidebar_url(url)
        return TileOperationHandlerRespone(config, _("Item updated"))


class MoveLinkOperation(BaseModel):
    path: list[int]
    direction: Literal["up", "down"]


class MoveLinkHandler(TileOperationHandler):
    @staticmethod
    def handle(config: LinkTileConfig, data: MoveLinkOperation) -> TileOperationHandlerRespone:
        """Move an item up or down among its current siblings."""
        if not data.path:
            raise ValueError(_("No link was selected"))
        items = _get_items_at_path(config, data.path[:-1])
        index = data.path[-1]
        destination = index - 1 if data.direction == "up" else index + 1
        if index < 0 or index >= len(items) or destination < 0 or destination >= len(items):
            return TileOperationHandlerRespone(config, _("Item cannot be moved further"), "info")

        items[index], items[destination] = items[destination], items[index]
        return TileOperationHandlerRespone(config, _("Item moved"))
