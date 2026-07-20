from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest, JsonResponse

from bloomerp.router import router
from bloomerp.services.object_services import get_object_detail_url, string_search_on_queryset
from bloomerp.services.permission_services import UserPermissionManager, create_permission_str
from bloomerp.services.search_services import get_accessible_search_models
from bloomerp.utils.labels import safe_object_label


@router.register(
    path="components/search-content-objects/",
    name="components_search_content_objects",
)
@login_required
def search_content_objects(request: HttpRequest) -> JsonResponse:
    """Search permission-visible objects across accessible content types."""
    query = (request.GET.get("q") or "").strip()
    if not query:
        return JsonResponse({"objects": []})

    permission_manager = UserPermissionManager(request.user)
    objects = []
    for model in get_accessible_search_models(request.user, permission_manager):
        queryset = permission_manager.get_queryset(
            model,
            create_permission_str(model, "view"),
        )
        matches = string_search_on_queryset(queryset, query)[:5]
        content_type = ContentType.objects.get_for_model(model)
        for obj in matches:
            objects.append(
                {
                    "content_type_id": str(content_type.pk),
                    "object_id": str(obj.pk),
                    "label": safe_object_label(obj),
                    "model_label": str(model._meta.verbose_name),
                    "detail_url": get_object_detail_url(obj),
                }
            )
            if len(objects) >= 20:
                return JsonResponse({"objects": objects})

    return JsonResponse({"objects": objects})
