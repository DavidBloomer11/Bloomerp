from django.test import SimpleTestCase

from bloomerp.components.layout.save_layout_object import (
    _protected_layout_items_are_unchanged,
)
from bloomerp.models.base_bloomerp_model import FieldLayout, LayoutItem, LayoutRow


class TestSaveLayoutObject(SimpleTestCase):
    def test_protected_item_must_remain_structurally_unchanged(self):
        existing = FieldLayout(
            rows=[
                LayoutRow(
                    columns=2,
                    title="Details",
                    items=[LayoutItem(id="protected", colspan=1)],
                )
            ]
        )
        submitted = FieldLayout(
            rows=[
                LayoutRow(
                    columns=2,
                    title="Details",
                    items=[LayoutItem(id="protected", colspan=2)],
                )
            ]
        )

        self.assertFalse(
            _protected_layout_items_are_unchanged(
                existing_layout=existing,
                submitted_layout=submitted,
                protected_ids={"protected"},
            )
        )

    def test_accessible_items_can_change_around_a_protected_item(self):
        existing = FieldLayout(
            rows=[
                LayoutRow(
                    columns=2,
                    title="Details",
                    items=[
                        LayoutItem(id="accessible"),
                        LayoutItem(id="protected"),
                    ],
                )
            ]
        )
        submitted = FieldLayout(
            rows=[
                LayoutRow(
                    columns=2,
                    title="Details",
                    items=[
                        LayoutItem(id="protected"),
                        LayoutItem(id="accessible", colspan=2),
                    ],
                )
            ]
        )

        self.assertTrue(
            _protected_layout_items_are_unchanged(
                existing_layout=existing,
                submitted_layout=submitted,
                protected_ids={"protected"},
            )
        )
