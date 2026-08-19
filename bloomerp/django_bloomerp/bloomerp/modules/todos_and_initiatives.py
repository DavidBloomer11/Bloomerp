from bloomerp.models.definition import LayoutItem, LayoutRow, WorkspaceLayout
from bloomerp.modules.definition import BloomerpModule
from bloomerp.workspaces.links_tile.model import Link, LinkTileConfig


class TodosAndInitiatives(BloomerpModule):
    id = "todos_and_initiatives"
    name = "Todos & Initiatives"
    code = "todos"
    description = "Manage todos and initiatives within the ERP system."
    icon = "fa fa-tasks"
    route_path = "todos-and-initiatives"

    tiles = [
        LinkTileConfig(
            id="todos:quick_links",
            name="Todo shortcuts",
            description="Quick access to Todo actions.",
            icon="fa-solid fa-list-check",
            links=[
                Link(
                    name="View all todos",
                    url_name="todos_model",
                    is_internal=True,
                ),
                Link(
                    name="My todo's",
                    url="/todos-and-initiatives/todos?assigned_to={{current_user.id}}",
                ),
                Link(
                    name="Create a todo",
                    url_name="todos_add",
                    is_internal=True,
                ),
            ],
        ),
        LinkTileConfig(
            id="initiatives:quick_links",
            name="Initiative shortcuts",
            description="Quick access to Initiative actions.",
            icon="fa-solid fa-bullseye",
            links=[
                Link(
                    name="View all initiatives",
                    url_name="initiatives_model",
                    is_internal=True,
                ),
                Link(
                    name="Create an initiative",
                    url_name="initiatives_add",
                    is_internal=True,
                ),
            ],
        ),
    ]

    workspaces = [
        WorkspaceLayout(
            name="Todos & Initiatives overview",
            is_default=True,
            rows=[
                LayoutRow(
                    title="At a glance",
                    columns=4,
                    items=[
                        LayoutItem(id="todos:number_of_todos"),
                        LayoutItem(id="todos:open_todos"),
                        LayoutItem(id="todos:completion_rate"),
                        LayoutItem(id="todos:average_completion_speed"),
                    ],
                ),
                LayoutRow(
                    title="Quick access",
                    columns=2,
                    items=[
                        LayoutItem(id="todos:quick_links"),
                        LayoutItem(id="initiatives:quick_links"),
                    ],
                ),
                LayoutRow(
                    title="Work overview",
                    columns=2,
                    items=[
                        LayoutItem(id="todos:status_distribution"),
                        LayoutItem(id="initiatives:status_distribution"),
                    ],
                ),
                LayoutRow(
                    title="Priority and delivery",
                    columns=2,
                    items=[
                        LayoutItem(id="todos:priority_distribution"),
                        LayoutItem(id="todos:completion_trend"),
                    ],
                ),
            ],
        )
    ]
