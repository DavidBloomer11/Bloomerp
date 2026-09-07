from bloomerp.router import router
from bloomerp.views.api.generic.base import AUTO_API_MODELS, BaseModelApiView


@router.register(
    path="",
    route_type="api_model",
    models=AUTO_API_MODELS
)
class BloomerpListApiView(BaseModelApiView):
    actions = {
        "get": "list",
        "post": "create",
    }
