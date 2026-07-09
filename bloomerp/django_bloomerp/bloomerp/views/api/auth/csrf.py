from django.http import HttpRequest, JsonResponse
from django.middleware.csrf import get_token

from bloomerp.router import router
from bloomerp.views.api.auth.common import (
    BaseSessionAuthApiView,
    json_not_found,
    session_auth_enabled,
)


@router.register(
    path="auth/csrf/",
    route_type="api",
    name="csrf",
)
class CsrfView(BaseSessionAuthApiView):
    def get(self, request: HttpRequest) -> JsonResponse:
        if not session_auth_enabled():
            return json_not_found("Session auth endpoints are disabled.")

        return JsonResponse({"csrfToken": get_token(request)})
