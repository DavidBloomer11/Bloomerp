from django.test import Client, TestCase
from django.urls import reverse

from bloomerp.models import User
from bloomerp.models.users.user import DetailSidebarViewPreference


class DetailSidebarPreferenceComponentTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="detail-sidebar-user",
            password="testpass123",
        )
        self.url = reverse("components_detail_sidebar_preference")

    def test_user_defaults_to_activity_as_the_first_sidebar_panel(self):
        """
        Use case: A user has not selected a detail sidebar panel.
        Expected result: Activity is stored as the default preference.
        """
        # 1. Read the newly created user's sidebar preference.
        preference = self.user.detail_sidebar_view_preference

        # 2. Confirm the existing Activity-first behavior is preserved.
        self.assertEqual(preference, DetailSidebarViewPreference.ACTIVITY)

    def test_user_can_persist_comments_as_the_first_sidebar_panel(self):
        """
        Use case: A user selects Comments in a detail view sidebar.
        Expected result: The user's preference is saved for future detail views.
        """
        # 1. Authenticate as the user selecting the panel.
        self.client.force_login(self.user)

        # 2. Persist the Comments selection.
        response = self.client.post(self.url, {"view": "comments"})

        # 3. Confirm the response and stored preference.
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok", "view": "comments"})
        self.user.refresh_from_db()
        self.assertEqual(
            self.user.detail_sidebar_view_preference,
            DetailSidebarViewPreference.COMMENTS,
        )

    def test_user_can_switch_the_first_sidebar_panel_back_to_activity(self):
        """
        Use case: A user selects Activity after previously selecting Comments.
        Expected result: Activity becomes the persisted sidebar preference.
        """
        # 1. Give the user an existing Comments preference and authenticate them.
        self.user.detail_sidebar_view_preference = DetailSidebarViewPreference.COMMENTS
        self.user.save(update_fields=["detail_sidebar_view_preference"])
        self.client.force_login(self.user)

        # 2. Persist the Activity selection.
        response = self.client.post(
            self.url,
            {"view": DetailSidebarViewPreference.ACTIVITY},
        )

        # 3. Confirm the latest selection replaces the previous preference.
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(
            self.user.detail_sidebar_view_preference,
            DetailSidebarViewPreference.ACTIVITY,
        )

    def test_invalid_sidebar_panel_is_rejected(self):
        """
        Use case: A client submits an unsupported detail sidebar panel.
        Expected result: The preference remains at the Activity default.
        """
        # 1. Authenticate as the user.
        self.client.force_login(self.user)

        # 2. Submit an unsupported panel value.
        response = self.client.post(self.url, {"view": "unsupported"})

        # 3. Confirm validation prevents a preference change.
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(
            self.user.detail_sidebar_view_preference,
            DetailSidebarViewPreference.ACTIVITY,
        )

    def test_sidebar_preference_requires_authentication(self):
        """
        Use case: An anonymous client tries to change a sidebar preference.
        Expected result: Authentication is required and no user preference changes.
        """
        # 1. Submit a preference without authenticating.
        response = self.client.post(self.url, {"view": "comments"})

        # 2. Confirm the request is redirected to authentication.
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(
            self.user.detail_sidebar_view_preference,
            DetailSidebarViewPreference.ACTIVITY,
        )

    def test_sidebar_preference_requires_csrf_token(self):
        """
        Use case: An authenticated client submits a preference without a CSRF token.
        Expected result: Django rejects the update.
        """
        # 1. Authenticate with a client that enforces CSRF validation.
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)

        # 2. Submit the preference without a CSRF token.
        response = csrf_client.post(self.url, {"view": "comments"})

        # 3. Confirm the request is forbidden and the preference is unchanged.
        self.assertEqual(response.status_code, 403)
        self.user.refresh_from_db()
        self.assertEqual(
            self.user.detail_sidebar_view_preference,
            DetailSidebarViewPreference.ACTIVITY,
        )

    def test_sidebar_preference_requires_post(self):
        """
        Use case: A client tries to read the preference endpoint directly.
        Expected result: The endpoint only accepts preference updates.
        """
        # 1. Authenticate as the user.
        self.client.force_login(self.user)

        # 2. Use an unsupported request method.
        response = self.client.get(self.url)

        # 3. Confirm the endpoint rejects the request.
        self.assertEqual(response.status_code, 405)
