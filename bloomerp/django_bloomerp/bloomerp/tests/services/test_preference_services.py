from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction

from bloomerp.models.users.user_list_view_preference import UserListViewPreference
from bloomerp.models.workspaces.sidebar import Sidebar
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.tests.base import BaseBloomerpModelTestCase


class PreferenceManagerTestCase(BaseBloomerpModelTestCase):
    auto_create_customers = False

    def extendedSetup(self):
        self.content_type = ContentType.objects.get_for_model(self.CustomerModel)
        self.scope = {"content_type_id": self.content_type.pk}
        self.manager = PreferenceManager(self.admin_user)

    def test_get_or_create_selected_returns_existing_selection(self):
        selected = UserListViewPreference.objects.create(
            user=self.admin_user,
            content_type=self.content_type,
            name="Existing",
            selected=True,
        )

        result = self.manager.get_or_create_selected(
            UserListViewPreference,
            self.scope,
        )

        self.assertEqual(result, selected)
        self.assertEqual(
            UserListViewPreference.objects.filter(user=self.admin_user).count(),
            1,
        )

    def test_get_or_create_selected_selects_existing_unselected_preference(self):
        existing = UserListViewPreference.objects.create(
            user=self.admin_user,
            content_type=self.content_type,
            name="Existing",
        )
        UserListViewPreference.objects.filter(pk=existing.pk).update(selected=False)

        result = self.manager.get_or_create_selected(
            UserListViewPreference,
            self.scope,
        )

        existing.refresh_from_db()
        self.assertEqual(result, existing)
        self.assertTrue(existing.selected)

    def test_get_or_create_selected_references_shared_initial_default(self):
        shared_default = UserListViewPreference.objects.create(
            user=self.normal_user,
            content_type=self.content_type,
            name="Company default",
            initial_default=True,
        )
        shared_default.shared_with_users.add(self.admin_user)

        result = self.manager.get_or_create_selected(
            UserListViewPreference,
            self.scope,
        )

        reference = UserListViewPreference.objects.get(
            user=self.admin_user,
            source_object=shared_default,
        )
        self.assertEqual(result, shared_default)
        self.assertTrue(reference.selected)

    def test_get_or_create_selected_ignores_non_initial_shared_preference(self):
        shared = UserListViewPreference.objects.create(
            user=self.normal_user,
            content_type=self.content_type,
            name="Optional shared view",
        )
        shared.shared_with_users.add(self.admin_user)

        result = self.manager.get_or_create_selected(
            UserListViewPreference,
            self.scope,
        )

        self.assertEqual(result.user, self.admin_user)
        self.assertTrue(result.selected)
        self.assertFalse(
            UserListViewPreference.objects.filter(
                user=self.admin_user,
                source_object=shared,
            ).exists()
        )

    def test_saving_selected_preference_deselects_siblings_in_same_scope(self):
        first = UserListViewPreference.objects.create(
            user=self.admin_user,
            content_type=self.content_type,
            name="First",
            selected=True,
        )
        second = UserListViewPreference.objects.create(
            user=self.admin_user,
            content_type=self.content_type,
            name="Second",
            selected=False,
        )

        second.selected = True
        second.save(update_fields=["selected"])

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.selected)
        self.assertTrue(second.selected)

    def test_saving_selected_preference_preserves_other_scopes(self):
        other_content_type = ContentType.objects.get_for_model(
            UserListViewPreference
        )
        first_scope = UserListViewPreference.objects.create(
            user=self.admin_user,
            content_type=self.content_type,
            name="Customer view",
            selected=True,
        )
        second_scope = UserListViewPreference.objects.create(
            user=self.admin_user,
            content_type=other_content_type,
            name="Preference view",
            selected=True,
        )

        first_scope.refresh_from_db()
        second_scope.refresh_from_db()
        self.assertTrue(first_scope.selected)
        self.assertTrue(second_scope.selected)

    def test_database_rejects_multiple_selected_unscoped_preferences(self):
        Sidebar.objects.create(
            user=self.admin_user,
            name="Primary",
            selected=True,
        )
        secondary = Sidebar.objects.create(
            user=self.admin_user,
            name="Secondary",
            selected=False,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Sidebar.objects.filter(pk=secondary.pk).update(selected=True)
