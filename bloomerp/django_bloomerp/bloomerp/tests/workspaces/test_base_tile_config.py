from django.test import SimpleTestCase

from bloomerp.workspaces.text_tile.model import TextTileConfig


class BaseTileConfigTests(SimpleTestCase):
    def test_concrete_tile_config_accepts_optional_metadata(self):
        """
        Use case: A tile is declared with reusable metadata and type-specific configuration.
        Expected result: The concrete tile config retains both the metadata and its payload.
        """
        # 1. Create a concrete tile configuration with all optional metadata.
        config = TextTileConfig(
            id="welcome",
            name="Welcome",
            description="Introduces users to their workspace.",
            icon="fa-solid fa-hand-wave",
            markdown="Hello!",
        )

        # 2. Verify inherited metadata and the concrete payload remain available.
        self.assertEqual(config.id, "welcome")
        self.assertEqual(config.name, "Welcome")
        self.assertEqual(
            config.description,
            "Introduces users to their workspace.",
        )
        self.assertEqual(config.icon, "fa-solid fa-hand-wave")
        self.assertEqual(config.markdown, "Hello!")

    def test_concrete_tile_config_metadata_is_optional(self):
        """
        Use case: An existing tile config is created without declarative metadata.
        Expected result: Existing construction remains valid and metadata defaults to None.
        """
        # 1. Create a tile configuration using the pre-existing payload-only form.
        config = TextTileConfig(markdown="Existing tile")

        # 2. Verify backward-compatible metadata defaults.
        self.assertIsNone(config.id)
        self.assertIsNone(config.name)
        self.assertIsNone(config.description)
        self.assertIsNone(config.icon)
        self.assertEqual(config.markdown, "Existing tile")
