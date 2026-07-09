from bloomerp.router import router
from bloomerp.views.api.generic.base import AUTO_API_MODELS, BaseModelApiView


@router.register(
    path="",
    route_type="api_detail",
    models=AUTO_API_MODELS
)
class BloomerpDetailAPIView(BaseModelApiView):
    actions = {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    }
