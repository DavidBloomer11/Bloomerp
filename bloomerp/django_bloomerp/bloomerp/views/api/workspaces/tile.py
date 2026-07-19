import json
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from bloomerp.models.workspaces.tile import Tile
from bloomerp.router import router
from bloomerp.workspaces.canvas_tile.model import CanvasTileConfig
from bloomerp.workspaces.tiles import TileType


def _parse_state(request: HttpRequest) -> dict[str, Any] | None:
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    state = payload.get("state") if isinstance(payload, dict) else None
    return state if isinstance(state, dict) else None


@router.register(
    path="canvas-state/",
    route_type="api_detail",
    models=[Tile],
    url_name="api_tile_canvas_state",
)
@require_POST
def save_canvas_state(request: HttpRequest, pk, model: type[Tile]) -> HttpResponse:
    """Persist the current Excalidraw state for a saved canvas tile."""
    tile = get_object_or_404(Tile, pk=pk)

    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({"detail": "Authentication required."}, status=401)

    # TODO: Check whether the user has access to a dashboard with this tile. For now, low risk so user.is_authenticated is enough.
    
    if TileType.from_key(tile.type) != TileType.CANVAS_TILE:
        return JsonResponse({"detail": "Tile is not a canvas."}, status=400)

    state = _parse_state(request)
    if state is None:
        return JsonResponse({"detail": "A JSON object named 'state' is required."}, status=400)

    config = CanvasTileConfig(**tile.schema)
    config.content = state
    tile.schema = config.model_dump()
    tile.updated_by = request.user
    tile.save(update_fields=["schema", "updated_by", "datetime_updated"])

    return JsonResponse({"saved": True})
