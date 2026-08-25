from django.views.generic import TemplateView
from django.urls import reverse
from bloomerp.models.files import File
from bloomerp.permissions.definition import BloomerpPermission
from bloomerp.permissions.manager import UserPolicyManager
from bloomerp.views.base import BaseBloomerpView
from bloomerp.router import router


@router.register(
    path="files",
    route_type="app",
    name="Files",
    url_name="app",
    description="List of all files across the application.",
)
class BloomerpFileListView(BaseBloomerpView, TemplateView):
    template_name = "views/generic/model/bloomerp_file_list.html"
    model = File
    module = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_string = self.request.GET.urlencode()
        context["file_browser_url"] = reverse("components_files")
        if query_string:
            context["file_browser_url"] = f"{context['file_browser_url']}?{query_string}"
        return context
    
    def has_permission(self):
        manager = UserPolicyManager(self.request.user)
        return manager.has_global_permission(
            model_or_content_type=File,
            permissions=BloomerpPermission.VIEW
        )
