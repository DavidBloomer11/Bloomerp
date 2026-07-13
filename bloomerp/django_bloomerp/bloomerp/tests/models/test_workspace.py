from django.db import IntegrityError, transaction

from bloomerp.models.users.base_preference import BasePreference
from bloomerp.models.workspaces.tile import Tile
from bloomerp.models.workspaces.workspace import Workspace
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.services.workspace_services import select_workspace
from bloomerp.tests.base import BaseBloomerpModelTestCase
from bloomerp.workspaces.tiles import TileType


class WorkspaceModelTestCase(BaseBloomerpModelTestCase):
    auto_create_customers = False

    def create_tile(self, name: str) -> Tile:
        return Tile.objects.create(
            name=name,
            description="",
            type=TileType.TEXT_TILE.name,
            schema={},
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )

    def test_workspace_uses_module_scoped_base_preference(self):
        self.assertTrue(issubclass(Workspace, BasePreference))
        self.assertEqual(Workspace.preference_scope_fields, ("module_id",))

    def test_get_or_create_for_user_creates_selected_workspace(self):
        workspace = Workspace.create_default_for_user(
            self.admin_user,
            module_id="sales",
        )

        self.assertEqual(workspace.user, self.admin_user)
        self.assertEqual(workspace.module_id, "sales")
        self.assertTrue(workspace.selected)

    def test_shared_initial_workspace_creates_live_selected_reference(self):
        shared_workspace = Workspace.objects.create(
            user=self.normal_user,
            module_id="sales",
            name="Shared sales workspace",
            initial_default=True,
            layout={
                "rows": [
                    {
                        "title": "Shared",
                        "columns": 4,
                        "items": [],
                    }
                ]
            },
        )
        shared_workspace.shared_with_users.add(self.admin_user)

        result = PreferenceManager(self.admin_user).get_or_create_selected(
            Workspace,
            {"module_id": "sales"},
        )

        reference = Workspace.objects.get(
            user=self.admin_user,
            source_object=shared_workspace,
        )
        self.assertEqual(result, shared_workspace)
        self.assertTrue(reference.selected)
        self.assertEqual(reference.module_id, "sales")

    def test_workspace_selection_is_independent_per_module(self):
        sales = Workspace.objects.create(
            user=self.admin_user,
            module_id="sales",
            name="Sales",
            selected=True,
        )
        finance = Workspace.objects.create(
            user=self.admin_user,
            module_id="finance",
            name="Finance",
            selected=True,
        )

        sales.refresh_from_db()
        finance.refresh_from_db()
        self.assertTrue(sales.selected)
        self.assertTrue(finance.selected)

    def test_none_scope_selects_general_workspace_only(self):
        module_workspace = Workspace.objects.create(
            user=self.admin_user,
            module_id="sales",
            name="Sales",
            selected=True,
        )

        general_workspace = PreferenceManager(self.admin_user).get_or_create_selected(
            Workspace,
            {"module_id": "None"},
        )

        module_workspace.refresh_from_db()
        self.assertIsNone(general_workspace.module_id)
        self.assertTrue(general_workspace.selected)
        self.assertTrue(module_workspace.selected)

    def test_database_rejects_multiple_selected_general_workspaces(self):
        Workspace.objects.create(
            user=self.admin_user,
            module_id=None,
            name="Primary general workspace",
            selected=True,
        )
        secondary = Workspace.objects.create(
            user=self.admin_user,
            module_id=None,
            name="Secondary general workspace",
            selected=False,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Workspace.objects.filter(pk=secondary.pk).update(selected=True)

    def test_selecting_shared_workspace_creates_selected_live_reference(self):
        current = Workspace.objects.create(
            user=self.admin_user,
            module_id="sales",
            name="Current",
            selected=True,
        )
        shared = Workspace.objects.create(
            user=self.normal_user,
            module_id="sales",
            name="Shared",
        )
        shared.shared_with_users.add(self.admin_user)

        effective = select_workspace(shared, self.admin_user)

        current.refresh_from_db()
        reference = Workspace.objects.get(
            user=self.admin_user,
            source_object=shared,
        )
        self.assertEqual(effective, shared)
        self.assertFalse(current.selected)
        self.assertTrue(reference.selected)

    def test_get_tiles_returns_tiles_in_layout_order(self):
        first_tile = self.create_tile("First")
        second_tile = self.create_tile("Second")
        third_tile = self.create_tile("Third")
        workspace = Workspace.objects.create(
            user=self.admin_user,
            name="Workspace",
            layout={
                "rows": [
                    {
                        "columns": 4,
                        "items": [
                            {"id": str(second_tile.pk), "colspan": 1},
                            {"id": str(first_tile.pk), "colspan": 1},
                        ],
                    },
                    {
                        "columns": 4,
                        "items": [
                            {"id": str(third_tile.pk), "colspan": 1},
                        ],
                    },
                ],
            },
        )

        self.assertEqual(
            list(workspace.get_tiles().values_list("pk", flat=True)),
            [second_tile.pk, first_tile.pk, third_tile.pk],
        )

    def test_get_tiles_ignores_stale_and_invalid_layout_ids(self):
        tile = self.create_tile("Only valid tile")
        workspace = Workspace.objects.create(
            user=self.admin_user,
            name="Workspace",
            layout={
                "rows": [
                    {
                        "columns": 4,
                        "items": [
                            {"id": "not-a-tile", "colspan": 1},
                            {"id": str(tile.pk), "colspan": 1},
                            {"id": "999999", "colspan": 1},
                        ],
                    },
                ],
            },
        )

        self.assertEqual(list(workspace.get_tiles()), [tile])
