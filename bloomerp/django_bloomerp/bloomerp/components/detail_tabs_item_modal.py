from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from bloomerp.forms.detail_tabs import DetailTabItemForm
from bloomerp.models.users.user_detail_view_tabs_preference import (
    UserDetailViewTabsPreference,
)
from bloomerp.router import router
from bloomerp.services.detail_tab_services import get_detail_route_options
from bloomerp.services.preference_services import PreferenceManager


@router.register(
    path="components/detail-tabs/item-modal/",
    name="components_detail_tabs_item_modal",
)
@login_required
def detail_tabs_item_modal(request: HttpRequest) -> HttpResponse:
    """Render and validate the shared folder/URL create and edit modal."""
    if request.method not in {"GET", "POST"}:
        return HttpResponse("Method not allowed", status=405)

    values = request.GET if request.method == "GET" else request.POST
    try:
        content_type_id = int(values.get("content_type_id", ""))
    except ValueError:
        return HttpResponse("Invalid content_type_id", status=400)
    content_type = get_object_or_404(ContentType, id=content_type_id)
    manager = PreferenceManager(request.user)
    preference = manager.get_or_create_selected(
        UserDetailViewTabsPreference,
        {"content_type_id": content_type.pk},
    )
    if preference is None or not manager.can_manage(preference):
        return HttpResponse("You cannot edit this tabs preference.", status=403)

    item_type = values.get("item_type", "folder")
    if item_type not in {"folder", "url"}:
        return HttpResponse("Invalid item type", status=400)
    mode = values.get("mode", "create")
    if mode not in {"create", "edit"}:
        return HttpResponse("Invalid mode", status=400)

    item_id = values.get("item_id") or None
    item = None
    if mode == "edit":
        try:
            item = preference.items.filter(pk=item_id).first()
        except (ValidationError, ValueError):
            return HttpResponse("Invalid item_id", status=400)
        if item is None:
            return HttpResponse("Tab item not found", status=404)
        expected_type = "folder" if item.is_folder else "url"
        if item_type != expected_type:
            return HttpResponse("Item type cannot be changed", status=400)

    initial = {
        "item_type": item_type,
        "item_id": item_id,
        "name": item.name if item is not None else values.get("name", ""),
        "url": item.url if item is not None else values.get("url", ""),
    }
    form = DetailTabItemForm(request.POST or None, initial=initial)
    success = request.method == "POST" and form.is_valid()

    return render(
        request,
        "components/detail_tabs/item_modal_form.html",
        {
            "form": form,
            "mode": mode,
            "item_type": item_type,
            "content_type_id": content_type.pk,
            "route_options": get_detail_route_options(content_type.model_class()),
            "pk_placeholder": "{{pk}}",
            "success": success,
            "result": form.cleaned_data if success else None,
        },
    )
