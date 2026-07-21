from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.urls import reverse

from bloomerp.forms.model_form import bloomerp_modelform_factory
from bloomerp.router import router
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.utils.requests import render_blank_form, render_message, render_page_refresh


@router.register(
    path="components/preferences/share_preference/<str:model_name>/<str:preference_id>/",
    url_name="components_share_preference",
)
@login_required
def share_preference(request: HttpRequest, model_name: str, preference_id: str) -> HttpResponse:
    """Render and save the owner-only sharing form for a preference."""
    manager = PreferenceManager(request.user)
    preference_model = manager.resolve_model(model_name)
    if preference_model is None:
        return HttpResponse("Unknown preference model.", status=404)

    preference = preference_model.objects.filter(pk=preference_id).first()
    if preference is None:
        return HttpResponse("Preference not found.", status=404)
    if not manager.can_manage(preference):
        return HttpResponse("You cannot share this preference.", status=403)

    fields = ["shared_with_users", "shared_with_groups"]
    if manager.can_set_initial_default(request.user, preference_model):
        fields.append("initial_default")
    form_class = bloomerp_modelform_factory(preference_model, fields=fields)

    if request.method == "POST":
        form = form_class(request.POST, instance=preference)
        if form.is_valid():
            form.save()
            return render_page_refresh()
    elif request.method == "GET":
        form = form_class(instance=preference)
    else:
        return HttpResponse("Method not allowed", status=405)

    return render_blank_form(
        request,
        form,
        reverse(
            "components_share_preference",
            kwargs={"model_name": model_name, "preference_id": preference_id},
        ),
        submit_label="Share",
        text=f"Share this {preference_model._meta.verbose_name} with individual users or groups. Shared users can select it, while only you can edit it.",
    )
