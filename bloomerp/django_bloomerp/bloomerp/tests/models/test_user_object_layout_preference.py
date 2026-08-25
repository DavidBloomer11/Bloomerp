from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType

from bloomerp.models.application_field import ApplicationField
from bloomerp.models.definition import (
    BloomerpModelConfig,
    DetailViewSettings,
    FieldLayout,
    LayoutItem,
    LayoutRow,
)
from bloomerp.models.users.user_object_layout_preference import (
    UserObjectLayoutPreference,
)
from bloomerp.tests.base import BaseBloomerpModelTestCase


class UserObjectLayoutPreferenceDefaultTests(BaseBloomerpModelTestCase):
    def setUp(self):
        super().setUp()
        self.content_type = ContentType.objects.get_for_model(self.CustomerModel)

    def test_create_default_for_user_materializes_all_layouts_and_selects_default(self):
        settings = DetailViewSettings(
            layout=[
                FieldLayout(
                    name="Compact",
                    is_default=False,
                    rows=[
                        LayoutRow(
                            columns=1,
                            items=[LayoutItem(id="first_name")],
                        )
                    ],
                ),
                FieldLayout(
                    name="Detailed",
                    rows=[
                        LayoutRow(
                            columns=1,
                            items=[LayoutItem(id="last_name")],
                        )
                    ],
                ),
            ]
        )

        with patch.object(
            self.CustomerModel,
            "bloomerp_config",
            BloomerpModelConfig(detail_view_settings=settings),
            create=True,
        ):
            selected = UserObjectLayoutPreference.create_default_for_user(
                self.admin_user,
                content_type_id=self.content_type.pk,
            )

        preferences = list(
            UserObjectLayoutPreference.objects.filter(
                user=self.admin_user,
                content_type=self.content_type,
            ).order_by("pk")
        )
        self.assertEqual(
            [preference.name for preference in preferences],
            ["Compact", "Detailed"],
        )
        self.assertFalse(preferences[0].selected)
        self.assertTrue(preferences[1].selected)
        self.assertEqual(selected, preferences[1])
        first_name = ApplicationField.get_by_field(self.CustomerModel, "first_name")
        last_name = ApplicationField.get_by_field(self.CustomerModel, "last_name")
        self.assertEqual(
            preferences[0].layout["rows"][0]["items"][0]["id"],
            first_name.pk,
        )
        self.assertEqual(
            preferences[1].layout["rows"][0]["items"][0]["id"],
            last_name.pk,
        )
