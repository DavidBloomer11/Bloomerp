from django.contrib.auth import SESSION_KEY, get_user_model
from django.urls import resolve, reverse

from bloomerp.tests.base import BaseBloomerpModelTestCase
from bloomerp.utils.models import get_detail_view_url


User = get_user_model()


class TestUserPasswordResetViews(BaseBloomerpModelTestCase):
    auto_create_customers = False

    def setUp(self):
        super().setUp()
        self.normal_user.set_password("current-password-123")
        self.normal_user.save(update_fields=["password"])

    def reset_url(self, user=None):
        user = user or self.normal_user
        return reverse(
            "users_detail_reset_password",
            kwargs={"pk": user.pk},
        )

    def admin_reset_url(self, user=None):
        user = user or self.normal_user
        return reverse(
            "users_detail_admin_reset_password_for_user",
            kwargs={"pk": user.pk},
        )

    def test_reset_routes_are_bound_to_the_active_user_model(self):
        for url in (self.reset_url(), self.admin_reset_url()):
            match = resolve(url)
            self.assertIs(match.func.view_initkwargs["model"], User)

    def test_user_can_open_their_own_password_reset_form(self):
        self.client.force_login(self.normal_user)

        response = self.client.get(self.reset_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="old_password"')

    def test_user_can_reset_their_password_without_losing_the_session(self):
        self.client.force_login(self.normal_user)

        response = self.client.post(
            self.reset_url(),
            {
                "old_password": "current-password-123",
                "new_password1": "new-password-456",
                "new_password2": "new-password-456",
            },
        )

        self.assertRedirects(
            response,
            reverse("users_my_profile_overview"),
            fetch_redirect_response=False,
        )
        self.normal_user.refresh_from_db()
        self.assertTrue(self.normal_user.check_password("new-password-456"))
        self.assertEqual(
            self.client.session[SESSION_KEY],
            str(self.normal_user.pk),
        )

    def test_non_superuser_cannot_reset_another_users_password(self):
        other_user = User.objects.create_user(
            username="other-user",
            password="other-password-123",
        )
        self.client.force_login(self.normal_user)

        response = self.client.get(self.reset_url(other_user))

        self.assertEqual(response.status_code, 403)

    def test_admin_reset_view_loads_the_target_user(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.admin_reset_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="password1"')

    def test_admin_can_reset_another_users_password(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            self.admin_reset_url(),
            {
                "password1": "admin-set-password-789",
                "password2": "admin-set-password-789",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                get_detail_view_url(User),
                kwargs={"pk": self.normal_user.pk},
            ),
            fetch_redirect_response=False,
        )
        self.normal_user.refresh_from_db()
        self.assertTrue(
            self.normal_user.check_password("admin-set-password-789")
        )

    def test_non_superuser_cannot_use_the_admin_reset_view(self):
        self.client.force_login(self.normal_user)

        response = self.client.get(self.admin_reset_url())

        self.assertEqual(response.status_code, 403)
