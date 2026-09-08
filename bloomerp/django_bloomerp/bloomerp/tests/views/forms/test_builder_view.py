from bloomerp.models.forms.form import Form
from bloomerp.models.project_management.todo import Todo
from bloomerp.tests.base import (
    BloomerpDetailViewTestCase,
    ExpectedResult,
    RequestSetup,
    ModelRequestSetup,
)


class TestBuilderView(BloomerpDetailViewTestCase):
    view_name = 'form_builder'
    model = Form

    def create_test_object(self):
        return Form.objects.create(
            name="Default form",
            content_type=self.get_content_type_for_model(Todo)
        )
    
    def get_request_setups(self) -> list[RequestSetup]:
        return [
            RequestSetup(
                name="Accessible to admin user",
                method="GET",
                user=self.admin_user,
                expected=ExpectedResult(
                    200,
                    response_validators=[
                        self.contains_text("Search"),
                        self.contains_text("Initial Data"),
                        self.contains_text("Edit"),
                        self.contains_text("Add items"),
                    ]
                )
            ),
            RequestSetup(
                name="Inaccessible to normal user",
                user=self.normal_user,
                expected=ExpectedResult(
                    403
                )
            )
        ]
