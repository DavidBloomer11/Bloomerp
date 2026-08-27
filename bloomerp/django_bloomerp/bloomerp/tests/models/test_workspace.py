from datetime import timedelta
from django.db import IntegrityError, transaction
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from bloomerp.models.definition import LayoutItem, LayoutRow, WorkspaceLayout
from bloomerp.models.project_management.initiative import Initiative, InitiativeStatus
from bloomerp.models.project_management.todo import Todo, TodoPriority, TodoStatus
from bloomerp.models.users.base_preference import BasePreference
from bloomerp.models.workspaces.tile import Tile
from bloomerp.models.workspaces.workspace import Workspace
from bloomerp.modules.definition import BloomerpModule, ModuleRegistry
from bloomerp.modules.todos_and_initiatives import TodosAndInitiatives
from bloomerp.services.preference_services import PreferenceManager
from bloomerp.services.workspace_services import (
    create_or_update_default_tiles,
    render_tile_to_string,
    resolve_tile_type_from_config,
    select_workspace,
)
from bloomerp.tests.base import BaseBloomerpTestCaseWithModels
from bloomerp.workspaces.text_tile.model import TextTileConfig
from bloomerp.workspaces.tiles import TileType


class WorkspaceModelTestCase(BaseBloomerpTestCaseWithModels):
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

    def test_default_tile_sync_creates_and_updates_by_native_id(self):
        class PlanningModule(BloomerpModule):
            id = "planning"
            name = "Planning"
            tiles = [
                TextTileConfig(
                    id="planning:notes",
                    name="Planning notes",
                    markdown="Initial",
                )
            ]

        registry = ModuleRegistry()
        registry.register(PlanningModule.to_config())

        first_result = create_or_update_default_tiles(registry)
        tile = first_result["planning:notes"]

        self.assertTrue(tile.auto_generated)
        self.assertEqual(tile.type, TileType.TEXT_TILE.name)
        self.assertEqual(tile.schema["id"], "planning:notes")
        self.assertEqual(
            Tile.get_tiles_by_native_ids(["planning:notes"]),
            {"planning:notes": tile},
        )

        registry.get("planning").tiles[0].name = "Updated planning notes"
        registry.get("planning").tiles[0].markdown = "Updated"
        second_result = create_or_update_default_tiles(registry)
        updated_tile = second_result["planning:notes"]

        self.assertEqual(updated_tile.pk, tile.pk)
        self.assertEqual(updated_tile.name, "Updated planning notes")
        self.assertEqual(updated_tile.schema["markdown"], "Updated")
        self.assertEqual(
            Tile.get_default_tiles().filter(schema__id="planning:notes").count(),
            1,
        )

    def test_create_default_for_user_materializes_all_module_workspaces(self):
        class PlanningModule(BloomerpModule):
            id = "planning"
            name = "Planning"
            tiles = [
                TextTileConfig(
                    id="planning:notes",
                    name="Planning notes",
                    markdown="Notes",
                )
            ]
            workspaces = [
                WorkspaceLayout(
                    name="My planning",
                    rows=[
                        LayoutRow(
                            columns=2,
                            items=[LayoutItem(id="planning:notes", colspan=2)],
                        )
                    ],
                ),
                WorkspaceLayout(
                    name="Planning overview",
                    is_default=False,
                    rows=[],
                ),
            ]

        registry = ModuleRegistry()
        registry.register(PlanningModule.to_config())

        with patch(
            "bloomerp.models.workspaces.workspace.module_registry",
            registry,
        ):
            selected = Workspace.create_default_for_user(
                self.admin_user,
                module_id="planning",
            )

        workspaces = list(
            Workspace.objects.filter(
                user=self.admin_user,
                module_id="planning",
            ).order_by("name")
        )
        generated_tile = Tile.get_tile_by_native_id("planning:notes")

        self.assertEqual(len(workspaces), 2)
        self.assertEqual(selected.name, "My planning")
        self.assertTrue(selected.selected)
        self.assertFalse(
            Workspace.objects.get(name="Planning overview").selected,
        )
        self.assertEqual(
            selected.layout_obj.rows[0].items[0].id,
            str(generated_tile.pk),
        )
        self.assertEqual(
            registry.get("planning").workspaces[0].rows[0].items[0].id,
            "planning:notes",
        )

    def test_real_todos_dashboard_materializes_all_declared_tiles(self):
        registry = ModuleRegistry()
        registry.register(TodosAndInitiatives.to_config())
        registry._module_models["todos_and_initiatives"] = {
            Todo._meta.label_lower: Todo,
            Initiative._meta.label_lower: Initiative,
        }
        registry.validate_workspace_tile_references()

        with patch(
            "bloomerp.models.workspaces.workspace.module_registry",
            registry,
        ):
            workspace = Workspace.create_default_for_user(
                self.admin_user,
                module_id="todos_and_initiatives",
            )

        generated_tiles = Tile.get_default_tiles()
        generated_by_native_id = {
            tile.schema["id"]: tile
            for tile in generated_tiles
        }
        materialized_ids = [
            str(item.id)
            for row in workspace.layout_obj.rows
            for item in row.items
        ]

        self.assertEqual(workspace.name, "Todos & Initiatives overview")
        self.assertTrue(workspace.selected)
        self.assertEqual(len(workspace.layout_obj.rows), 4)
        self.assertEqual(len(generated_by_native_id), 10)
        self.assertEqual(len(materialized_ids), 10)
        todo_links = {
            link["name"]: link["url"]
            for link in generated_by_native_id["todos:quick_links"].schema["links"]
        }
        self.assertEqual(todo_links["View all todos"], reverse("todos_model"))
        self.assertEqual(todo_links["Create a todo"], reverse("todos_add"))
        self.assertEqual(
            [
                link["url"]
                for link in generated_by_native_id["initiatives:quick_links"].schema["links"]
            ],
            [reverse("initiatives_model"), reverse("initiatives_add")],
        )
        self.assertEqual(
            set(materialized_ids),
            {str(tile.pk) for tile in generated_by_native_id.values()},
        )

        completed_todo = Todo.objects.create(
            title="Ship dashboard",
            status=TodoStatus.COMPLETED,
            priority=TodoPriority.HIGH,
            assigned_to=self.admin_user,
        )
        Todo.objects.filter(pk=completed_todo.pk).update(
            datetime_created=timezone.now() - timedelta(days=2),
        )
        Todo.objects.create(
            title="Review backlog",
            status=TodoStatus.BACKLOG,
            priority=TodoPriority.URGENT,
            assigned_to=self.admin_user,
        )
        Initiative.objects.create(
            name="Dashboard rollout",
            status=InitiativeStatus.IN_PROGRESS,
            owner=self.admin_user,
        )

        request = RequestFactory().get("/")
        request.user = self.admin_user
        for native_id, tile in generated_by_native_id.items():
            rendered = render_tile_to_string(tile, request)
            self.assertTrue(rendered.strip(), native_id)
            if native_id in {
                "todos:status_distribution",
                "initiatives:status_distribution",
                "todos:priority_distribution",
                "todos:completion_trend",
            }:
                self.assertIn("min-w-0", rendered, native_id)
                self.assertIn("max-w-full", rendered, native_id)

    def test_resolve_tile_type_from_config_uses_registered_config_model(self):
        self.assertEqual(
            resolve_tile_type_from_config(TextTileConfig(id="notes")),
            TileType.TEXT_TILE.name,
        )

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
