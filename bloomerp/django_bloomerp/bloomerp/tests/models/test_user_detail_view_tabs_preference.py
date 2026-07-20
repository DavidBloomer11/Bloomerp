import json
import uuid

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from bloomerp.models import Todo, User
from bloomerp.models.users.user_detail_view_tabs_preference import (
    UserDetailViewTabItem,
    UserDetailViewTabsPreference,
)
from bloomerp.services.detail_tab_services import (
    build_rendered_tab_items,
    get_detail_route_options,
    sync_tab_items,
)
from bloomerp.services.preference_services import PreferenceManager


class UserDetailViewTabsPreferenceTests(TestCase):
    def setUp(self) -> None:
        self.owner = User.objects.create_user(
            username="tabs-owner",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            username="tabs-other",
            password="testpass123",
        )
        self.content_type = ContentType.objects.get_for_model(Todo)

    def test_default_preference_uses_one_argument_detail_route_templates(self):
        """
        Use case: A user opens a model detail page without a tabs preference.
        Expected result: The default preference contains every one-PK detail route using {{pk}} URLs.
        """
        # 1. Create the default preference through the required BasePreference factory.
        preference = UserDetailViewTabsPreference.create_default_for_user(
            self.owner,
            content_type_id=self.content_type.pk,
        )

        # 2. Compare the relational items with the route catalog.
        options = get_detail_route_options(Todo)
        items = list(preference.items.order_by("position"))
        self.assertTrue(options)
        self.assertEqual([item.name for item in items], [option["name"] for option in options])
        self.assertEqual([item.url for item in items], [option["url"] for option in options])
        self.assertTrue(all("{{pk}}" in (item.url or "") for item in items))

    def test_preference_api_is_owner_scoped_and_items_are_not_exposed(self):
        """
        Use case: The preference selector renames an owned layout through the SDK.
        Expected result: Only owner-scoped preference fields are exposed, while item mutation stays component-only.
        """
        # 1. Read the explicit model API configurations.
        preference_api = UserDetailViewTabsPreference.bloomerp_config.api_settings
        item_api = UserDetailViewTabItem.bloomerp_config.api_settings

        # 2. Confirm the preference API is generated for authenticated owners.
        self.assertTrue(preference_api.enable_auto_generation)
        self.assertEqual(preference_api.user_access[0].through_field, "user")
        self.assertEqual(
            preference_api.user_access[0].field_actions["name"],
            ["view", "change"],
        )

        # 3. Confirm relational items remain behind the permission-aware components.
        self.assertFalse(item_api.enable_auto_generation)

    def test_folder_can_only_contain_tabs_from_the_same_preference(self):
        """
        Use case: Invalid folder trees are submitted programmatically.
        Expected result: Cross-preference children and nested folders are rejected.
        """
        # 1. Create two preferences and a valid folder.
        first = UserDetailViewTabsPreference.objects.create(
            user=self.owner,
            content_type=self.content_type,
        )
        second = UserDetailViewTabsPreference.objects.create(
            user=self.other_user,
            content_type=self.content_type,
        )
        folder = UserDetailViewTabItem.objects.create(
            preference=first,
            name="Related",
            url=None,
        )

        # 2. Validate that another preference cannot place a tab in that folder.
        cross_preference_tab = UserDetailViewTabItem(
            preference=second,
            parent=folder,
            name="Invalid",
            url="/todos/{{pk}}/",
        )
        with self.assertRaises(ValidationError):
            cross_preference_tab.full_clean()

        # 3. Validate that folders cannot be nested.
        nested_folder = UserDetailViewTabItem(
            preference=first,
            parent=folder,
            name="Nested",
            url=None,
        )
        with self.assertRaises(ValidationError):
            nested_folder.full_clean()

    def test_sync_tab_items_persists_order_folders_and_deletions(self):
        """
        Use case: The browser saves a drag-and-drop snapshot.
        Expected result: Positions, membership, edits, additions, and deletions are persisted atomically.
        """
        # 1. Create a preference containing an item that will be removed.
        preference = UserDetailViewTabsPreference.objects.create(
            user=self.owner,
            content_type=self.content_type,
        )
        removed = UserDetailViewTabItem.objects.create(
            preference=preference,
            name="Removed",
            url="/removed/",
        )
        folder_id = uuid.uuid4()
        tab_id = uuid.uuid4()

        # 2. Save a new folder tree snapshot.
        sync_tab_items(
            preference,
            [
                {
                    "id": str(folder_id),
                    "name": "Relationships",
                    "url": None,
                    "parent_id": None,
                    "position": 0,
                },
                {
                    "id": str(tab_id),
                    "name": "Tasks",
                    "url": "/todos/{{pk}}/",
                    "parent_id": str(folder_id),
                    "position": 0,
                },
            ],
        )

        # 3. Confirm the old item is gone and the hierarchy is relational.
        self.assertFalse(UserDetailViewTabItem.objects.filter(pk=removed.pk).exists())
        folder = preference.items.get(pk=folder_id)
        tab = preference.items.get(pk=tab_id)
        self.assertTrue(folder.is_folder)
        self.assertEqual(tab.parent, folder)
        self.assertEqual(tab.position, 0)

    def test_new_named_preference_copies_the_relational_tree(self):
        """
        Use case: A user creates a named tabs preference from the selector.
        Expected result: The new independent preference receives a deep copy of the selected tree.
        """
        # 1. Create and select a source preference with a folder and child tab.
        source = UserDetailViewTabsPreference.objects.create(
            user=self.owner,
            content_type=self.content_type,
            selected=True,
        )
        folder = UserDetailViewTabItem.objects.create(
            preference=source,
            name="Folder",
            url=None,
        )
        UserDetailViewTabItem.objects.create(
            preference=source,
            parent=folder,
            name="Overview",
            url="/todos/{{pk}}/",
        )

        # 2. Create a named preference through the generic preference manager.
        copied = PreferenceManager(self.owner).create(
            UserDetailViewTabsPreference,
            name="Alternative",
            scope={"content_type_id": self.content_type.pk},
        )

        # 3. Confirm both rows were copied with new identities and preserved membership.
        copied_items = list(copied.items.order_by("parent_id", "position"))
        self.assertEqual(len(copied_items), 2)
        copied_folder = next(item for item in copied_items if item.is_folder)
        copied_tab = next(item for item in copied_items if not item.is_folder)
        self.assertNotEqual(copied_folder.pk, folder.pk)
        self.assertEqual(copied_tab.parent, copied_folder)

    def test_rendered_items_resolve_only_the_primary_key_placeholder(self):
        """
        Use case: A stored URL is rendered for a concrete object.
        Expected result: {{pk}} resolves to that object's key and determines active navigation state.
        """
        # 1. Create a stored URL template.
        preference = UserDetailViewTabsPreference.objects.create(
            user=self.owner,
            content_type=self.content_type,
        )
        UserDetailViewTabItem.objects.create(
            preference=preference,
            name="Overview",
            url="/todos/{{pk}}/overview/",
        )

        # 2. Render the preference for object 42.
        rendered = build_rendered_tab_items(
            preference,
            object_pk=42,
            request_path="/todos/42/overview/",
        )

        # 3. Confirm URL resolution and active state.
        self.assertEqual(rendered[0]["href"], "/todos/42/overview/")
        self.assertTrue(rendered[0]["is_active"])


class DetailTabsComponentTests(TestCase):
    def setUp(self) -> None:
        self.owner = User.objects.create_user(
            username="component-tabs-owner",
            password="testpass123",
        )
        self.viewer = User.objects.create_user(
            username="component-tabs-viewer",
            password="testpass123",
        )
        self.content_type = ContentType.objects.get_for_model(Todo)
        self.preference = UserDetailViewTabsPreference.objects.create(
            user=self.owner,
            content_type=self.content_type,
            selected=True,
        )

    def test_owner_can_save_relational_tab_snapshot(self):
        """
        Use case: The owner reorders and creates items in the browser.
        Expected result: The component accepts and persists the complete snapshot.
        """
        # 1. Authenticate as the preference owner.
        self.client.force_login(self.owner)
        tab_id = uuid.uuid4()

        # 2. Submit a valid snapshot.
        response = self.client.post(
            reverse("components_detail_tabs_preference"),
            {
                "content_type_id": self.content_type.pk,
                "items": json.dumps(
                    [
                        {
                            "id": str(tab_id),
                            "name": "Overview",
                            "url": "/todos/{{pk}}/",
                            "parent_id": None,
                            "position": 0,
                        }
                    ]
                ),
            },
        )

        # 3. Confirm persistence.
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.preference.items.filter(pk=tab_id).exists())

    def test_generated_api_allows_only_the_owner_to_rename_preference(self):
        """
        Use case: The generic selector renames a tabs preference through the generated SDK.
        Expected result: The owner can change the name and another authenticated user cannot.
        """
        # 1. Rename through the same endpoint used by the generated SDK.
        endpoint = f"/api/user_detail_view_tabs_preferences/{self.preference.pk}/"
        self.client.force_login(self.owner)
        owner_response = self.client.patch(
            endpoint,
            data=json.dumps({"name": "Owner layout"}),
            content_type="application/json",
        )

        # 2. Confirm the owner-scoped update succeeded.
        self.assertEqual(owner_response.status_code, 200)
        self.preference.refresh_from_db()
        self.assertEqual(self.preference.name, "Owner layout")

        # 3. Confirm another user cannot rename the owner's preference.
        self.client.force_login(self.viewer)
        viewer_response = self.client.patch(
            endpoint,
            data=json.dumps({"name": "Hijacked"}),
            content_type="application/json",
        )
        self.assertIn(viewer_response.status_code, {403, 404})
        self.preference.refresh_from_db()
        self.assertEqual(self.preference.name, "Owner layout")

    def test_shared_preference_is_read_only_for_recipient(self):
        """
        Use case: A recipient selects a live shared tabs preference.
        Expected result: Mutation is denied because only the source owner may edit it.
        """
        # 1. Share and select the owner's preference for another user.
        self.preference.shared_with_users.add(self.viewer)
        PreferenceManager(self.viewer).select(self.preference)
        self.client.force_login(self.viewer)

        # 2. Attempt to overwrite the shared layout.
        response = self.client.post(
            reverse("components_detail_tabs_preference"),
            {
                "content_type_id": self.content_type.pk,
                "items": "[]",
            },
        )

        # 3. Confirm the permission-aware component rejects the write.
        self.assertEqual(response.status_code, 403)

    def test_url_modal_exposes_one_pk_route_datalist(self):
        """
        Use case: The owner creates a URL tab.
        Expected result: The modal exposes detail route templates and their names through a datalist.
        """
        # 1. Authenticate as the owner and request the create-URL form.
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("components_detail_tabs_item_modal"),
            {
                "content_type_id": self.content_type.pk,
                "item_type": "url",
                "mode": "create",
            },
        )

        # 2. Confirm the route datalist and supported placeholder are rendered.
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<datalist id="detail-tab-route-options">', html=False)
        self.assertContains(response, "{{pk}}", html=False)
        self.assertContains(response, 'data-name="', html=False)
