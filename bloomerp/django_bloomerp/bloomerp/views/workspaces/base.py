

from abc import abstractmethod
from typing import Optional

from django.db.models import Q
from django.urls import reverse

from bloomerp.modules.definition import module_registry
from bloomerp.models.workspaces.workspace import Workspace
from bloomerp.services.sectioned_layout_services import dump_layout_json
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.utils.models import get_create_view_url
from bloomerp.views.base import BaseBloomerpView
from django.contrib.contenttypes.models import ContentType

class BaseWorkspaceView(BaseBloomerpView):
    template_name = 'views/workspaces/bloomerp_workspace_view.html'
    
    @abstractmethod
    def get_module_id(self) -> Optional[str]:
        pass

    @abstractmethod
    def get_workspace(self) -> Optional[Workspace]:
        pass

    def get_visible_workspaces(self):
        return PreferenceManager(self.request.user).get_available(
            Workspace,
            {"module_id": self.get_module_id()},
        )

    def get_fallback_workspace(self) -> Optional[Workspace]:
        return self.get_visible_workspaces().first()

    def get_workspace_badges(self, workspace: Workspace) -> list[dict[str, str]]:
        module = module_registry.get_all().get(workspace.module_id) if workspace.module_id else None
        lineage = module_registry.get_lineage(workspace.module_id) if module else []

        badges: list[dict[str, str]] = []
        if lineage:
            badges.append({"label": lineage[0].name, "tone": "module"})
        else:
            badges.append({"label": "General", "tone": "general"})

        for nested_module in lineage[1:]:
            badges.append({"label": nested_module.name, "tone": "nested"})

        if workspace.user_id != self.request.user.id:
            badges.append({"label": "Shared", "tone": "shared"})

        return badges

    def build_workspace_item(self, workspace: Workspace) -> dict:
        workspace = workspace.effective_preference
        return {
            "workspace": workspace,
        }

    def get_create_url(self) -> str:
        url = reverse(get_create_view_url(Workspace, "relative"))
        params = []

        module_id = self.get_module_id()

        if module_id:
            params.append(f"module_id={module_id}")

        if params:
            return f"{url}?{'&'.join(params)}"
        return url

    def get_workspace_template_context(self) -> dict:
        workspace = self.get_workspace()
        if workspace:
            workspace = workspace.effective_preference
        visible_workspaces = [self.build_workspace_item(item) for item in self.get_visible_workspaces()]
        
        context = {
            "workspace": workspace,
            "available_workspaces": visible_workspaces,
            "create_url": self.get_create_url(),
            "my_workspaces_url": reverse("my_workspaces"),
            "module_id": self.get_module_id(),
            "workspace_is_selected": bool(
                workspace
                and Workspace.objects.filter(
                    user=self.request.user,
                    module_id=workspace.module_id,
                    selected=True,
                )
                .filter(Q(pk=workspace.pk) | Q(source_object_id=workspace.pk))
                .exists()
            ),
            "workspace_content_type_id" : ContentType.objects.get_for_model(Workspace),
            "extra_attrs" : {"data-workspace-id": workspace.id if workspace else None},
            "preference_args" : {"module_id": self.get_module_id()}
        }

        if workspace:
            context["workspace_layout_json"] = dump_layout_json(workspace.layout_obj)

        return context
        
