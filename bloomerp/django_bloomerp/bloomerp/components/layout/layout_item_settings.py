from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from bloomerp.router import router
from bloomerp.models import models
from django.contrib.contenttypes.models import ContentType

from bloomerp.utils.models import get_model_and_content_type_or_404

def get_item_and_content_type(request: HttpRequest, content_type_id: str, object_id: str) -> tuple[models.Model, ContentType]:
    """Renders the item settings form for a layout object.

    Args:
        request (HttpRequest): the request object containing the layout item data.
        content_type_id (str): the ID of the content type for the layout item.

    Returns:
        HttpResponse: The rendered item settings form.
    """
    model, content_type = get_model_and_content_type_or_404(content_type_id)
    
    obj = get_object_or_404(model, pk=object_id)
    
    return obj, content_type



@router.register(
    path="components/layout/item_settings/<str:content_type_id>/<str:object_id>/",
    url_name="components_item_settings"
)
@login_required
def item_settings(request: HttpRequest, content_type_id: str, object_id: str) -> HttpResponse:
    """Renders the item settings form for a layout object.

    Args:
        request (HttpRequest): the request object containing the layout item data.
        content_type_id (str): the ID of the content type for the layout item.

    Returns:
        HttpResponse: The rendered item settings form.
    """
    obj, content_type = get_item_and_content_type(request, content_type_id, object_id)
    
    return HttpResponse(
        "Layout"
    )
    
    
