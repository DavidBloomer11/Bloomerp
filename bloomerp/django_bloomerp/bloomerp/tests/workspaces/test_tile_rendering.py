from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from django.test import RequestFactory

from bloomerp.models.workspaces.tile import Tile
from bloomerp.services.permission_services import UserPermissionManager
from bloomerp.services.workspace_services import render_tile_to_string
from bloomerp.tests.base import BaseBloomerpModelTestCase
from bloomerp.workspaces.links_tile.model import Link, LinkTileConfig
from bloomerp.workspaces.links_tile.render import LinksTileRenderer
from bloomerp.workspaces.canvas_tile.model import CanvasTileConfig
from bloomerp.workspaces.canvas_tile.render import CanvasTileRenderer
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

    def test_saved_canvas_tile_renders_state_height_and_save_url(self):
        """
        Use case: A saved canvas tile is rendered after a user has drawn on it.
        Expected result: The canvas receives its saved state, configured height, and persistence URL.
        """
        # 1. Create a canvas tile with persisted Excalidraw state and a custom height.
        tile = Tile.objects.create(
            name="Planning canvas",
            description="",
            type=TileType.CANVAS_TILE.name,
            schema={"content": {"elements": [{"id": "shape-1"}]}, "height": 640},
            created_by=self.admin_user,
            updated_by=self.admin_user,
        )
        request = self.factory.get("/")
        request.user = self.admin_user

        # 2. Render the saved tile through the workspace rendering service.
        html = render_tile_to_string(tile, request)
        soup = BeautifulSoup(html, "html.parser")
        canvas = soup.find(attrs={"bloomerp-component": "workspace-tile-canvas"})

        # 3. Verify the persisted state and save context are present.
        self.assertIsNotNone(canvas)
        self.assertEqual(canvas["style"], "height: 640px;")
        self.assertIn('"shape-1"', canvas["data-initial-state"])
        self.assertEqual(canvas["data-save-url"], f"/api/tiles/{tile.pk}/canvas-state/")

    def test_canvas_preview_does_not_render_save_url(self):
        """
        Use case: A canvas is rendered in the tile builder before a Tile exists.
        Expected result: The preview has no persistence URL and cannot send state updates.
        """
        # 1. Render a canvas config directly, matching the builder preview path.
        request = self.factory.get("/")
        request.user = self.admin_user
        html = CanvasTileRenderer.render(CanvasTileConfig(height=512), request)
        canvas = BeautifulSoup(html, "html.parser").find(
            attrs={"bloomerp-component": "workspace-tile-canvas"}
        )

        # 2. Verify height still applies while persistence remains disabled.
        self.assertIsNotNone(canvas)
        self.assertEqual(canvas["style"], "height: 512px;")
        self.assertNotIn("data-save-url", canvas.attrs)

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
        Use case: A workspace link tile points to an internal Bloomerp URL.
        Expected result: The tile renders an HTMX navigation link with resolved parameters.
        """
        # 1. Render a link tile whose URL contains a current-user template parameter.
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

        # 3. Verify the original config is preserved and rendered links use HTMX navigation.
        resolved_url = f"/employees/?user={self.admin_user.id}"
        self.assertIn(f'href="/employees/?user={self.admin_user.id}"', html)
        self.assertIn(f'hx-get="{resolved_url}"', html)
        self.assertIn('hx-target="#main-content"', html)
        self.assertIn('hx-push-url="true"', html)
        self.assertIn('hx-swap="innerHTML"', html)
        self.assertEqual(config.links[0].url, "/employees/?user={{ current_user.id }}")

    def test_link_tile_leaves_external_links_as_regular_anchors(self):
        """
        Use case: A workspace link tile points to an external URL.
        Expected result: The tile renders a regular anchor without HTMX navigation.
        """
        # 1. Render a link tile with an external URL.
        config = LinkTileConfig(
            links=[
                Link(
                    url="https://example.com/docs",
                    name="Docs",
                    is_internal=False,
                )
            ]
        )
        request = self.factory.get("/")
        request.user = self.admin_user

        # 2. Render the tile.
        html = LinksTileRenderer.render(config, request)

        # 3. Verify external navigation remains a normal browser link.
        self.assertIn('href="https://example.com/docs"', html)
        self.assertNotIn("hx-get=", html)
        self.assertNotIn("hx-target=", html)

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
