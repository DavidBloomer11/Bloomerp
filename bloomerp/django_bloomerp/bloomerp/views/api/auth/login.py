from django.contrib.auth import authenticate, login
from django.http import HttpRequest, JsonResponse

from bloomerp.router import router
from bloomerp.views.api.auth.common import (
    BaseSessionAuthApiView,
    get_login_credentials,
    json_not_found,
    parse_request_data,
    serialize_user,
    session_auth_enabled,
)


@router.register(
    path="auth/login/",
    route_type="api",
    name="api_login",
)
class LoginView(BaseSessionAuthApiView):
    def post(self, request: HttpRequest) -> JsonResponse:
        if not session_auth_enabled():
            return json_not_found("Session auth endpoints are disabled.")

        data = parse_request_data(request)
        credentials = get_login_credentials(data)
        user = authenticate(request, **credentials)

        if user is None:
            return JsonResponse(
                {
                    "authenticated": False,
                    "detail": "Invalid credentials.",
                },
                status=400,
            )

        login(request, user)
        return JsonResponse(
            {
                "authenticated": True,
                "user": serialize_user(user),
            }
        )
