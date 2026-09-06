from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.test import TestCase

from bloomerp.models.definition import BloomerpModelConfig, get_model_config
from bloomerp.services.sql_services import SqlExecutor
from bloomerp.workspaces.analytics_tile.model import AnalyticsTileConfig, AnalyticsTileType
from bloomerp.workspaces.base import BaseTileConfig
from bloomerp.workspaces.registry import TILE_TYPE_REGISTRY


class BloomerpModelTestCase(TestCase):
    """Base class providing common configuration checks for a model."""

    model: type[models.Model] | None = None

    def get_model_config(self) -> BloomerpModelConfig | None:
        """Return the configured model's Bloomerp metadata."""
        if self.model is None:
            return None
        return get_model_config(self.model)

    def test_model_config_is_valid(self) -> None:
        """
        Use case: A model declares Bloomerp configuration.
        Expected result: The configuration can be validated from its serialized form.
        """
        # 1. Do not execute the reusable base class itself.
        config = self.get_model_config()
        if config is None:
            return

        # 2. Revalidate the complete configuration instead of trusting import-time state.
        validated = BloomerpModelConfig.model_validate(config.__dict__)
        self.assertIsInstance(validated, BloomerpModelConfig)

        # 3. Validate configured layout, search, and dataview field references.
        for field_name, source in self.get_configured_field_references(config):
            with self.subTest(field_name=field_name, source=source):
                self.assert_model_has_field(field_name, source=source)

    def test_model_tiles_are_valid(self) -> None:
        """
        Use case: A model declares reusable workspace tiles.
        Expected result: Every tile is registered and valid; analytics SQL executes.
        """
        # 1. Load every tile from the model configuration.
        config = self.get_model_config()
        if config is None:
            return

        # 2. Validate each tile independently for useful failure reporting.
        for tile in config.tiles:
            with self.subTest(tile_id=tile.id, tile_type=type(tile).__name__):
                self.validate_tile(tile)

    def validate_tile(self, tile: BaseTileConfig) -> None:
        """Validate one tile, including executing analytics SQL."""
        validated = type(tile).model_validate(tile.model_dump())
        self.assertIsInstance(validated, type(tile))
        TILE_TYPE_REGISTRY.key_for_config(tile)

        if not isinstance(tile, AnalyticsTileConfig):
            return

        AnalyticsTileType.from_key(tile.type)
        response = SqlExecutor().execute_query(tile.query, paginate=False)
        output_columns = set(response.columns)

        configured_fields = {
            field.name for fields in tile.fields.values() for field in fields
        }
        self.assertFalse(
            configured_fields - output_columns,
            "Analytics tile fields are missing from its SQL output: "
            f"{sorted(configured_fields - output_columns)}",
        )

        non_variable_filters = {
            filter_config.field
            for filter_config in tile.filters
            if not filter_config.is_variable
        }
        self.assertFalse(
            non_variable_filters - output_columns,
            "Analytics tile filters are missing from its SQL output: "
            f"{sorted(non_variable_filters - output_columns)}",
        )

    def get_configured_field_references(
        self, config: BloomerpModelConfig
    ) -> list[tuple[str, str]]:
        """Collect model-field references from declarative model configuration."""
        references: list[tuple[str, str]] = []

        detail_settings = config.detail_view_settings
        if detail_settings:
            for layout in detail_settings.layouts:
                for row in layout.rows:
                    for item in row.items:
                        if isinstance(item.id, str):
                            references.append((item.id, f"layout {layout.name!r}"))

        search_fields = config.string_search_settings.string_search_fields or []
        references.extend((field_name, "string search") for field_name in search_fields)

        model_view_settings = config.model_view_settings
        if model_view_settings:
            for dataview in model_view_settings.default_dataviews:
                dataview_name = f"dataview {dataview.name!r}"
                references.extend(
                    (field_name, dataview_name)
                    for field_name in dataview.display_fields
                )
                references.extend(
                    (field_name.split("__", 1)[0], dataview_name)
                    for field_name in dataview.default_filters
                )
                for attribute in (
                    "sort_field",
                    "group_by_field",
                    "start_field",
                    "end_field",
                    "color_grouping_field",
                    "dependency_from_field",
                    "dependency_for_field",
                ):
                    field_name = getattr(dataview, attribute, None)
                    if field_name:
                        references.append((field_name, dataview_name))
                for attribute in ("row_fields", "column_fields", "value_fields"):
                    references.extend(
                        (field_name, dataview_name)
                        for field_name in getattr(dataview, attribute, [])
                    )

        return references

    def assert_model_has_field(self, field_path: str, *, source: str) -> None:
        """Assert that a Django field path or model property can be resolved."""
        if self.model is None:
            raise AssertionError("Model test cases must define model")

        current_model = self.model
        path_parts = field_path.split("__")
        for index, field_name in enumerate(path_parts):
            try:
                field = current_model._meta.get_field(field_name)
            except FieldDoesNotExist:
                is_terminal_property = index == len(path_parts) - 1 and isinstance(
                    getattr(current_model, field_name, None), property
                )
                self.assertTrue(
                    is_terminal_property,
                    f"{source} references unknown field {field_path!r} on "
                    f"{self.model._meta.label}",
                )
                return

            if index == len(path_parts) - 1:
                return

            related_model = getattr(field, "related_model", None)
            self.assertIsNotNone(
                related_model,
                f"{source} traverses non-related field {field_name!r} in "
                f"{field_path!r}",
            )
            current_model = related_model


# Backwards-compatible name used by existing Bloomerp tests.
BaseBloomerpModelTestCase = BloomerpModelTestCase
