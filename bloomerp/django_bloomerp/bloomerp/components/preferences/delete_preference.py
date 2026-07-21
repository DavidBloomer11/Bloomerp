from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.html import format_html

from bloomerp.router import router
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.utils.requests import render_blank_form, render_page_refresh_with_message


@router.register(
    path="components/preferences/delete_preference/<str:model>/<str:preference_id>/",
    url_name="components_delete_preference",
)
@login_required
def delete_preference(
    request: HttpRequest,
    model: str,
    preference_id: str,
) -> HttpResponse:
    """Delete an owner-managed preference and refresh the current page."""
    manager = PreferenceManager(request.user)
    preference_model = manager.resolve_model(model)
    if preference_model is None:
        return HttpResponse("Unknown preference model.", status=404)

    preference = get_object_or_404(preference_model, pk=preference_id)
    if not manager.can_manage(preference):
        return HttpResponse("You cannot delete this preference.", status=403)

    if request.method == "GET":
        return render_blank_form(
            request,
            form=None,
            url=reverse(
                "components_delete_preference",
                kwargs={"model": model, "preference_id": preference_id},
            ),
            submit_label="Delete",
            text=format_html(
                'Are you sure you want to delete <strong>"{}"</strong>? '
                "This action cannot be undone.",
                preference.name,
            ),
        )

    if request.method != "POST":
        return HttpResponse("Method not allowed", status=405)

    preference_name = preference.name
    preference.delete()

    return render_page_refresh_with_message(
        request,
        message=f'Preference "{preference_name}" deleted successfully.',
        type="success",
    )
