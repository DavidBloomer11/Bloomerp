from __future__ import annotations

from collections.abc import Iterable

from django.db.models import Model
from drf_spectacular.views import SpectacularAPIView
from bloomerp.utils.api import ApiAccessResolver
from bloomerp.router import router

@router.register(
    path="schema/",
    route_type="api",
    url_name="schema",
)
class BloomerpOpenAPISchemaView(SpectacularAPIView):
    """
    Custom OpenAPI schema view for the Bloomerp API.
    """

    def _get_schema_response(self, request):
        response = super()._get_schema_response(request)
        if isinstance(response.data, dict):
            response.data = filter_openapi_schema_for_request(response.data, request)
        return response


MODEL_ACTION_BY_METHOD = {
    "post": "create",
    "put": "update",
    "patch": "partial_update",
    "delete": "destroy",
}

READ_METHODS = {"get", "head"}


def filter_openapi_schema_for_request(schema: dict, request, registry=None) -> dict:
    registry = list(registry if registry is not None else _get_router_registry())
    model_routes = [
        route
        for route in (_build_model_route(prefix, viewset) for prefix, viewset, _ in registry)
        if route is not None
    ]
    if not model_routes:
        return schema

    paths = schema.get("paths")
    if isinstance(paths, dict):
        schema["paths"] = _filter_paths_for_request(paths, request, model_routes)

    components = schema.get("components", {})
    schemas = components.get("schemas")
    if isinstance(schemas, dict):
        _trim_model_component_fields(schemas, request, model_routes)
        _prune_unused_components(schema)

    return schema


def _get_router_registry():
    from bloomerp.urls import drf_router

    return drf_router.registry


def _build_model_route(prefix: str, viewset) -> dict | None:
    model = _get_viewset_model(viewset)
    if model is None:
        return None

    component_name = _get_component_name(model, viewset)
    return {
        "prefix": prefix.strip("/"),
        "model": model,
        "viewset": viewset,
        "component_names": {
            component_name,
            f"Patched{component_name}",
        },
    }


def _get_viewset_model(viewset) -> type[Model] | None:
    model = getattr(viewset, "model", None)
    if isinstance(model, type) and issubclass(model, Model):
        return model

    queryset = getattr(viewset, "queryset", None)
    model = getattr(queryset, "model", None)
    if isinstance(model, type) and issubclass(model, Model):
        return model

    return None


def _get_component_name(model: type[Model], viewset) -> str:
    serializer_class = getattr(viewset, "serializer_class", None)
    serializer_name = getattr(serializer_class, "__name__", "")
    if serializer_name.endswith("Serializer"):
        return serializer_name.removesuffix("Serializer")
    return model.__name__


def _filter_paths_for_request(paths: dict, request, model_routes: list[dict]) -> dict:
    filtered_paths = {}
    for path, path_item in paths.items():
        route = _match_model_route(path, model_routes)
        if route is None or not isinstance(path_item, dict):
            filtered_paths[path] = path_item
            continue

        filtered_item = {}
        for method, operation in path_item.items():
            if method not in READ_METHODS and method not in MODEL_ACTION_BY_METHOD:
                filtered_item[method] = operation
                continue

            action = _get_action_for_path_method(path, route, method)
            if _has_schema_action_access(request, route["model"], action):
                filtered_item[method] = operation

        if _has_operations(filtered_item):
            filtered_paths[path] = filtered_item

    return filtered_paths


def _match_model_route(path: str, model_routes: list[dict]) -> dict | None:
    for route in sorted(model_routes, key=lambda candidate: len(candidate["prefix"]), reverse=True):
        prefix_path = f"/api/{route['prefix']}/"
        if path == prefix_path or path.startswith(prefix_path):
            return route
    return None


def _get_action_for_path_method(path: str, route: dict, method: str) -> str:
    if method in READ_METHODS:
        return "retrieve" if _is_detail_path(path, route) else "list"
    return MODEL_ACTION_BY_METHOD[method]


def _is_detail_path(path: str, route: dict) -> bool:
    prefix_path = f"/api/{route['prefix']}/"
    return "{" in path.removeprefix(prefix_path)


def _has_operations(path_item: dict) -> bool:
    return any(method in READ_METHODS or method in MODEL_ACTION_BY_METHOD for method in path_item)


def _has_schema_action_access(request, model: type[Model], action: str) -> bool:
    resolver = ApiAccessResolver(request)
    if action in {"list", "retrieve"}:
        return resolver.has_read_contract(model, action)

    if getattr(resolver.permission_manager.user, "is_superuser", False):
        return True

    if resolver.should_use_user_access(model, action):
        return True

    permission_str = resolver.get_permission_str(model, action)
    return (
        resolver.permission_manager.has_global_permission(model, permission_str)
        or resolver.permission_manager.has_row_level_access(model, permission_str)
    )


def _trim_model_component_fields(schemas: dict, request, model_routes: list[dict]) -> None:
    for route in model_routes:
        allowed_fields = _get_schema_accessible_fields(request, route["model"])
        if allowed_fields is None:
            continue

        for component_name in route["component_names"]:
            schema = schemas.get(component_name)
            if isinstance(schema, dict):
                _trim_component_schema_fields(schema, allowed_fields)


def _get_schema_accessible_fields(request, model: type[Model]) -> set[str] | None:
    resolver = ApiAccessResolver(request)
    allowed_fields: set[str] = set()

    for action in ("list", "retrieve", "create", "update", "partial_update"):
        if not _has_schema_action_access(request, model, action):
            continue

        action_fields = resolver.get_accessible_field_names(model, action)
        if action_fields is None:
            return None
        allowed_fields.update(action_fields)

    return allowed_fields


def _trim_component_schema_fields(schema: dict, allowed_fields: set[str]) -> None:
    properties = schema.get("properties")
    if isinstance(properties, dict):
        schema["properties"] = {
            field_name: field_schema
            for field_name, field_schema in properties.items()
            if field_name in allowed_fields
        }

    required = schema.get("required")
    if isinstance(required, list):
        schema["required"] = [
            field_name for field_name in required if field_name in allowed_fields
        ]


def _prune_unused_components(schema: dict) -> None:
    schemas = schema.get("components", {}).get("schemas")
    if not isinstance(schemas, dict):
        return

    used_refs = _collect_schema_refs(schema.get("paths", {}))
    changed = True
    while changed:
        changed = False
        for ref_name in list(used_refs):
            component_schema = schemas.get(ref_name)
            if component_schema is None:
                continue
            nested_refs = _collect_schema_refs(component_schema)
            new_refs = nested_refs - used_refs
            if new_refs:
                used_refs.update(new_refs)
                changed = True

    for component_name in list(schemas.keys()):
        if component_name not in used_refs:
            schemas.pop(component_name, None)


def _collect_schema_refs(value) -> set[str]:
    refs: set[str] = set()
    for ref in _walk_refs(value):
        prefix = "#/components/schemas/"
        if isinstance(ref, str) and ref.startswith(prefix):
            refs.add(ref.removeprefix(prefix))
    return refs


def _walk_refs(value) -> Iterable[str]:
    if isinstance(value, dict):
        ref = value.get("$ref")
        if ref:
            yield ref
        for child in value.values():
            yield from _walk_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_refs(child)
