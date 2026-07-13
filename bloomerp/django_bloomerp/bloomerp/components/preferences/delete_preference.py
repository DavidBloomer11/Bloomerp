from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import render
from bloomerp.router import router
from bloomerp.utils.requests import render_page_refresh, render_page_refresh_with_message

@router.register(
    path="components/preferences/delete_preference/<str:model>/<str:preference_id>/",
    url_name="components_delete_preference"
)
@login_required
def delete_preference(request: HttpRequest, model:str, preference_id: str) -> HttpResponse:
    """Deletes a preference object

    Args:
        request (HttpRequest): _description_

    Returns:
        HttpResponse: _description_
    """
    # REQs
    # - Only post requests should be allowed
    # - Should check if the user can manage the preference object
    # - Should delete the preference object afterwards
    # - Should 
    
    return render_page_refresh_with_message(
        request,
        message=f"Preference {preference_id} deleted successfully",
        type="success"
    )
