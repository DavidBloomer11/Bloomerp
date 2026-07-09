from django.contrib.auth import logout
from django.http import HttpRequest, JsonResponse

from bloomerp.router import router
from bloomerp.views.api.auth.common import (
    BaseSessionAuthApiView,
    json_not_found,
    session_auth_enabled,
)


@router.register(
    path="auth/logout/",
    route_type="api",
    name="api_logout",
)
class LogoutView(BaseSessionAuthApiView):
    def post(self, request: HttpRequest) -> JsonResponse:
        if not session_auth_enabled():
            return json_not_found("Session auth endpoints are disabled.")

        logout(request)
        return JsonResponse({"authenticated": False})
