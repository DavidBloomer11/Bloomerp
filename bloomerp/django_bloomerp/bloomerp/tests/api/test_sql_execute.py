from django.contrib.auth.models import Permission

from bloomerp.tests.base import BaseBloomerpModelTestCase


class SqlExecuteApiTests(BaseBloomerpModelTestCase):
    def extendedSetup(self):
        self.url = "/api/sql/execute/"
        self.db_table = self.CustomerModel._meta.db_table
        self.permission = Permission.objects.get(codename="execute_sql_query")

    def test_execute_sql_api_returns_query_results(self):
        """
        Use case: A permitted user posts a read-only SQL query to the SQL API.
        Expected result: The API returns paginated query results as JSON.
        """
        # 1. Authenticate a superuser with SQL execution access.
        self.client.force_login(self.admin_user)

        # 2. Execute a safe read-only query through the API.
        response = self.client.post(
            self.url,
            {
                "query": f"SELECT first_name FROM {self.db_table} ORDER BY first_name",
                "page_size": 3,
            },
            content_type="application/json",
        )

        # 3. Verify the response shape and pagination metadata.
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["columns"], ["first_name"])
        self.assertEqual(payload["page_rows_count"], 3)
        self.assertEqual(payload["row_count"], 10)
        self.assertEqual(payload["page"], 1)
        self.assertEqual(payload["page_size"], 3)
        self.assertEqual(payload["rows"][0], {"first_name": "Alice"})

    def test_execute_sql_api_requires_permission(self):
        """
        Use case: An authenticated user without SQL execution access posts a query.
        Expected result: The API denies the request before executing SQL.
        """
        # 1. Authenticate without granting the SQL execution permission.
        self.client.force_login(self.normal_user)

        # 2. Try to execute a safe query.
        response = self.client.post(
            self.url,
            {"query": f"SELECT first_name FROM {self.db_table}"},
            content_type="application/json",
        )

        # 3. Verify the permission gate is enforced.
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"error": "Permission denied"})

    def test_execute_sql_api_rejects_unsafe_query(self):
        """
        Use case: A permitted user posts a write SQL statement.
        Expected result: The API rejects unsafe SQL with a validation error.
        """
        # 1. Grant SQL execution access and authenticate the user.
        self.normal_user.user_permissions.add(self.permission)
        self.client.force_login(self.normal_user)

        # 2. Try to execute an unsafe query.
        response = self.client.post(
            self.url,
            {"query": f"DELETE FROM {self.db_table}"},
            content_type="application/json",
        )

        # 3. Verify the safety check blocks the query.
        self.assertEqual(response.status_code, 400)
        self.assertIn("Only safe read-only SELECT/WITH queries are allowed", response.json()["error"])

    def test_execute_sql_api_rejects_get(self):
        """
        Use case: A user calls the SQL execution API with GET.
        Expected result: The API only allows POST requests.
        """
        # 1. Authenticate as an allowed user.
        self.normal_user.user_permissions.add(self.permission)
        self.client.force_login(self.normal_user)

        # 2. Request the endpoint with GET.
        response = self.client.get(self.url)

        # 3. Verify the method is not allowed.
        self.assertEqual(response.status_code, 405)
