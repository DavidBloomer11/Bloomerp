from django.http import HttpRequest, JsonResponse

from bloomerp.router import router
from bloomerp.views.api.auth.common import (
    BaseSessionAuthApiView,
    json_not_found,
    serialize_user,
    session_auth_enabled,
)


@router.register(
    path="auth/session/",
    route_type="api",
    name="session",
)
class SessionView(BaseSessionAuthApiView):
    def get(self, request: HttpRequest) -> JsonResponse:
        if not session_auth_enabled():
            return json_not_found("Session auth endpoints are disabled.")

        if not request.user.is_authenticated:
            return JsonResponse({"authenticated": False})

        return JsonResponse(
            {
                "authenticated": True,
                "user": serialize_user(request.user),
            }
        )
