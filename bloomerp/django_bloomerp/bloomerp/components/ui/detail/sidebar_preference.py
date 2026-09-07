from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_POST

from bloomerp.models.users.user import DetailSidebarViewPreference
from bloomerp.router import router


@router.register(
    path="components/detail-sidebar/preference/",
    name="components_detail_sidebar_preference",
)
@login_required
@require_POST
def detail_sidebar_preference(request: HttpRequest) -> HttpResponse:
    """Persist the authenticated user's preferred detail sidebar panel."""
    view = request.POST.get("view")
    if view not in DetailSidebarViewPreference.values:
        return JsonResponse({"status": "error", "error": "Invalid sidebar view."}, status=400)

    request.user.detail_sidebar_view_preference = view
    request.user.save(update_fields=["detail_sidebar_view_preference"])
    return JsonResponse({"status": "ok", "view": view})
