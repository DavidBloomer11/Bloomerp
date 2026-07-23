from django import forms
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django_htmx.http import HttpResponseClientRedirect

from bloomerp.communication.inbox_folder_definition import InboxFolderType
from bloomerp.models.communication.inbox.inbox import Inbox
from bloomerp.models.communication.inbox.inbox_folder import InboxFolder
from bloomerp.models.communication.inbox.user_inbox_preference import UserInboxPreference
from bloomerp.router import router
from bloomerp.utils.requests import parse_bool_parameter, render_blank_form


class CreateInboxForm(forms.ModelForm):
    class Meta:
        model = Inbox
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "input",
                    "placeholder": "Inbox name",
                }
            )
        }


def _default_inbox_name(request: HttpRequest) -> str:
    full_name = request.user.get_full_name()
    if full_name:
        return f"{full_name}'s Inbox"
    return "My Inbox"


def _create_default_folders(inbox: Inbox) -> list[InboxFolder]:
    folders: list[InboxFolder] = []
    for folder_type in InboxFolderType:
        if folder_type.value.is_default:
            folders.append(
                InboxFolder.objects.create(
                    inbox=inbox,
                    type=folder_type.value.key,
                )
            )
    return folders


def _render_create_inbox_form(
    request: HttpRequest,
    form: CreateInboxForm,
    status: int = 200,
) -> HttpResponse:
    response = render_blank_form(
        request,
        form=form,
        url=reverse("components_create_inbox"),
        submit_label="Create inbox",
    )
    response.status_code = status
    return response


@router.register(
    path="components/communication/create_inbox",
    url_name="components_create_inbox",
)
@login_required
def create_inbox(request: HttpRequest) -> HttpResponse:
    """Creates inbox component

    If the user has no inbox, it will also create a UserInboxPreference for the user.
    
    If post arg "create_default=true" is passed, it will create a default inbox for the user.
    
    Args:
        request (HttpRequest): The HTTP request object.
    """
    create_default = parse_bool_parameter(request.POST.get("create_default"))

    if request.method == "POST":
        post_data = request.POST.copy()
        if create_default and not post_data.get("name"):
            post_data["name"] = _default_inbox_name(request)

        form = CreateInboxForm(post_data)
        if form.is_valid():
            with transaction.atomic():
                inbox = form.save(commit=False)
                inbox.user = request.user
                inbox.selected = True
                inbox.save()

                default_folders = _create_default_folders(inbox) if create_default else []
                selected_folder = default_folders[0] if default_folders else None

                preference = UserInboxPreference.get_for_user(request.user)
                preference.selected_inbox_folder = selected_folder
                preference.save(update_fields=["selected_inbox_folder"])

            redirect_url = reverse("inbox")
            if request.htmx:
                return HttpResponseClientRedirect(redirect_url)
            return redirect(redirect_url)

        return _render_create_inbox_form(request, form, status=400)

    if request.method == "GET":
        form = CreateInboxForm(initial={"name": _default_inbox_name(request)})
        return _render_create_inbox_form(request, form)

    return HttpResponse(status=405)
