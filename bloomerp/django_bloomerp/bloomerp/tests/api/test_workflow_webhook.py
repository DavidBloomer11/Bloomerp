from django.test import TestCase
from django.urls import resolve, reverse


class TestWorkflowWebhookRoute(TestCase):
    def test_workflow_webhook_keeps_its_custom_url_name(self):
        url = reverse("api_workflow_webhook", kwargs={"pk": 1})

        self.assertEqual(url, "/api/workflows/1/webhook/")
        self.assertEqual(resolve(url).url_name, "api_workflow_webhook")

        response = self.client.post(url)

        self.assertEqual(response.status_code, 404)
