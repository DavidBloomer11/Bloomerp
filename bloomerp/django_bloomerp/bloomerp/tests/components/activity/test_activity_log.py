from bloomerp.models.project_management.todo import Todo
from bloomerp.tests.base_component_test import BaseBloomerpComponentTest, ExpectedResult, RequestSetup


class ActivityLogComponentTestCase(BaseBloomerpComponentTest):
    view_name = "components_activity_log"
    
    def get_request_setups(self):
        content_type = self.get_content_type_for_model(Todo)
        obj = Todo.objects.create(
            name="Todo"
        )
        get_args = {
            "content_type_id" : content_type.id,
            "object_id" : obj.id
        }
        
        return [
            RequestSetup(
                name="Authorized User",
                method="GET",
                user=self.admin_user,
                get_args=get_args,
                expected=ExpectedResult(
                    status_code=200,
                )
                
            ),
            RequestSetup(
                name="Unauthorized user",
                method="GET",
                user=self.normal_user,
                get_args=get_args,
                expected=ExpectedResult(
                    status_code=403
                )
            )
        ]
    