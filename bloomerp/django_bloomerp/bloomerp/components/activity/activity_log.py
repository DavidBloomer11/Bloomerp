from django.http import HttpRequest, HttpResponse
from bloomerp.permissions.definition import BloomerpPermission
from bloomerp.router import router
from bloomerp.services.activity_log_services import ActivityLogManager
from django.apps import apps
from django.shortcuts import render
from django.utils.translation import gettext as _
from bloomerp.permissions.manager import UserPolicyManager

@router.register(
    path="components/activity-log/",
    url_name="components_activity_log",
)
def activity_log(request:HttpRequest) -> HttpResponse:
    object_id = request.GET.get("object_id")
    content_type_id = request.GET.get("content_type_id")
    
    # Get content type and model class
    try:
        content_type_id_int = int(content_type_id) if content_type_id else None
    except ValueError:
        return HttpResponse(_("Invalid content type ID"), status=400)
    
    content_type = apps.get_model("contenttypes.ContentType").objects.filter(id=content_type_id_int).first() if content_type_id_int else None
    model_class = content_type.model_class() if content_type else None
    object_instance = model_class.objects.filter(id=object_id).first() if model_class and object_id else None
    
    if not ActivityLogManager.should_record_change(model_class):
        return HttpResponse(_("Activity logging is not enabled for this model."), status=400)
    
    if not object_id or not content_type_id:
        return HttpResponse(_("Missing object ID or content type ID"), status=400)
    
    if not UserPolicyManager(request.user).has_access_to_object(
        object_instance,
        BloomerpPermission.VIEW
    ):
        return HttpResponse("No access to object", status=403)
    
    manager = ActivityLogManager(object_instance)
    
    return render(
        request,
        "views/generic/detail/activity.html",
        context={
            "object_id": object_id,
            "content_type_id": content_type_id,
            "queryset": manager.get_for_object(),
        }
    )
