from django.shortcuts import redirect
from django_htmx.http import HttpResponseClientRedirect

from bloomerp.router import router
from bloomerp.models.workspaces.workspace import Workspace
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.views.workspaces.base import BaseWorkspaceView
from django.views.generic import TemplateView


@router.register(
    path=f"/",
    name='{module}',
    description='The homepage for the {module} module.',
    route_type='module',
    modules="__all__"
)
class BloomerpModuleHomeView(BaseWorkspaceView, TemplateView):
    
    def get_visible_workspaces(self):
        module_id = self.get_module_id()
        return PreferenceManager(self.request.user).get_available(
            Workspace,
            {"module_id": module_id},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_workspace_template_context())
        return context

    def post(self, request, *args, **kwargs):
        if request.POST.get("action") == "create_default":
            Workspace.create_default_for_user(
                user=request.user,
                module_id=self.get_module_id() or None,
            )
            if request.htmx:
                return HttpResponseClientRedirect(request.path)
            return redirect(request.path)

        return self.get(request, *args, **kwargs)

    def get_module_id(self) -> str | None:
        return self.module.id if self.module else None

    def get_workspace(self) -> Workspace | None:
        module_id = self.get_module_id()
        return PreferenceManager(self.request.user).get_or_create_selected(
            Workspace,
            {"module_id": module_id},
            force_create=False
        )
