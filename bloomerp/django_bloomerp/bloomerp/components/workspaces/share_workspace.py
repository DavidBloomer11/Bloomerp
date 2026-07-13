from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _

from bloomerp.models.workspaces.workspace import Workspace
from bloomerp.router import router
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.widgets.foreign_field_widget import ForeignFieldWidget


class WorkspaceShareForm(forms.Form):
    shared_with_users = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.none(),
        required=False,
        label=_("Shared with"),
        help_text=_("Search and add users who should be able to open this workspace."),
        widget=ForeignFieldWidget(
            attrs={
                "model": get_user_model(),
                "is_m2m": True,
                "class": "input h-11 w-full",
            }
        ),
    )
    shared_with_groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),
        required=False,
        label=_("Shared with groups"),
        help_text=_(
            "Search and add groups whose members should be able to open this workspace."
        ),
        widget=ForeignFieldWidget(
            attrs={
                "model": Group,
                "is_m2m": True,
                "class": "input h-11 w-full",
            }
        ),
    )
    initial_default = forms.BooleanField(
        required=False,
        label=_("Initial default"),
        help_text=_(
            "Use this workspace initially for users who receive it through sharing."
        ),
    )

    def __init__(self, *args, workspace: Workspace, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.workspace = workspace
        self.fields["shared_with_users"].queryset = (
            get_user_model()
            .objects.exclude(pk=workspace.user_id)
            .order_by("username")
        )
        self.fields["shared_with_groups"].queryset = Group.objects.order_by("name")
        if not PreferenceManager.can_set_initial_default(user, Workspace):
            self.fields.pop("initial_default")


def _get_owned_workspace(request: HttpRequest, workspace_id: int) -> Workspace | HttpResponse:
    workspace = get_object_or_404(Workspace, pk=workspace_id)
    if workspace.user_id != request.user.pk:
        return HttpResponse("Permission denied", status=403)
    return workspace


@router.register(
    path="components/workspaces/share/<int:workspace_id>/",
    name="components_workspaces_share_workspace",
)
def share_workspace(request: HttpRequest, workspace_id: int) -> HttpResponse:
    """Component to share workspaces

    Args:
        request (HttpRequest): 
        workspace_id (int): the workspace id

    Returns:
        HttpResponse: 
    """
    workspace = _get_owned_workspace(request, workspace_id)
    if isinstance(workspace, HttpResponse):
        return workspace

    initial = {
        "shared_with_users": workspace.shared_with_users.all(),
        "shared_with_groups": workspace.shared_with_groups.all(),
        "initial_default": workspace.initial_default,
    }
    form = WorkspaceShareForm(workspace=workspace, user=request.user, initial=initial)
    success = False

    if request.method == "POST":
        form = WorkspaceShareForm(request.POST, workspace=workspace, user=request.user)
        if form.is_valid():
            workspace.shared_with_users.set(form.cleaned_data["shared_with_users"])
            workspace.shared_with_groups.set(form.cleaned_data["shared_with_groups"])
            if "initial_default" in form.cleaned_data:
                workspace.initial_default = form.cleaned_data["initial_default"]
                workspace.save(update_fields=["initial_default"])
            form = WorkspaceShareForm(
                workspace=workspace,
                user=request.user,
                initial={
                    "shared_with_users": workspace.shared_with_users.all(),
                    "shared_with_groups": workspace.shared_with_groups.all(),
                    "initial_default": workspace.initial_default,
                },
            )
            success = True

    return render(
        request,
        "components/workspaces/share_workspace.html",
        {
            "workspace": workspace,
            "form": form,
            "success": success,
        },
    )
