from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
from typing import Self

from django import apps
from django.db.models import Model
from django.utils.translation import gettext, pgettext
from pydantic import BaseModel, Field, SerializeAsAny, field_validator, model_validator

from bloomerp.models.definition import (
    BloomerpModelConfig,
    WorkspaceLayout,
    validate_declarative_tile_configs,
)
from bloomerp.workspaces.base import BaseTileConfig

logger = logging.getLogger(__name__)


class BaseConfig(BaseModel):
    id: str
    name: str
    description: str | None = None
    enabled: bool = True


class ModuleConfig(BaseConfig):
    code: str 
    icon: str = "fa-solid fa-folder"
    parent_module_id: str | None = None
    visible: bool = True
    full_id: str | None = None
    route_path: str | None = None
    root_module_id: str | None = None
    depth: int = 0
    owner_app_label: str | None = None
    tiles: list[SerializeAsAny[BaseTileConfig]] = Field(default_factory=list)
    workspaces: list[WorkspaceLayout] = Field(default_factory=list)

    def _translation_context(self, field: str) -> str:
        owner = self.owner_app_label or "bloomerp"
        return f"{owner}:module:{field}"

    def _localized_message(self, message: str | None, field: str) -> str:
        if not message:
            return ""
        translated = pgettext(self._translation_context(field), message)
        if translated == message:
            # Reuse context-free catalogs while module-specific entries are
            # introduced and translated.
            translated = gettext(message)
        return translated

    @property
    def localized_name(self) -> str:
        return self._localized_message(self.name, "name")

    @property
    def localized_description(self) -> str:
        return self._localized_message(self.description, "description")

    @field_validator("tiles")
    @classmethod
    def validate_tiles(
        cls,
        value: list[BaseTileConfig],
    ) -> list[BaseTileConfig]:
        return validate_declarative_tile_configs(
            value,
            owner=cls.__name__,
        )

    @model_validator(mode="after")
    def validate_workspaces(self) -> Self:
        if not self.workspaces:
            return self

        workspace_names = [workspace.name.strip() for workspace in self.workspaces]
        if any(not name for name in workspace_names):
            raise ValueError("Every configured workspace must have a name.")
        if len(workspace_names) != len(set(workspace_names)):
            raise ValueError("Configured workspace names must be unique within a module.")

        default_count = sum(workspace.is_default for workspace in self.workspaces)
        if default_count != 1:
            raise ValueError(
                "A module with configured workspaces must define exactly one default workspace."
            )

        for workspace, name in zip(self.workspaces, workspace_names):
            workspace.name = name
        return self


class BloomerpModule:
    """Django-style authoring surface for Python module definitions."""

    id: str | None = None
    name: str | None = None
    code: str | None = None
    description: str | None = None
    enabled: bool = True
    icon: str = "fa-solid fa-folder"
    parent_module_id: str | None = None
    parent: str | None = None
    visible: bool = True
    route_path: str | None = None
    tiles: list[BaseTileConfig] = []
    workspaces: list[WorkspaceLayout] = []

    @classmethod
    def to_config(cls, *, owner_app_label: str | None = None) -> ModuleConfig:
        data = {
            "id": cls.id,
            "name": cls.name,
            "description": cls.description,
            "enabled": cls.enabled,
            "icon": cls.icon,
            "visible": cls.visible,
            "route_path": cls.route_path,
            "owner_app_label": owner_app_label,
            "tiles": list(cls.tiles),
            "workspaces": list(cls.workspaces),
        }

        parent_module_id = cls.parent_module_id or cls.parent
        if parent_module_id is not None:
            data["parent_module_id"] = parent_module_id

        data["code"] = cls.code or (cls.id.upper() if cls.id else None)
        return ModuleConfig(**data)


class ModuleRegistry:
    def __init__(self):
        self.items: dict[str, ModuleConfig] = {}
        self._module_models: dict[str, dict[str, type[Model]]] = {}
        self._declared_route_paths: dict[int, str] = {}

    def register(self, module: ModuleConfig) -> None:
        module_key = module.full_id or module.id
        if module_key in self.items:
            logger.warning("Module with ID '%s' already exists. Overwriting.", module_key)
        if module.route_path:
            self._declared_route_paths[id(module)] = module.route_path.strip("/")
        self.items[module_key] = module

    def get(self, module_id: str | None) -> ModuleConfig | None:
        if not module_id:
            return None
        return self.items.get(module_id)

    def get_all(self) -> dict[str, ModuleConfig]:
        return self.items.copy()

    def get_enabled(self) -> dict[str, ModuleConfig]:
        return {
            module_id: module
            for module_id, module in self.items.items()
            if module.enabled
        }

    def get_root_modules(self) -> list[ModuleConfig]:
        return [
            module
            for module in self.items.values()
            if module.parent_module_id is None
        ]

    def get_children(self, module_id: str | None) -> list[ModuleConfig]:
        if module_id is None:
            return self.get_root_modules()
        return [
            module
            for module in self.items.values()
            if module.parent_module_id == module_id
        ]

    def get_ancestors(self, module_id: str | None) -> list[ModuleConfig]:
        ancestors: list[ModuleConfig] = []
        current = self.get(module_id)
        seen: set[str] = set()
        while current and current.parent_module_id:
            if current.parent_module_id in seen:
                logger.warning("Detected circular module ancestry while resolving '%s'.", module_id)
                break
            seen.add(current.parent_module_id)
            parent = self.get(current.parent_module_id)
            if not parent:
                break
            ancestors.append(parent)
            current = parent
        ancestors.reverse()
        return ancestors

    def get_lineage(self, module_id: str | None) -> list[ModuleConfig]:
        module = self.get(module_id)
        if not module:
            return []
        return [*self.get_ancestors(module_id), module]

    def get_root(self, module_id: str | None) -> ModuleConfig | None:
        lineage = self.get_lineage(module_id)
        if not lineage:
            return None
        return lineage[0]

    def get_models_for_module(self, module_id: str, include_descendants: bool = False) -> list[type[Model]]:
        module_ids = {module_id}
        if include_descendants:
            module_ids.update(self._collect_descendant_ids(module_id))

        models: dict[str, type[Model]] = {}
        for current_id in module_ids:
            for model_key, model in self._module_models.get(current_id, {}).items():
                models.setdefault(model_key, model)
        return list(models.values())

    def get_tiles_for_module(
        self,
        module_id: str,
        include_descendants: bool = False,
    ) -> list[BaseTileConfig]:
        """Return module-owned and model-owned tile definitions for a module."""
        module_ids = [module_id]
        if include_descendants:
            module_ids.extend(sorted(self._collect_descendant_ids(module_id)))

        tiles: list[BaseTileConfig] = []
        for current_id in module_ids:
            module = self.get(current_id)
            if module is not None:
                tiles.extend(module.tiles)

            for model in self.get_models_for_module(current_id):
                config = self._get_model_config(model)
                if config is not None:
                    tiles.extend(config.tiles)
        return tiles

    def get_tile_for_module(
        self,
        module_id: str,
        tile_id: str,
    ) -> BaseTileConfig | None:
        """Resolve a declarative tile ID from a module or one of its models."""
        normalized_tile_id = str(tile_id).strip()
        for tile in self.get_tiles_for_module(module_id):
            if tile.id == normalized_tile_id:
                return tile
        return None

    def get_module_for_model(self, model: type[Model]) -> ModuleConfig | None:
        config = self._get_model_config(model)
        if config and config.module:
            return self.get(config.module)

        model_key = model._meta.label_lower
        for module_id, models in self._module_models.items():
            if model_key in models:
                return self.get(module_id)
        return None

    def refresh(self) -> None:
        self.clear()

        for app_config in apps.apps.get_app_configs():
            try:
                module_package = importlib.import_module(f"{app_config.name}.modules")
            except ModuleNotFoundError:
                continue

            for _, attribute in inspect.getmembers(module_package, inspect.isclass):
                self._register_module_class(
                    attribute,
                    source=app_config.name,
                    owner_app_label=app_config.label,
                )

            if not hasattr(module_package, "__path__"):
                continue

            for _, module_name, _ in pkgutil.iter_modules(module_package.__path__, module_package.__name__ + "."):
                if module_name.endswith(".definition"):
                    continue
                try:
                    imported_module = importlib.import_module(module_name)
                except Exception as exc:
                    logger.error("Error importing module '%s': %s", module_name, exc)
                    continue

                for _, attribute in inspect.getmembers(imported_module, inspect.isclass):
                    self._register_module_class(
                        attribute,
                        source=module_name,
                        owner_app_label=app_config.label,
                    )

        try:
            from bloomerp_modules.utils.reader import scan_modules_directory
        except Exception:
            scan_modules_directory = None

        if scan_modules_directory is not None:
            try:
                for module in scan_modules_directory():
                    module.owner_app_label = module.owner_app_label or "bloomerp_modules"
                    self.register(module)
            except Exception as exc:
                logger.error("Error loading YAML module definitions: %s", exc)

        self._rebuild_hierarchy_metadata()
        self._register_models_from_apps()
        self.validate_workspace_tile_references()

    def validate_workspace_tile_references(self) -> None:
        """Ensure workspace items resolve to unique tile IDs in their module."""
        for module_id, module in self.items.items():
            tile_definitions: dict[str, BaseTileConfig] = {}
            for tile in self.get_tiles_for_module(module_id):
                tile_id = str(tile.id)
                if tile_id in tile_definitions:
                    raise ValueError(
                        f"Duplicate tile id '{tile_id}' found in module '{module_id}'."
                    )
                tile_definitions[tile_id] = tile

            for workspace in module.workspaces:
                for row in workspace.rows:
                    for item in row.items:
                        tile_id = str(item.id).strip()
                        if tile_id not in tile_definitions:
                            raise ValueError(
                                f"Workspace '{workspace.name}' on module '{module_id}' "
                                f"references unknown tile id '{tile_id}'."
                            )

    def clear(self) -> None:
        self.items.clear()
        self._module_models.clear()
        self._declared_route_paths.clear()

    def __len__(self) -> int:
        return len(self.items)

    def __contains__(self, module_id: str) -> bool:
        return module_id in self.items

    def _register_models_from_apps(self) -> None:
        self._module_models.clear()
        for model in apps.apps.get_models():
            config = self._get_model_config(model)
            module_id = None
            if config and config.module:
                module_id = config.module
            if not module_id:
                module_id = "misc"

            module = self.get(module_id)
            if module is None:
                module = ModuleConfig(
                    id=module_id.split(".")[-1],
                    name=module_id.split(".")[-1].replace("_", " ").replace("-", " ").title(),
                    code=module_id.split(".")[-1],
                    full_id=module_id,
                    owner_app_label=model._meta.app_label,
                )
                self.register(module)
                self._rebuild_hierarchy_metadata()

            self._add_model_to_module(module, model)

    def _get_model_config(self, model: type[Model]) -> BloomerpModelConfig | None:
        config = getattr(model, "bloomerp_config", None)
        if isinstance(config, BloomerpModelConfig):
            return config
        return None

    def _register_module_class(
        self,
        attribute: type,
        source: str,
        owner_app_label: str,
    ) -> None:
        if attribute in {ModuleConfig, BloomerpModule}:
            return

        try:
            if issubclass(attribute, ModuleConfig):
                module = attribute()
                module.owner_app_label = module.owner_app_label or owner_app_label
                self.register(module)
                return

            if issubclass(attribute, BloomerpModule):
                self.register(attribute.to_config(owner_app_label=owner_app_label))
                return
        except TypeError:
            return
        except Exception as exc:
            logger.error(
                "Error instantiating module '%s' in '%s': %s",
                attribute.__name__,
                source,
                exc,
            )

    def _add_model_to_module(self, module: ModuleConfig, model: type[Model]) -> None:
        module_key = module.full_id or module.id
        module_models = self._module_models.setdefault(module_key, {})
        module_models.setdefault(model._meta.label_lower, model)

    def _collect_descendant_ids(self, module_id: str) -> set[str]:
        descendants: set[str] = set()
        pending = [module_id]
        while pending:
            current_id = pending.pop()
            for child in self.get_children(current_id):
                child_id = child.full_id or child.id
                if child_id in descendants:
                    continue
                descendants.add(child_id)
                pending.append(child_id)
        return descendants

    def _rebuild_hierarchy_metadata(self) -> None:
        for module in self.items.values():
            module.full_id = module.full_id or (
                f"{module.parent_module_id}.{module.id}" if module.parent_module_id else module.id
            )

        self.items = {
            module.full_id or module.id: module
            for module in self.items.values()
        }

        for module in self.items.values():
            lineage = self.get_lineage(module.full_id or module.id)
            if not lineage:
                module.route_path = (
                    self._declared_route_paths.get(id(module))
                    or module.id.lower()
                )
                module.root_module_id = module.full_id or module.id
                module.depth = 0
                continue

            route_path = ""
            for lineage_module in lineage:
                declared_path = self._declared_route_paths.get(id(lineage_module))
                if declared_path:
                    route_path = declared_path
                else:
                    route_path = "/".join(
                        part
                        for part in (route_path, lineage_module.id.lower())
                        if part
                    )

            module.route_path = route_path
            module.root_module_id = lineage[0].full_id or lineage[0].id
            module.depth = len(lineage) - 1


module_registry = ModuleRegistry()
