from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from bloomerp.models.project_management.todo import Todo
from bloomerp.tests.base import BaseBloomerpModelTestCase


class GenericForeignKeyCrudTests(BaseBloomerpModelTestCase):
    auto_create_customers = False

    def test_create_view_saves_content_object_widget_values(self):
        """
        Use case: A user selects an object in the Todo create view's single content-object widget.
        Expected result: The created Todo stores the selected content type and object id.
        """
        # 1. Create a target object and authenticate as a superuser.
        customer = self.create_customer(first_name="Create", last_name="Target", age=30)
        customer_content_type = ContentType.objects.get_for_model(self.CustomerModel)
        self.client.force_login(self.admin_user)

        # 2. Submit the two hidden values produced by the content-object widget.
        response = self.client.post(
            reverse("todos_add"),
            {
                "title": "Linked todo",
                "priority": "medium",
                "effort": "4",
                "status": "backlog",
                "content_type": str(customer_content_type.pk),
                "object_id": str(customer.pk),
            },
        )

        # 3. Verify the generic relation resolves to the selected object.
        self.assertEqual(response.status_code, 302)
        todo = Todo.objects.get(title="Linked todo")
        self.assertEqual(todo.content_type, customer_content_type)
        self.assertEqual(todo.object_id, str(customer.pk))
        self.assertEqual(todo.content_object, customer)

    def test_overview_updates_content_object_widget_values(self):
        """
        Use case: A user changes the selected content object on a Todo overview.
        Expected result: Both generic relation backing fields are updated together.
        """
        # 1. Create a Todo and two possible target objects.
        original = self.create_customer(first_name="Original", last_name="Target", age=30)
        replacement = self.create_customer(first_name="Replacement", last_name="Target", age=31)
        todo = Todo.objects.create(title="Update linked todo", content_object=original)
        replacement_content_type = ContentType.objects.get_for_model(self.CustomerModel)
        self.client.force_login(self.admin_user)

        # 2. Submit the replacement values from the overview widget.
        response = self.client.post(
            reverse("todos_detail_overview", kwargs={"pk": todo.pk}),
            {
                "title": todo.title,
                "priority": todo.priority,
                "effort": str(todo.effort),
                "status": todo.status,
                "content_type": str(replacement_content_type.pk),
                "object_id": str(replacement.pk),
            },
        )

        # 3. Verify the Todo now resolves to the replacement object.
        self.assertEqual(response.status_code, 302)
        todo.refresh_from_db()
        self.assertEqual(todo.content_object, replacement)
