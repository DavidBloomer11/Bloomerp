import json
from typing import TYPE_CHECKING

from django.http import HttpRequest
from django.urls import reverse

from bloomerp.workspaces.base import BaseTileRenderer
from bloomerp.workspaces.canvas_tile.model import CanvasTileConfig

if TYPE_CHECKING:
    from bloomerp.models.workspaces.tile import Tile


class CanvasTileRenderer(BaseTileRenderer):
    template_name = "cotton/features/workspaces/tiles/canvas.html"

    @classmethod
    def render(
        cls,
        config: CanvasTileConfig,
        request: HttpRequest,
        tile: "Tile | None" = None,
    ) -> str:
        """
        Render the canvas tile based on the provided configuration.

        Args:
            config (CanvasTileConfig): The configuration for the canvas tile.

        Returns:
            str: The rendered HTML for the canvas tile.
        """
        context = {
            "content_json": json.dumps(config.content),
            "height": config.height,
            "save_url": reverse("api_tile_canvas_state", kwargs={"pk": tile.pk}) if tile else "",
        }
        return cls.render_to_string(context)
