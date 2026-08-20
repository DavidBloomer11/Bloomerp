import json
from django.http import HttpResponse, HttpRequest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.urls import reverse
from bloomerp.models import ApplicationField, BloomerpModel
from bloomerp.permissions.definition import BloomerpPermission
from bloomerp.router import router
from bloomerp.services.object_services import string_search_on_queryset
from bloomerp.permissions.manager import UserPolicyManager
from bloomerp.services.related_value_services import get_allowed_related_queryset

def _get_detail_url(obj) -> str:
    """Helper function to get the detail url"""
    try:
        return obj.get_absolute_url()
    except Exception:
        try:
            from bloomerp.utils.models import get_detail_view_url
            return reverse(get_detail_view_url(obj.__class__), kwargs={"pk": obj.pk})
        except Exception:
            return ""


@router.register(
    path="components/search-objects/<int:content_type_id>/",
    name="components_search_objects",
)
def search_objects(request:HttpRequest, content_type_id:int) -> HttpResponse:
    """Component that returns search results for a given query

    Args:
        request (HttpRequest): request object
        content_type_id (int): content type id

    Returns:
        HttpResponse: the response
    """
    Model : BloomerpModel = ContentType.objects.get_for_id(content_type_id).model_class()
    query = request.GET.get('fk_search_results_query')
    permission_manager = UserPolicyManager(request.user)
    
    # Get the base queryset
    application_field_id = request.GET.get("application_field_id")
    if application_field_id:
        try:
            application_field = ApplicationField.objects.select_related(
                "content_type", "related_model"
            ).get(pk=application_field_id)
            base_queryset = get_allowed_related_queryset(application_field, request.user)
            if ContentType.objects.get_for_model(base_queryset.model).pk != content_type_id:
                return HttpResponse("Field does not relate to this content type", status=400)
        except (ApplicationField.DoesNotExist, ValidationError, ValueError, TypeError):
            return HttpResponse("Invalid application field", status=400)
    else:
        base_queryset = permission_manager.get_queryset(
            Model,
            BloomerpPermission.VIEW
        )
    
    if query:
        results = string_search_on_queryset(
            queryset=base_queryset, 
            query=query
        )
    else:
        # Take first 10 objects
        results = base_queryset[:10]
    
    # Construct response
    
    resp = {
        'objects' : [
            {
                'id': str(obj.pk),
                'string_representation': str(obj),
                'detail_url': _get_detail_url(obj),
            } for obj in results
        ]
    }
    
    return HttpResponse(
        json.dumps(resp),
        content_type="application/json"
    )
