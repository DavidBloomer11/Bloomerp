from typing import Any, Self

from pydantic import BaseModel, Field

from bloomerp.workspaces.base import (
    BaseTileConfig,
    TileOperationDefinition,
    TileOperationHandler,
    TileOperationHandlerRespone,
)


class CanvasTileConfig(BaseTileConfig):
    content: dict[str, Any] = Field(default_factory=dict)
    height: int = Field(default=384, ge=256, le=1600)

    @classmethod
    def get_default(cls, *args, **kwargs) -> Self:
        return cls()

    @classmethod
    def get_operation(cls, operation: str) -> TileOperationDefinition:
        return {
            "set_height": TileOperationDefinition(
                validation_model=SetCanvasHeightOperation,
                handler=SetCanvasHeightHandler,
            ),
        }[operation]


class SetCanvasHeightOperation(BaseModel):
    height: int = Field(ge=256, le=1600)


class SetCanvasHeightHandler(TileOperationHandler):
    @staticmethod
    def handle(
        config: CanvasTileConfig,
        data: SetCanvasHeightOperation,
    ) -> TileOperationHandlerRespone:
        config.height = data.height
        return TileOperationHandlerRespone(config=config, message="")
