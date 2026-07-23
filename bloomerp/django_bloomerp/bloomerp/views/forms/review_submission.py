from bloomerp.models.forms.form_submission import FormSubmission
from bloomerp.router import router
from bloomerp.services.form_services import FormManager
from bloomerp.views.generic.detail.base import BaseBloomerpDetailView
from bloomerp.views.mixins.application_field_layout_form_mixin import (
    ApplicationFieldLayoutFormMixin,
)
from bloomerp.views.mixins.layout_mixin import LayoutBinding


@router.register(
    path="review",
    route_type="detail",
    models=[FormSubmission],
    name="Review Submission",
    description="Review a form submission",
)
class ReviewFormSubmissionView(
    ApplicationFieldLayoutFormMixin,
    BaseBloomerpDetailView,
):
    apply_permissions = False

    def get_submission(self) -> FormSubmission:
        if getattr(self, "object", None) is None:
            self.object = self.get_object()
        return self.object

    def get_layout_binding(self) -> LayoutBinding:
        submission = self.get_submission()
        return LayoutBinding(
            owner=submission.form,
            target_content_type=submission.form.content_type,
        )

    def get_view_permission_str(self) -> str:
        return ""

    def get_change_permission_str(self) -> str:
        return ""

    def get_form(self):
        cached_form = getattr(self, "_layout_form", None)
        if cached_form is not None:
            return cached_form

        submission = self.get_submission()
        form_class = FormManager(submission.form).layout_form_cls()
        if form_class is None:
            return super().get_form()

        self._layout_form = form_class(
            initial={
                **submission.data,
                "files": list(submission.files.all()),
            },
        )
        return self.apply_layout_widget_config(self._layout_form)
