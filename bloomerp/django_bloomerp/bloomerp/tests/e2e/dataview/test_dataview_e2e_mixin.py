from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from bloomerp.models.project_management.todo import Todo
from bloomerp.tests.e2e.base import BaseE2ETestCase
from bloomerp.utils.models import get_list_view_url


class TestDataviewE2EMixin(BaseE2ETestCase):
    
    def goto_todo_page(self):
        self.goto(
            reverse(
                get_list_view_url(Todo)
            )
        )
        
        with self.expect_response_for(
            reverse(
                "components_dataview",
                kwargs={
                    "content_type_id" : ContentType.objects.get_for_model(Todo).pk
                }
            )
        ):
            pass