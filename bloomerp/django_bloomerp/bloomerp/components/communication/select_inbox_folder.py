from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404

from bloomerp.communication.utils.permissions import accessible_inbox_folders
from bloomerp.models.communication.inbox.inbox import Inbox
from bloomerp.models.communication.inbox.user_inbox_preference import (
    UserInboxPreference,
)
from bloomerp.router import router
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.utils.requests import render_page_refresh


@router.register(
    path="components/communication/select_inbox_folder/<str:folder_id>/",
    url_name="components_select_inbox_folder",
)
@login_required
def select_inbox_folder(
    request: HttpRequest,
    folder_id: str,
) -> HttpResponse:
    """Select an accessible inbox folder for the requesting user."""
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    inbox = PreferenceManager(request.user).get_or_create_selected(
        Inbox,
        force_create=False,
    )
    if inbox is None:
        return HttpResponse("No inbox is selected.", status=400)

    folder = get_object_or_404(
        accessible_inbox_folders(request.user).filter(inbox=inbox),
        pk=folder_id,
    )
    preference = UserInboxPreference.get_for_user(request.user)
    preference.selected_inbox_folder = folder
    preference.save(update_fields=["selected_inbox_folder"])
    return render_page_refresh()
