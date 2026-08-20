import json

from django.test import TestCase
from django.urls import reverse

from bloomerp.models.workspaces.tile import Tile
from bloomerp.tests.utils.users import create_admin, create_normal_user
from bloomerp.workspaces.tiles import TileType


class CanvasTileStateApiTests(TestCase):
    def setUp(self):
        self.admin_user = create_admin()
        self.normal_user = create_normal_user()

    def create_canvas_tile(self, *, created_by) -> Tile:
        return Tile.objects.create(
            name="Canvas",
            description="",
            type=TileType.CANVAS_TILE.name,
            schema={"content": {}, "height": 480},
            created_by=created_by,
            updated_by=created_by,
        )

    def test_creator_can_save_canvas_state(self):
        """
        Use case: A user changes a canvas tile that they created.
        Expected result: The endpoint persists the new state while retaining other canvas settings.
        """
        # 1. Create a canvas owned by the normal user and authenticate as that user.
        tile = self.create_canvas_tile(created_by=self.normal_user)
        self.client.force_login(self.normal_user)
        url = reverse("api_tile_canvas_state", kwargs={"pk": tile.pk})
        state = {"elements": [{"id": "shape-1"}], "appState": {"zoom": {"value": 1}}}

        # 2. Save the serialized canvas state.
        response = self.client.post(
            url,
            data=json.dumps({"state": state}),
            content_type="application/json",
        )

        # 3. Verify the state is persisted without losing the configured height.
        self.assertEqual(response.status_code, 200)
        tile.refresh_from_db()
        self.assertEqual(tile.schema["content"], state)
        self.assertEqual(tile.schema["height"], 480)
        self.assertEqual(tile.updated_by, self.normal_user)

    def test_non_owner_without_change_permission_cannot_save_canvas_state(self):
        """
        Use case: A user without change access posts state to another user's canvas.
        Expected result: The endpoint rejects the write and leaves the tile unchanged.
        """
        # 1. Create a canvas owned by an administrator and authenticate as another user.
        tile = self.create_canvas_tile(created_by=self.admin_user)
        self.client.force_login(self.normal_user)
        url = reverse("api_tile_canvas_state", kwargs={"pk": tile.pk})

        # 2. Attempt to overwrite the canvas state.
        response = self.client.post(
            url,
            data=json.dumps({"state": {"elements": [{"id": "blocked"}]}}),
            content_type="application/json",
        )

        # 3. Verify access is denied and no state is persisted.
        self.assertEqual(response.status_code, 403)
        tile.refresh_from_db()
        self.assertEqual(tile.schema["content"], {})

    def test_state_endpoint_rejects_non_canvas_tiles(self):
        """
        Use case: A state update is sent to a tile of another type.
        Expected result: The endpoint rejects the payload without changing its schema.
        """
        # 1. Create a text tile and authenticate as its owner.
        tile = Tile.objects.create(
            name="Text",
            description="",
            type=TileType.TEXT_TILE.name,
            schema={"markdown": "Keep me"},
            created_by=self.normal_user,
            updated_by=self.normal_user,
        )
        self.client.force_login(self.normal_user)

        # 2. Attempt to use the canvas state endpoint.
        response = self.client.post(
            reverse("api_tile_canvas_state", kwargs={"pk": tile.pk}),
            data=json.dumps({"state": {"elements": []}}),
            content_type="application/json",
        )

        # 3. Verify the endpoint rejects the tile and preserves its schema.
        self.assertEqual(response.status_code, 400)
        tile.refresh_from_db()
        self.assertEqual(tile.schema, {"markdown": "Keep me"})

    def test_state_endpoint_requires_an_object_state(self):
        """
        Use case: A canvas state request contains an invalid non-object value.
        Expected result: The endpoint returns a validation error and does not update the tile.
        """
        # 1. Create a canvas owned by the authenticated user.
        tile = self.create_canvas_tile(created_by=self.normal_user)
        self.client.force_login(self.normal_user)

        # 2. Post an invalid state value.
        response = self.client.post(
            reverse("api_tile_canvas_state", kwargs={"pk": tile.pk}),
            data=json.dumps({"state": []}),
            content_type="application/json",
        )

        # 3. Verify validation fails and existing state remains intact.
        self.assertEqual(response.status_code, 400)
        tile.refresh_from_db()
        self.assertEqual(tile.schema["content"], {})
