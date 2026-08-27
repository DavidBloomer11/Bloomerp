from django.urls import resolve, reverse

from bloomerp.models.workspaces import SqlQuery
from bloomerp.tests.base import BaseBloomerpTestCaseWithModels


class SqlQueryApiTests(BaseBloomerpTestCaseWithModels):
    def test_generated_endpoint_scopes_queries_to_the_authenticated_creator(self):
        url = reverse("sql_queries-list")

        self.assertEqual(url, "/api/sql_queries/")
        self.assertEqual(resolve(url).url_name, "sql_queries-list")

        self.client.force_login(self.normal_user)
        response = self.client.post(
            url,
            data={"name": "Revenue", "query": "SELECT 1"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(set(response.json()), {"id", "name", "query"})

        saved_query = SqlQuery.objects.get(name="Revenue")
        self.assertEqual(saved_query.created_by, self.normal_user)
        self.assertEqual(saved_query.updated_by, self.normal_user)
        SqlQuery.objects.create(
            name="Other user's query",
            query="SELECT 2",
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [{
            "id": str(saved_query.pk),
            "name": "Revenue",
            "query": "SELECT 1",
        }])

    def test_generated_endpoint_updates_an_owned_query(self):
        saved_query = SqlQuery.objects.create(
            name="Before",
            query="SELECT 1",
            created_by=self.normal_user,
            updated_by=self.admin_user,
        )
        self.client.force_login(self.normal_user)

        response = self.client.patch(
            reverse("sql_queries-detail", kwargs={"pk": saved_query.pk}),
            data={"name": "After", "query": "SELECT 2"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        saved_query.refresh_from_db()
        self.assertEqual(saved_query.name, "After")
        self.assertEqual(saved_query.query, "SELECT 2")
        self.assertEqual(saved_query.updated_by, self.normal_user)
