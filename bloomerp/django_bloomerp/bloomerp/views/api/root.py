from django.urls import NoReverseMatch
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse

from bloomerp.views.api.base import BaseBloomerpApiView
from bloomerp.router import BloomerpRoute, RouteType, ViewType, router
from bloomerp.utils.api import ApiAccessResolver


API_ROUTE_TYPES = {
    RouteType.API,
    RouteType.API_MODEL,
    RouteType.API_DETAIL,
}


@router.register(
    path="/",
    route_type="api",
    name="API Root",
    url_name="api_root",
)
class BloomerpApiRootView(BaseBloomerpApiView):
    """
    API root view for the Bloomerp application.
    This view provides a list of available API endpoints.
    """
    permission_classes = ()

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to the API root view.
        Returns a list of available API endpoints.
        """
        routes = [
            self._serialize_route(request, route)
            for route in self._get_visible_api_routes(request)
        ]
        return Response(
            {
                "routes": routes,
                "nested": self._build_nested_routes(routes),
            }
        )

    def _get_visible_api_routes(self, request) -> list[BloomerpRoute]:
        visible_routes: list[BloomerpRoute] = []

        for route in router.get_routes():
            if route.route_type not in API_ROUTE_TYPES:
                continue
            if route.view is self.__class__:
                continue
            if not self._should_include_route(request, route):
                continue
            visible_routes.append(route)

        return visible_routes

    def _should_include_route(self, request, route: BloomerpRoute) -> bool:
        if route.model is not None and not self._has_custom_permission_classes(route):
            action = "retrieve" if route.route_type == RouteType.API_DETAIL else "list"
            return ApiAccessResolver(request).has_read_contract(route.model, action)

        return self._route_permissions_allow(request, route)

    def _route_permissions_allow(self, request, route: BloomerpRoute) -> bool:
        if route.view_type != ViewType.CLASS:
            return True

        view = route.view()
        view.request = request
        view.kwargs = {}
        view.args = ()

        permission_classes = getattr(route.view, "permission_classes", ()) or ()
        for permission_class in permission_classes:
            if not callable(permission_class):
                continue
            if not permission_class().has_permission(request, view):
                return False
        return True

    def _has_custom_permission_classes(self, route: BloomerpRoute) -> bool:
        if route.view_type != ViewType.CLASS:
            return True

        permission_classes = tuple(getattr(route.view, "permission_classes", ()) or ())
        return permission_classes != (IsAuthenticated,)

    def _serialize_route(self, request, route: BloomerpRoute) -> dict:
        path_template = self._path_template(route.path)
        route_data = {
            "name": route.name,
            "urlName": route.url_name,
            "type": route.route_type.value,
            "path": path_template,
            "methods": self._get_route_methods(route),
        }

        url = self._reverse_route(request, route)
        if url is not None:
            route_data["url"] = url

        if route.model is not None:
            route_data["model"] = {
                "appLabel": route.model._meta.app_label,
                "modelName": route.model._meta.model_name,
                "verboseName": str(route.model._meta.verbose_name),
                "verboseNamePlural": str(route.model._meta.verbose_name_plural),
            }

        return route_data

    def _reverse_route(self, request, route: BloomerpRoute) -> str | None:
        if "<" in route.path:
            return None

        try:
            return reverse(route.url_name, request=request)
        except NoReverseMatch:
            return request.build_absolute_uri(route.path)

    def _path_template(self, path: str) -> str:
        template = path
        template = template.replace("<int_or_uuid:pk>", "{pk}")
        template = template.replace("<int:pk>", "{pk}")
        template = template.replace("<str:pk>", "{pk}")
        return template

    def _get_route_methods(self, route: BloomerpRoute) -> list[str]:
        actions = getattr(route.view, "actions", None)
        if actions:
            return [
                method.upper()
                for method in actions.keys()
                if method.lower() != "head"
            ]

        return [
            method.upper()
            for method in getattr(route.view, "http_method_names", [])
            if method.lower() not in {"head", "options", "trace"}
            and hasattr(route.view, method.lower())
        ]

    def _build_nested_routes(self, routes: list[dict]) -> dict:
        root: dict = {}

        for route in routes:
            parts = self._get_route_parts(route["path"])
            if not parts:
                continue

            current = root
            for index, part in enumerate(parts):
                node = current.setdefault(
                    part,
                    {
                        "path": self._join_api_parts(parts[: index + 1]),
                        "children": {},
                    },
                )

                if index == len(parts) - 1:
                    node["route"] = route

                current = node["children"]

        return self._prune_empty_children(root)

    def _get_route_parts(self, path: str) -> list[str]:
        return [
            part
            for part in path.strip("/").split("/")
            if part and part != "api"
        ]

    def _join_api_parts(self, parts: list[str]) -> str:
        if not parts:
            return "/api/"
        return "/api/" + "/".join(parts) + "/"

    def _prune_empty_children(self, value):
        if isinstance(value, dict):
            pruned = {
                key: self._prune_empty_children(child)
                for key, child in value.items()
            }
            if "children" in pruned and not pruned["children"]:
                pruned.pop("children")
            return pruned
        return value
