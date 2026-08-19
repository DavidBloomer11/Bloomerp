from django.test import SimpleTestCase
from pydantic import ValidationError

from bloomerp.models.definition import BloomerpModelConfig
from bloomerp.workspaces.text_tile.model import TextTileConfig


class BloomerpModelConfigTileTests(SimpleTestCase):
    def test_model_config_accepts_concrete_tile_configs(self):
        """
        Use case: A model declares a reusable concrete tile configuration.
        Expected result: The model config retains its metadata and type-specific payload.
        """
        # 1. Define a text tile on a model configuration.
        tile = TextTileConfig(
            id="summary",
            name="Summary",
            description="A model summary.",
            icon="fa-solid fa-align-left",
            markdown="Model summary",
        )
        config = BloomerpModelConfig(tiles=[tile])

        # 2. Verify the concrete instance remains available through the config.
        self.assertIs(config.tiles[0], tile)
        self.assertEqual(config.tiles[0].markdown, "Model summary")

        # 3. Verify serialization retains both base metadata and subtype fields.
        serialized_tile = config.model_dump()["tiles"][0]
        self.assertEqual(serialized_tile["id"], "summary")
        self.assertEqual(serialized_tile["name"], "Summary")
        self.assertEqual(serialized_tile["markdown"], "Model summary")

    def test_model_config_uses_an_independent_empty_tile_list(self):
        """
        Use case: Multiple model configurations are created without tiles.
        Expected result: Each configuration receives its own empty tile list.
        """
        # 1. Create two model configurations with default tile lists.
        first = BloomerpModelConfig()
        second = BloomerpModelConfig()

        # 2. Mutate one list and verify the other configuration is unaffected.
        first.tiles.append(TextTileConfig(markdown="Only on first"))
        self.assertEqual(len(first.tiles), 1)
        self.assertEqual(second.tiles, [])

    def test_model_config_requires_unique_tile_ids(self):
        """
        Use case: A model declares tiles that workspaces can reference by ID.
        Expected result: Missing and duplicate IDs are rejected during configuration.
        """
        # 1. Verify a declarative tile cannot omit its stable ID.
        with self.assertRaisesRegex(ValidationError, "must have an id"):
            BloomerpModelConfig(
                tiles=[TextTileConfig(name="Missing ID", markdown="")]
            )

        # 2. Verify IDs must be unique within the model configuration.
        with self.assertRaisesRegex(ValidationError, "Duplicate tile id 'summary'"):
            BloomerpModelConfig(
                tiles=[
                    TextTileConfig(id="summary", markdown="First"),
                    TextTileConfig(id="summary", markdown="Second"),
                ]
            )
