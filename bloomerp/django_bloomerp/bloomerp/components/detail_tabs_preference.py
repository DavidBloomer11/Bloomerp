import json

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404

from bloomerp.models.users.user_detail_view_tabs_preference import (
    UserDetailViewTabsPreference,
)
from bloomerp.router import router
from bloomerp.services.preference_services import PreferenceManager


@router.register(
    path="components/detail-tabs/preference/",
    name="components_detail_tabs_preference",
)
@login_required
def detail_tabs_preference(request: HttpRequest) -> HttpResponse:
    """Persist the selected, owner-managed detail-tab tree."""
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    content_type_id = request.POST.get("content_type_id")
    if not content_type_id:
        return HttpResponse("Missing content_type_id", status=400)
    try:
        content_type_pk = int(content_type_id)
    except ValueError:
        return HttpResponse("Invalid content_type_id", status=400)
    content_type = get_object_or_404(ContentType, id=content_type_pk)

    manager = PreferenceManager(request.user)
    preference = manager.get_or_create_selected(
        UserDetailViewTabsPreference,
        {"content_type_id": content_type.pk},
    )
    if preference is None or not manager.can_manage(preference):
        return HttpResponse("You cannot edit this tabs preference.", status=403)

    try:
        payload = json.loads(request.POST.get("items", "[]"))
        preference.sync_items(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        message = exc.messages[0] if isinstance(exc, ValidationError) else "Invalid JSON."
        return JsonResponse({"status": "error", "error": message}, status=400)

    return JsonResponse({"status": "ok"})
