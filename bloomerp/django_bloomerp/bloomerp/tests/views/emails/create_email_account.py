from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from bloomerp.communication.utils.crypto import is_encrypted_email_secret
from bloomerp.communication.emails.email_providers import EmailProvider
from bloomerp.models.communication import EmailAccount


class TestCreateEmailAccountView(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_superuser(
            username="email-admin",
            email="email-admin@example.com",
            password="password",
        )
        self.client.force_login(self.user)
        self.url = reverse("email_accounts_add")

    def test_provider_step_renders_available_options(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Outlook")
        self.assertContains(response, "Google")
        self.assertContains(response, "IMAP / SMTP")
        self.assertContains(response, "Other")

    def test_imap_wizard_creates_email_account(self):
        response = self.client.post(self.url, {"provider": EmailProvider.IMAP.value.key})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            self.url,
            {
                "name": "Support",
                "email_address": "support@example.com",
                "username": "support@example.com",
                "password": "app-password",
                "imap_host": "imap.example.com",
                "imap_port": "993",
                "imap_security": EmailAccount.SecurityMode.SSL_TLS,
                "smtp_host": "smtp.example.com",
                "smtp_port": "587",
                "smtp_security": EmailAccount.SecurityMode.STARTTLS,
            },
        )

        self.assertEqual(response.status_code, 302)
        account = EmailAccount.objects.get(email_address="support@example.com")
        self.assertEqual(account.provider, EmailProvider.IMAP.value.key)
        self.assertEqual(account.status, EmailAccount.Status.DRAFT)
        self.assertEqual(account.created_by, self.user)
        self.assertEqual(account.imap_host, "imap.example.com")
        self.assertEqual(account.smtp_host, "smtp.example.com")
        self.assertNotEqual(account.password, "app-password")
        self.assertTrue(is_encrypted_email_secret(account.password))
        self.assertEqual(account.get_password_secret(), "app-password")

    def test_google_wizard_creates_email_account_with_oauth_settings(self):
        response = self.client.post(self.url, {"provider": EmailProvider.GOOGLE.value.key})
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            self.url,
            {
                "name": "Google Inbox",
                "email_address": "google@example.com",
                "oauth_client_id": "client-id",
                "oauth_client_secret": "client-secret",
                "oauth_scopes": "https://mail.google.com/",
            },
        )

        self.assertEqual(response.status_code, 302)
        account = EmailAccount.objects.get(email_address="google@example.com")
        self.assertEqual(account.provider, EmailProvider.GOOGLE.value.key)
        self.assertEqual(account.oauth_client_id, "client-id")
        self.assertNotEqual(account.oauth_client_secret, "client-secret")
        self.assertTrue(is_encrypted_email_secret(account.oauth_client_secret))
        self.assertEqual(account.get_oauth_client_secret(), "client-secret")

    def test_model_validation_uses_provider_required_fields(self):
        account = EmailAccount(
            provider=EmailProvider.GOOGLE.value.key,
            name="Google Inbox",
            email_address="google@example.com",
        )

        with self.assertRaisesMessage(ValidationError, "oauth_client_id"):
            account.full_clean()
