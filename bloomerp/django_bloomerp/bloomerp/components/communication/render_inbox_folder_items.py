from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, render
from bloomerp.models.communication.inbox.inbox_folder import InboxFolder
from bloomerp.router import router

@router.register(
    path="components/communication/render_inbox_folder/<str:folder_id>/",
    url_name="components_render_inbox_folder_items"
)
def render_inbox_folder(request:HttpRequest, folder_id: str):
    """
    Renders the inbox items for a given user and inbox type.

    Args:
        request (HttpRequest): The HTTP request object containing GET parameters.
    """
    inbox_folder = get_object_or_404(InboxFolder, id=folder_id)
    error_message = None

    try:
        items = inbox_folder.query_items(request.GET)
    except ValidationError as exc:
        items = []
        error_message = "; ".join(exc.messages)
    
    return render(
        request,
        "components/communication/render_inbox_folder_items.html",
        {
            "items": items,
            "inbox_folder": inbox_folder,
            "error_message": error_message,
        }
    )


