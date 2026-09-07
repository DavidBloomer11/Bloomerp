from bloomerp.models.project_management.todo import Todo
from bloomerp.tests.base import BaseBloomerpComponentTest, RequestSetup, ExpectedResult

class BulkActionsComponentTestCase(BaseBloomerpComponentTest):
    view_name = "components_bulk_actions"
    
    def get_request_setups(self):
        NUMBER_OF_OBJECTS = 10
        
        view_kwargs = {
            "content_type_id" : self.get_content_type_for_model(Todo)
        }
        
        object_ids = []
        for i in range(NUMBER_OF_OBJECTS):
            todo = Todo.objects.create(
                title=f"Todo {i}"
            )
            
            if i < 5:
                object_ids.append(
                    str(todo.id)
                )
        
        ids_in_response = [
            self.contains_text(id) for id in object_ids
        ]
        
        
        return [
            RequestSetup(
                name="Normal response",
                description="Will validate a response in general",
                method="GET",
                user=self.admin_user,
                view_kwargs=view_kwargs,
                query_params={},
                expected=ExpectedResult(
                    status_code=200,
                )
            ),
            RequestSetup(
                name="With selection",
                description="Selection will give you the selected amount",
                method="GET",
                user=self.admin_user,
                query_params={
                    "object_ids": object_ids,
                    "selection" : "selected"
                },
                expected=ExpectedResult(
                    status_code=200,
                    response_validators=[
                        *ids_in_response,
                        self.contains_text("No filters applied."),
                        self.contains_text(f"{len(object_ids)} Todo object(s)."),
                    ]
                )
            ),
            RequestSetup(
                name="With filter",
                description="Check if it works with filters",
                method="GET",
                
            )
        ]