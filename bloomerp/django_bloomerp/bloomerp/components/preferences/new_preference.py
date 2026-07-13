from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse

from bloomerp.router import router
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.utils.requests import render_page_refresh


@router.register(
    path="components/preferences/new_preference/<str:model>/",
    url_name="components_new_preference",
)
@login_required
def new_preference(request: HttpRequest, model: str) -> HttpResponse:
    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    manager = PreferenceManager(request.user)
    preference_model = manager.resolve_model(model)
    if preference_model is None:
        return HttpResponse("Unknown preference model.", status=404)

    name = request.POST.get("name", "").strip()
    if not name:
        return HttpResponse("A preference name is required.", status=400)

    scope = preference_model.normalize_scope(request.POST.dict())
    manager.create(preference_model, name=name, scope=scope)
    return render_page_refresh()
