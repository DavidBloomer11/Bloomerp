from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from bloomerp.router import router
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.utils.requests import render_page_refresh

@router.register(
    path="components/select_preference/<str:model>/",
    name="components_select_preference",
)
def select_preference(request: HttpRequest, model: str) -> HttpResponse:
    """Component that allows you to select a preference for preference models

    Args:
        request (HttpRequest): the request
        model (str): the model

    Returns:
        HttpResponse: the component
    """
    manager = PreferenceManager(request.user)
    preference_model = manager.resolve_model(model)
    if preference_model is None:
        return HttpResponse("Unknown preference model.", status=404)

    if request.method == "POST":
        action = request.POST.get("action")
        scope = preference_model.normalize_scope(request.POST.dict())
        if action == "select":
            preference = manager.get_available(preference_model, scope).filter(
                pk=request.POST.get("preference_id", "")
            ).first()
            if preference is None:
                return HttpResponse("Preference not found.", status=404)
            manager.select(preference)
            return render_page_refresh()

        return HttpResponse("Invalid action", status=400)

    if request.method != "GET":
        return HttpResponse("Method not allowed", status=405)

    scope = preference_model.normalize_scope(request.GET.dict())
    preferences = manager.get_available(preference_model, scope)

    return render(
        request,
        "components/select_preference.html",
        {
            "preferences": preferences,
            "model": model,
            "scope": scope,
            "model_verbose_name": preference_model._meta.verbose_name,
            
        },
    )
