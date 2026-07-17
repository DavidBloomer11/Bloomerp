from django.db import models
from django.urls import reverse

from bloomerp.dataviews.pivot_table import PivotField, PivotTable
from bloomerp.models import ApplicationField
from bloomerp.services.user_services import get_user_list_view_preference
from bloomerp.tests.base import BaseBloomerpModelTestCase
from bloomerp.tests.utils.dynamic_models import create_test_models


class TestPivotDataView(BaseBloomerpModelTestCase):
    auto_create_customers = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.PivotRecordModel = create_test_models(
            app_label="bloomerp",
            model_defs={
                "PivotRecord": {
                    "region": models.CharField(max_length=100),
                    "team": models.CharField(max_length=100),
                    "quarter": models.CharField(max_length=20),
                    "active": models.BooleanField(default=True),
                    "amount": models.DecimalField(max_digits=10, decimal_places=2),
                    "__str__": lambda self: f"{self.region} {self.team}",
                },
            },
            use_bloomerp_base=True,
        )["PivotRecord"]
        cls._register_dynamic_model_routes([cls.PivotRecordModel])

    def _field(self, name: str) -> ApplicationField:
        return ApplicationField.get_by_field(self.PivotRecordModel, name)

    def extendedSetup(self):
        self.PivotRecordModel.objects.all().delete()

    def _configure_pivot(
        self,
        *,
        row_fields: list[str],
        column_fields: list[str] | None = None,
        value_field: str = "amount",
        aggregation: str = "sum",
        page_size: int = 10,
        totals_scope: str = "page",
    ):
        preference = get_user_list_view_preference(
            self.admin_user,
            self._field("region").content_type,
        )
        preference.view_type = "pivot_table"
        preference.options = {
            "pivot_table": {
                "row_field_ids": [self._field(name).id for name in row_fields],
                "column_field_ids": [self._field(name).id for name in (column_fields or [])],
                "value_field_id": self._field(value_field).id,
                "aggregation": aggregation,
                "show_row_totals": True,
                "show_column_totals": True,
                "totals_scope": totals_scope,
                "page_size": page_size,
            },
        }
        preference.save()
        return preference

    def _component_url(self) -> str:
        return reverse(
            "components_data_view",
            kwargs={"content_type_id": self._field("region").content_type_id},
        )

    def test_pivot_dataview_renders_nested_rows_and_column_headers(self):
        """
        Use case: A pivot has multiple row and column dimensions with numeric values.
        Expected result: Database sums render in expandable rows and spanning column headers.
        """
        # 1. Create records containing nested row and column combinations.
        self.PivotRecordModel.objects.bulk_create([
            self.PivotRecordModel(region="North", team="Alpha", quarter="Q1", active=True, amount=10),
            self.PivotRecordModel(region="North", team="Alpha", quarter="Q2", active=True, amount=20),
            self.PivotRecordModel(region="North", team="Beta", quarter="Q1", active=False, amount=5),
            self.PivotRecordModel(region="South", team="Gamma", quarter="Q1", active=True, amount=7),
        ])
        self._configure_pivot(
            row_fields=["region", "team"],
            column_fields=["quarter", "active"],
        )
        self.client.force_login(self.admin_user)

        # 2. Request the permission-filtered data-view component.
        response = self.client.get(self._component_url(), HTTP_HX_REQUEST="true")

        # 3. Verify hierarchical rows, two header levels, aggregates, and totals.
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'bloomerp-component="pivot-table"', html=False)
        self.assertContains(response, 'data-pivot-toggle="0"', html=False)
        self.assertContains(response, 'data-pivot-parent-id="0"', count=2, html=False)
        self.assertContains(response, 'colspan="2"', html=False)
        self.assertContains(response, "North", html=False)
        self.assertContains(response, "35", html=False)

    def test_pivot_dataview_paginates_top_level_rows_and_can_total_dataset(self):
        """
        Use case: A pivot has more top-level rows than its configured page size.
        Expected result: Pagination counts row groups while dataset totals include every filtered record.
        """
        # 1. Create twelve top-level row groups and request ten per page.
        self.PivotRecordModel.objects.bulk_create([
            self.PivotRecordModel(
                region=f"Region {index:02d}",
                team="Core",
                quarter="Q1",
                active=True,
                amount=index,
            )
            for index in range(1, 13)
        ])
        self._configure_pivot(
            row_fields=["region"],
            page_size=10,
            totals_scope="dataset",
        )
        self.client.force_login(self.admin_user)

        # 2. Request the first pivot page.
        response = self.client.get(self._component_url(), HTTP_HX_REQUEST="true")

        # 3. Verify ten row groups, table-style pagination, and the all-data total.
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-pivot-row-id=", count=10, html=False)
        self.assertContains(response, 'data-testid="data-view-pagination"', html=False)
        self.assertContains(response, "of 12 results", html=False)
        self.assertContains(response, "78", html=False)

    def test_reusable_pivot_dataclass_limits_text_values_to_count(self):
        """
        Use case: A caller requests a numeric aggregation for a text value field.
        Expected result: The reusable pivot safely uses database count aggregation instead.
        """
        # 1. Create two text values in one row group.
        self.PivotRecordModel.objects.bulk_create([
            self.PivotRecordModel(region="North", team="Alpha", quarter="Q1", active=True, amount=10),
            self.PivotRecordModel(region="North", team="Beta", quarter="Q1", active=True, amount=20),
        ])
        region_field = self.PivotRecordModel._meta.get_field("region")
        team_field = self.PivotRecordModel._meta.get_field("team")
        pivot = PivotTable(
            queryset=self.PivotRecordModel.objects.all(),
            row_fields=[PivotField("region", "Region", region_field)],
            column_fields=[],
            value_field=PivotField("team", "Team", team_field),
            aggregation="sum",
        )

        # 2. Build the pivot from its top-level row value.
        result = pivot.build(["North"])

        # 3. Verify the effective aggregation and database-computed result.
        self.assertEqual(result.effective_aggregation, "count")
        self.assertEqual(result.rows[0].cells, [2])
        self.assertEqual(result.rows[0].total, 2)

    def test_pivot_options_use_application_field_multi_select_widgets(self):
        """
        Use case: A user opens the pivot display configuration.
        Expected result: Rows and columns use the reusable many-to-many foreign-field widget.
        """
        # 1. Configure the pivot view and sign in.
        self._configure_pivot(row_fields=["region"])
        self.client.force_login(self.admin_user)
        # 2. Request the data view, which contains its display options component.
        response = self.client.get(self._component_url(), HTTP_HX_REQUEST="true")

        # 3. Verify both dimension selectors render in M2M mode.
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-is-m2m="true"', count=2, html=False)
        self.assertContains(response, "Aggregation", html=False)

        # 4. Submit ordered row and column selections through the preference endpoint.
        preference_url = reverse(
            "components_change_data_view_preference",
            kwargs={"content_type_id": self._field("region").content_type_id},
        )
        post_response = self.client.post(
            preference_url,
            data={
                "dataview_options_view_type": "pivot_table",
                "row_field_ids": [str(self._field("region").id), str(self._field("team").id)],
                "column_field_ids": [str(self._field("quarter").id)],
                "value_field_id": str(self._field("amount").id),
                "aggregation": "sum",
                "show_row_totals": "on",
                "show_column_totals": "on",
                "totals_scope": "dataset",
                "page_size": "25",
            },
            HTTP_HX_REQUEST="true",
        )

        # 5. Verify the M2M widget values are validated and persisted as field IDs.
        self.assertEqual(post_response.status_code, 200)
        preference = get_user_list_view_preference(
            self.admin_user,
            self._field("region").content_type,
        )
        self.assertEqual(
            preference.options["pivot_table"]["row_field_ids"],
            [self._field("region").id, self._field("team").id],
        )
