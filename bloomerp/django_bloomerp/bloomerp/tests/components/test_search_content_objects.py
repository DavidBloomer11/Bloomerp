import json

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse

from bloomerp.tests.base import BaseBloomerpModelTestCase


class SearchContentObjectsTests(BaseBloomerpModelTestCase):
    auto_create_customers = False

    def test_search_returns_matching_object_with_generic_relation_keys(self):
        """
        Use case: A permitted user searches the generic content-object widget.
        Expected result: Matching objects include both content type and object identifiers.
        """
        # 1. Create matching and non-matching records and authenticate as a superuser.
        matching = self.create_customer(first_name="Generic", last_name="Target", age=30)
        self.create_customer(first_name="Different", last_name="Customer", age=31)
        self.client.force_login(self.admin_user)

        # 2. Search across accessible models.
        response = self.client.get(
            reverse("components_search_content_objects"),
            {"q": "Generic Target"},
        )

        # 3. Verify only the match is returned with its generic relation keys.
        self.assertEqual(response.status_code, 200)
        objects = json.loads(response.content)["objects"]
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0]["object_id"], str(matching.pk))
        self.assertEqual(
            objects[0]["content_type_id"],
            str(ContentType.objects.get_for_model(self.CustomerModel).pk),
        )
        self.assertEqual(objects[0]["label"], "Generic Target")

    def test_search_excludes_objects_without_view_access(self):
        """
        Use case: A user without view permission searches for an existing object.
        Expected result: The permission-bounded endpoint returns no objects.
        """
        # 1. Create a searchable record and authenticate a user without a policy.
        self.create_customer(first_name="Private", last_name="Target", age=30)
        self.client.force_login(self.normal_user)

        # 2. Search for the record.
        response = self.client.get(
            reverse("components_search_content_objects"),
            {"q": "Private Target"},
        )

        # 3. Verify the inaccessible object is absent.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["objects"], [])

    def test_search_requires_authentication(self):
        """
        Use case: An anonymous request calls the content-object search endpoint.
        Expected result: The request is redirected to authentication.
        """
        # 1. Call the endpoint without logging in.
        response = self.client.get(
            reverse("components_search_content_objects"),
            {"q": "anything"},
        )

        # 2. Verify authentication is required.
        self.assertEqual(response.status_code, 302)
