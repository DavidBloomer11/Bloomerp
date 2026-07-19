from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import SimpleTestCase

from bloomerp.components.workspaces.preview_workspace_tile import (
    _build_link_builder_items,
    _build_link_folder_options,
    _get_link_route_suggestions,
    _render_link_icon_picker,
)
from bloomerp.router import BloomerpRoute, RouteType, ViewType
from bloomerp.workspaces.links_tile.model import (
    AddFolderHandler,
    AddFolderOperation,
    AddLinkHandler,
    AddLinkOperation,
    Link,
    LinkTileConfig,
    MoveLinkHandler,
    MoveLinkOperation,
    RemoveLinkHandler,
    RemoveLinkOperation,
    UpdateLinkHandler,
    UpdateLinkOperation,
)


class LinksTileOperationTests(SimpleTestCase):
    def test_existing_flat_schema_remains_valid(self):
        """
        Use case: A link tile saved before folder support is loaded.
        Expected result: The existing link remains a normal link with no children.
        """
        # 1. Load the legacy schema without the new folder fields.
        config = LinkTileConfig(links=[{"url": "/customers/", "name": "Customers"}])

        # 2. Verify backward-compatible defaults were applied.
        self.assertFalse(config.links[0].is_folder)
        self.assertEqual(config.links[0].children, [])
        self.assertEqual(config.links[0].icon, "")

    def test_add_link_inside_nested_folder(self):
        """
        Use case: A user adds a link to a nested folder.
        Expected result: The link is created in that folder and marked internal.
        """
        # 1. Create two levels of folders.
        config = LinkTileConfig(
            links=[Link(name="People", is_folder=True, children=[Link(name="Teams", is_folder=True)])]
        )

        # 2. Add a link to the inner folder.
        response = AddLinkHandler.handle(
            config,
            AddLinkOperation(url="/employees/", name="Employees", parent_path=[0, 0]),
        )

        # 3. Verify the nested link configuration.
        link = response.config.links[0].children[0].children[0]
        self.assertEqual(link.name, "Employees")
        self.assertEqual(link.url, "/employees/")
        self.assertTrue(link.is_internal)

    def test_icons_can_be_added_to_links_and_folders(self):
        """
        Use case: A user chooses optional icons while adding a folder and link.
        Expected result: Both icon values are stored in the tile configuration.
        """
        # 1. Add an icon-bearing folder and link.
        config = LinkTileConfig(links=[])
        AddFolderHandler.handle(
            config,
            AddFolderOperation(name="Sales", icon="fa-solid fa-briefcase"),
        )
        AddLinkHandler.handle(
            config,
            AddLinkOperation(
                url="/leads/",
                name="Leads",
                icon="fa-solid fa-user",
                parent_path=[0],
            ),
        )

        # 2. Verify both optional icons were persisted.
        self.assertEqual(config.links[0].icon, "fa-solid fa-briefcase")
        self.assertEqual(config.links[0].children[0].icon, "fa-solid fa-user")

    def test_folder_can_be_added_and_removed_with_its_children(self):
        """
        Use case: A user creates and later removes a folder.
        Expected result: Removing the folder also removes its nested links.
        """
        # 1. Add a folder and place a link inside it.
        config = LinkTileConfig(links=[])
        AddFolderHandler.handle(config, AddFolderOperation(name="Sales"))
        AddLinkHandler.handle(
            config,
            AddLinkOperation(url="/leads/", name="Leads", parent_path=[0]),
        )

        # 2. Remove the folder by its index path.
        response = RemoveLinkHandler.handle(config, RemoveLinkOperation(path=[0]))

        # 3. Verify the complete subtree was removed.
        self.assertEqual(response.config.links, [])

    def test_update_targets_exact_nested_link(self):
        """
        Use case: Two nested links have similar values and one is edited.
        Expected result: Only the item at the submitted index path changes.
        """
        # 1. Create two links with the same name in a folder.
        config = LinkTileConfig(
            links=[
                Link(
                    name="Reports",
                    is_folder=True,
                    children=[Link(url="/one/", name="Report"), Link(url="/two/", name="Report")],
                )
            ]
        )

        # 2. Update only the second link.
        UpdateLinkHandler.handle(
            config,
            UpdateLinkOperation(path=[0, 1], url="/updated/", name="Updated report"),
        )

        # 3. Verify the sibling was untouched.
        self.assertEqual(config.links[0].children[0].url, "/one/")
        self.assertEqual(config.links[0].children[1].url, "/updated/")
        self.assertEqual(config.links[0].children[1].name, "Updated report")

    def test_move_reorders_items_within_the_same_folder(self):
        """
        Use case: A user moves a nested link upward.
        Expected result: Its order changes only within the containing folder.
        """
        # 1. Create an ordered set of nested links.
        config = LinkTileConfig(
            links=[
                Link(
                    name="Folder",
                    is_folder=True,
                    children=[Link(url="/first/", name="First"), Link(url="/second/", name="Second")],
                )
            ]
        )

        # 2. Move the second link upward.
        MoveLinkHandler.handle(config, MoveLinkOperation(path=[0, 1], direction="up"))

        # 3. Verify the new sibling order.
        self.assertEqual([link.name for link in config.links[0].children], ["Second", "First"])

    def test_update_link_can_change_its_folder_and_icon(self):
        """
        Use case: A user edits an existing link and selects a different folder and icon.
        Expected result: The updated link moves to that folder with its new icon.
        """
        # 1. Put a link before its destination folder to exercise shifting indexes.
        config = LinkTileConfig(
            links=[
                Link(url="/report/", name="Report"),
                Link(name="Sales", is_folder=True),
            ]
        )

        # 2. Update and move the link to the following folder.
        UpdateLinkHandler.handle(
            config,
            UpdateLinkOperation(
                path=[0],
                url="/reports/",
                name="Reports",
                icon="fa-solid fa-chart-bar",
                parent_path=[1],
            ),
        )

        # 3. Verify the destination object received the link despite the root index shift.
        self.assertEqual(len(config.links), 1)
        moved_link = config.links[0].children[0]
        self.assertEqual(moved_link.name, "Reports")
        self.assertEqual(moved_link.icon, "fa-solid fa-chart-bar")


class LinksTileBuilderHelperTests(SimpleTestCase):
    def test_builder_template_renders_nested_controls_and_route_suggestions(self):
        """
        Use case: The link builder opens with a nested link configuration.
        Expected result: It renders editable route suggestions and controls for nested items.
        """
        # 1. Prepare a folder, nested link, and route suggestion.
        links = [Link(name="Sales", is_folder=True, children=[Link(url="/leads/", name="Leads")])]
        context = {
            "link_builder_items": _build_link_builder_items(links),
            "link_folder_options": _build_link_folder_options(links),
            "link_route_suggestions": [
                {"url": "/customers/", "name": "Customers", "description": "Customer list"}
            ],
            "add_link_icon_picker": _render_link_icon_picker("add_link_icon"),
            "add_folder_icon_picker": _render_link_icon_picker("add_folder_icon"),
        }

        # 2. Render the complete builder template.
        html = render_to_string("components/workspaces/tile_builders/links_tile_builder.html", context)

        # 3. Verify suggestions, nesting operations, and edit controls are present.
        self.assertIn('value="/customers/"', html)
        self.assertIn("move_link", html)
        self.assertIn("parent_path", html)
        self.assertIn("Edit", html)
        self.assertIn('data-name="Customers"', html)
        self.assertIn('name="add_link_icon"', html)
        self.assertIn("data-edit-link-parent", html)

    def test_builder_helpers_preserve_nested_paths(self):
        """
        Use case: The builder renders nested folders and links.
        Expected result: Every item and folder option receives its full index path.
        """
        # 1. Build a nested configuration.
        links = [
            Link(
                name="Sales",
                is_folder=True,
                children=[Link(name="Reports", is_folder=True, children=[Link(url="/report/", name="Report")])],
            )
        ]

        # 2. Generate recursive builder data and folder choices.
        items = _build_link_builder_items(links)
        folders = _build_link_folder_options(links)

        # 3. Verify paths and indentation labels.
        self.assertEqual(items[0]["children"][0]["children"][0]["path"], [0, 0, 0])
        self.assertEqual(folders, [{"name": "Sales", "path": [0]}, {"name": "— Reports", "path": [0, 0]}])

    @patch("bloomerp.components.workspaces.preview_workspace_tile.reverse")
    @patch("bloomerp.components.workspaces.preview_workspace_tile.router.get_routes")
    def test_route_suggestions_exclude_non_navigable_routes(self, get_routes, reverse):
        """
        Use case: The URL input offers application route suggestions.
        Expected result: Suggestions contain navigable pages but omit components and parameterized routes.
        """
        # 1. Provide page, component, and parameterized routes.
        get_routes.return_value = [
            BloomerpRoute("customers/", RouteType.APP, "Customers", "customers", ViewType.FUNCTION, lambda: None, description="Customer list"),
            BloomerpRoute("components/search/", RouteType.APP, "Search", "components_search", ViewType.FUNCTION, lambda: None),
            BloomerpRoute("customers/<int:pk>/", RouteType.APP, "Customer", "customer", ViewType.FUNCTION, lambda: None),
        ]
        reverse.return_value = "/customers/"

        # 2. Build the suggestions.
        suggestions = _get_link_route_suggestions()

        # 3. Verify only the navigable page is offered with searchable metadata.
        self.assertEqual(
            suggestions,
            [{"url": "/customers/", "name": "Customers", "description": "Customer list"}],
        )
        reverse.assert_called_once_with("customers")
