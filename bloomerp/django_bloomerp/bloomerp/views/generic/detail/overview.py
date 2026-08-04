from __future__ import annotations

from django.shortcuts import redirect

from bloomerp.forms.model_form import BloomerpModelForm
from bloomerp.permissions.manager import create_permission_str
from bloomerp.router import router
from bloomerp.utils.models import get_detail_view_url
from bloomerp.views.generic.detail.base import BaseBloomerpDetailView
from bloomerp.views.mixins.layout_model_form_mixin import LayoutModelFormMixin


@router.register(
    path="/",
    name="Details",
    url_name="overview",
    description="Overview of object from {model} model",
    route_type="detail",
    models="__all__",
)
class BloomerpDetailOverviewView(LayoutModelFormMixin, BaseBloomerpDetailView):
    layout_mode = "detail"

    def has_permission(self):
        self.object = self.get_object()
        return self.permission_manager.has_access_to_object(
            self.object,
            self.get_view_permission_str()
        )
    
    def get_view_permission_str(self):
        return create_permission_str(self.model, "view")

    def get_change_permission_str(self):
        return create_permission_str(self.model, "change")

    def get_success_response(self, form: BloomerpModelForm):
        self.add_message(f"Object '{self.object}' updated", "success")
        if getattr(self.request, "htmx", False):
            return self.render_to_response(self.get_context_data())
        return redirect(get_detail_view_url(self.model), pk=self.object.pk)
