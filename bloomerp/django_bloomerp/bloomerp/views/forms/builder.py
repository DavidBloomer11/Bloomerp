from bloomerp.models.forms.form import Form
from bloomerp.permissions.manager import UserPolicyManager, create_permission_str
from bloomerp.router import router
from bloomerp.views.generic.detail.base import BaseBloomerpDetailView
from bloomerp.views.mixins.application_field_layout_form_mixin import (
    ApplicationFieldLayoutFormMixin,
)
from bloomerp.views.mixins.layout_mixin import LayoutBinding


@router.register(
    path="builder",
    name="Form Builder",
    url_name="form_builder",
    route_type="detail",
    models=[Form],
)
class BuilderView(ApplicationFieldLayoutFormMixin, BaseBloomerpDetailView):
    model = Form
    template_name = "views/forms/builder.html"
    layout_mode = "create"
    init_edit = True

    def get_layout_binding(self) -> LayoutBinding:
        form = getattr(self, "object", None) or self.get_object()
        self.object = form
        return LayoutBinding(
            owner=form,
            target_content_type=form.content_type,
            layout_mode=self.layout_mode,
        )

    def get_change_permission_str(self):
        return create_permission_str(self.layout_model, "add")

    def get_view_permission_str(self):
        return self.get_change_permission_str()

    def has_permission(self) -> bool:
        if self.request.user.is_superuser:
            return True
        manager = UserPolicyManager(self.request.user)
        form = self.get_object()
        self.object = form
        return manager.has_access_to_object(
            form,
            create_permission_str(form, "change"),
        )

    def get_can_change(self) -> bool:
        return True
