

from django.test import TestCase

from bloomerp.workspaces.base import TileTypeDefinition
from bloomerp.workspaces.registry import TILE_TYPE_REGISTRY


class TestBloomerpRegistry(TestCase):
    def test_other_app_can_add_items_to_registry(self):
        """
        UC: Other apps should be able to extend bloomerp by using the registry.
        Therefore, a developer should be able to register an item from inside their app,
        and it should appear within the registry.

        Expected Result: The registry item is registered successfully.
        """
        key = "EXTERNAL_TILE"
        external_tile = TileTypeDefinition(
            name="External Tile",
            description="A tile registered by an external app.",
            icon="fa-solid fa-puzzle-piece",
        )

        try:
            TILE_TYPE_REGISTRY.register(key, external_tile)

            self.assertIn(external_tile, TILE_TYPE_REGISTRY.values())
            self.assertIs(TILE_TYPE_REGISTRY.get(key), external_tile)
            self.assertIs(TILE_TYPE_REGISTRY.EXTERNAL_TILE, external_tile)
        finally:
            TILE_TYPE_REGISTRY.unregister(key)
    
