from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from django.test import RequestFactory

from bloomerp.models.workspaces.tile import Tile
from bloomerp.services.permission_services import UserPermissionManager
from bloomerp.services.workspace_services import render_tile_to_string
from bloomerp.tests.base import BaseBloomerpModelTestCase
from bloomerp.workspaces.links_tile.model import Link, LinkTileConfig
from bloomerp.workspaces.links_tile.render import LinksTileRenderer
from bloomerp.workspaces.text_tile.model import TextTileConfig
from bloomerp.workspaces.text_tile.render import render_html
from bloomerp.workspaces.tiles import TileType
from bloomerp.workspaces.utils import UserParameterResolver


class WorkspaceTileRenderingTests(BaseBloomerpModelTestCase):
    auto_create_customers = False

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def test_text_tile_renders_template_content(self):
        """
        Use case: A workspace text tile is rendered from its saved tile configuration.
        Expected result: The tile template renders content instead of surfacing a missing template path.
        """
        # 1. Create a text tile with visible markdown content.
        tile = Tile.objects.create(
            name="KPI tile",
            description="",
            type=TileType.TEXT_TILE.name,
            schema={"markdown": "Visible workspace tile"},
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        request = self.factory.get("/")
        request.user = self.admin_user

        # 2. Render the tile through the workspace rendering service.
        html = render_tile_to_string(tile, request)

        # 3. Verify the template content renders instead of the template file name.
        self.assertIn("Visible workspace tile", html)
        self.assertNotIn("cotton/workspaces/tiles/text.html", html)

    def test_text_tile_renders_sanitized_editor_html(self):
        html = render_html('<h2>Notes</h2><p>Visible content</p><script>alert("xss")</script>')

        self.assertIn("<h2", html)
        self.assertIn("Visible content", html)
        self.assertNotIn("<script", html)

    def test_text_tile_editor_has_valid_htmx_update_expression(self):
        html = render_to_string(
            "components/workspaces/tile_builders/text_tile_builder.html",
            {"config": TextTileConfig(markdown="<p>Initial content</p>")},
        )
        soup = BeautifulSoup(html, "html.parser")
        editor_request = soup.find(attrs={"hx-trigger": "bloomerp:widget-change delay:250ms"})

        self.assertIsNotNone(editor_request)
        self.assertIn("JSON.stringify", editor_request["hx-vars"])
        self.assertIn("[data-text-editor-input=true]", editor_request["hx-vars"])

    def test_user_parameter_resolver_replaces_current_user_attribute(self):
        resolver = UserParameterResolver(self.admin_user)

        rendered = resolver.resolve("/employees/?user={{ current_user.id }}")

        self.assertEqual(rendered, f"/employees/?user={self.admin_user.id}")

    def test_user_parameter_resolver_replaces_current_user_with_spaces(self):
        resolver = UserParameterResolver(self.normal_user)

        rendered = resolver.resolve("/employees/?user={{   current_user   }}")

        self.assertEqual(rendered, f"/employees/?user={self.normal_user.pk}")

    def test_link_tile_resolves_current_user_parameters(self):
        """
        Use case: A link tile URL contains a current-user parameter.
        Expected result: Rendering resolves the URL without mutating the saved configuration.
        """
        # 1. Create a link with a current-user parameter.
        config = LinkTileConfig(
            links=[
                Link(
                    url="/employees/?user={{ current_user.id }}",
                    name="Employees",
                    is_internal=True,
                )
            ]
        )
        request = self.factory.get("/")
        request.user = self.admin_user

        # 2. Render the tile.
        html = LinksTileRenderer.render(config, request)

        # 3. Verify the resolved output and unchanged source configuration.
        self.assertIn(f'href="/employees/?user={self.admin_user.id}"', html)
        self.assertEqual(config.links[0].url, "/employees/?user={{ current_user.id }}")

    def test_link_tile_renders_nested_folders(self):
        """
        Use case: A link tile contains nested folders.
        Expected result: Folders render as collapsible levels and the nested link remains navigable.
        """
        # 1. Create two nested folders containing a link.
        config = LinkTileConfig(
            links=[
                Link(
                    name="Sales",
                    is_folder=True,
                    children=[
                        Link(
                            name="Reports",
                            is_folder=True,
                            children=[Link(url="/sales/report/", name="Monthly report", is_internal=True)],
                        )
                    ],
                )
            ]
        )
        request = self.factory.get("/")
        request.user = self.admin_user

        # 2. Render the tile.
        html = LinksTileRenderer.render(config, request)

        # 3. Verify collapsible hierarchy, progressive indentation, and the nested link.
        self.assertEqual(html.count("<details"), 2)
        self.assertGreaterEqual(html.count("ml-4"), 2)
        self.assertIn('href="/sales/report/"', html)
        self.assertIn("Monthly report", html)

    def test_user_parameter_resolver_hides_model_object_without_view_permission(self):
        customer = self.CustomerModel.objects.create(
            first_name="Blocked",
            last_name="Customer",
            age=30,
            created_by=self.normal_user,
        )
        self.normal_user.visible_customers = self.CustomerModel.objects.filter(pk=customer.pk)
        resolver = UserParameterResolver(self.normal_user)

        rendered = resolver.resolve(
            "/customers/?customer={{ current_user.visible_customers.first() }}"
        )

        self.assertEqual(rendered, "/customers/?customer=")
        self.assertTrue(self.CustomerModel.objects.filter(pk=customer.pk).exists())

    def test_user_parameter_resolver_serializes_permitted_model_object_pk(self):
        customer = self.CustomerModel.objects.create(
            first_name="Allowed",
            last_name="Customer",
            age=30,
            created_by=self.normal_user,
        )
        UserPermissionManager(self.normal_user).assign_creator_permission(
            self.CustomerModel,
            field_policy={"__all__": "__all__"},
            row_permissions=["view"],
        )
        self.assertTrue(
            UserPermissionManager(self.normal_user)
            .get_queryset(self.CustomerModel, "view_customer")
            .filter(pk=customer.pk)
            .exists()
        )
        self.normal_user.visible_customers = self.CustomerModel.objects.filter(pk=customer.pk)
        resolver = UserParameterResolver(self.normal_user)

        rendered = resolver.resolve(
            "/customers/?customer={{ current_user.visible_customers.first() }}"
        )

        self.assertEqual(rendered, f"/customers/?customer={customer.pk}")
