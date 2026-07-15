from django.urls import resolve

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from bloomerp.models import FieldPolicy, Policy, RowPolicy
from bloomerp.models.application_field import ApplicationField
from bloomerp.models.definition import BloomerpModelConfig
from bloomerp.services.permission_services import ensure_model_permissions
from bloomerp.tests.base import BaseBloomerpModelTestCase


class AssistantMutationApiTests(BaseBloomerpModelTestCase):
    def extendedSetup(self):
        self.url = "/api/mutations/"
        self.CustomerModel.bloomerp_config = BloomerpModelConfig()
        self.resource = self.CustomerModel._meta.verbose_name_plural.replace(" ", "_").lower()

    def test_create_update_and_delete_mutations(self):
        """
        UC: User want's to mutate objects via create, update, and delete
        Expected result: mutations work
        """
        self.client.force_login(self.admin_user)

        create_response = self.client.post(
            self.url,
            {
                "resource": self.resource,
                "operation": "create",
                "data": {
                    "first_name": "Grace",
                    "last_name": "Hopper",
                    "age": 85,
                },
            },
            content_type="application/json",
        )

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.json()["operation"], "create")
        object_id = create_response.json()["object"]["id"]

        update_response = self.client.post(
            self.url,
            {
                "resource": self.resource,
                "operation": "update",
                "object_id": object_id,
                "data": {"first_name": "Rear Admiral Grace"},
            },
            content_type="application/json",
        )

        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["object"]["first_name"], "Rear Admiral Grace")

        delete_response = self.client.post(
            self.url,
            {
                "resource": self.resource,
                "operation": "delete",
                "object_id": object_id,
            },
            content_type="application/json",
        )

        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.json()["object_id"], str(object_id))
        self.assertFalse(self.CustomerModel.objects.filter(pk=object_id).exists())

    def test_mutations_require_a_generated_api_resource(self):
        """
        UC: Users sometimes return a wrong resource
        Expected result: Wrong resource should return an error
        """
        self.client.force_login(self.admin_user)

        response = self.client.post(
            self.url,
            {
                "resource": "not-a-resource",
                "operation": "create",
                "data": {},
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"resource": "Unknown generated API resource."})

    def test_mutations_preserve_generated_model_write_permissions(self):
        """
        UC: Users need to have the correct perms
        Expected result: User blocked from mutating
        """
        self.client.force_login(self.normal_user)

        response = self.client.post(
            self.url,
            {
                "resource": self.resource,
                "operation": "create",
                "data": {
                    "first_name": "Unauthorized",
                    "last_name": "User",
                    "age": 1,
                },
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.CustomerModel.objects.filter(first_name="Unauthorized").exists())

    def test_catalog_lists_available_operations_and_writable_fields(self):
        """
        UC: Users want to know what operations and fields are available for a resource
        Expected result: Catalog lists available operations and writable fields
        """
        self.client.force_login(self.admin_user)

        response = self.client.get("/api/mutations/catalog/")

        self.assertEqual(response.status_code, 200)
        resource = next(
            item for item in response.json()["resources"] if item["resource"] == self.resource
        )
        self.assertEqual(
            resource["object_id"],
            {"field": "id", "type": "string", "format": "uuid"},
        )
        self.assertEqual(set(resource["operations"]), {"create", "update", "delete"})

        create_fields = {field["name"]: field for field in resource["operations"]["create"]["fields"]}
        update_fields = {field["name"]: field for field in resource["operations"]["update"]["fields"]}
        self.assertTrue(create_fields["first_name"]["required"])
        self.assertFalse(update_fields["first_name"]["required"])
        self.assertEqual(create_fields["age"]["type"], "integer")

    def test_catalog_uses_operation_specific_field_permissions(self):
        """
        UC: Users want to know what operations and fields are available for a resource
        Expected result: Catalog lists available operations and writable fields
        """
        content_type = ContentType.objects.get_for_model(self.CustomerModel)
        first_name_field = ApplicationField.get_by_field(self.CustomerModel, "first_name")
        field_policy = FieldPolicy.objects.create(
            content_type=content_type,
            name="Mutation catalog fields",
            rule={
                str(first_name_field.id): ["add_customer", "change_customer"],
            },
        )
        row_policy = RowPolicy.objects.create(
            content_type=content_type,
            name="Mutation catalog rows",
        )
        policy = Policy.objects.create(
            name="Mutation catalog policy",
            row_policy=row_policy,
            field_policy=field_policy,
        )
        policy.assign_user(self.normal_user)

        ensure_model_permissions(self.CustomerModel)
        self.normal_user.user_permissions.add(
            *Permission.objects.filter(
                content_type=content_type,
                codename__in=["add_customer", "change_customer"],
            )
        )
        self.client.force_login(self.normal_user)

        response = self.client.get("/api/mutations/catalog/")

        self.assertEqual(response.status_code, 200)
        resource = next(
            item for item in response.json()["resources"] if item["resource"] == self.resource
        )
        self.assertEqual(set(resource["operations"]), {"create", "update"})
        self.assertEqual(
            [field["name"] for field in resource["operations"]["create"]["fields"]],
            ["first_name"],
        )
        self.assertEqual(
            [field["name"] for field in resource["operations"]["update"]["fields"]],
            ["first_name"],
        )

    def test_catalog_hides_resources_without_write_permission(self):
        """
        UC: Users want to know what operations and fields are available for a resource
        Expected result: Catalog lists available operations and writable fields
        """
        self.client.force_login(self.normal_user)

        response = self.client.get("/api/mutations/catalog/")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            self.resource,
            [resource["resource"] for resource in response.json()["resources"]],
        )

    def test_route_is_registered_for_openapi_schema_and_redoc(self):
        """
        UC: Users want to see the OpenAPI schema and Redoc documentation
        Expected result: Route is registered for OpenAPI schema and Redoc
        """
        self.assertEqual(resolve(self.url).url_name, "api_assistant_mutations")
        self.assertEqual(resolve("/api/schema/ui/").func.view_class.url_name, "schema")

        response = self.client.get("/api/schema/?format=json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("/api/mutations/", response.json()["paths"])
        self.assertIn("/api/mutations/catalog/", response.json()["paths"])
