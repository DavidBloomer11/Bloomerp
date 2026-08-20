from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.test import RequestFactory
from django.urls import reverse

from bloomerp.dataviews.kanban import (
    KANBAN_UNAVAILABLE_COLUMN_VALUE,
    KanbanDataviewRenderer,
)
from bloomerp.forms.model_form import bloomerp_modelform_factory
from bloomerp.models import ApplicationField
from bloomerp.services.related_value_services import get_allowed_related_queryset
from bloomerp.tests.base import BaseBloomerpModelTestCase
from bloomerp.tests.utils.dynamic_models import create_test_models
from bloomerp.utils.api import generate_serializer
from bloomerp.widgets.foreign_field_widget import ForeignFieldWidget


class TestRelatedValueServices(BaseBloomerpModelTestCase):
    auto_create_customers = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.PipelineModel = create_test_models(
            app_label="bloomerp",
            model_defs={
                "RelatedValuePipeline": {
                    "name": models.CharField(max_length=100),
                    "type": models.CharField(max_length=20),
                    "__str__": lambda self: self.name,
                },
            },
            use_bloomerp_base=True,
        )["RelatedValuePipeline"]
        cls.StageModel = create_test_models(
            app_label="bloomerp",
            model_defs={
                "RelatedValueStage": {
                    "name": models.CharField(max_length=100),
                    "position": models.PositiveIntegerField(),
                    "pipeline": models.ForeignKey(
                        cls.PipelineModel,
                        on_delete=models.CASCADE,
                    ),
                    "__str__": lambda self: self.name,
                },
            },
            use_bloomerp_base=True,
        )["RelatedValueStage"]
        cls.StageModel._meta.ordering = ["position"]
        cls.LeadModel = create_test_models(
            app_label="bloomerp",
            model_defs={
                "RelatedValueLead": {
                    "name": models.CharField(max_length=100),
                    "pipeline_stage": models.ForeignKey(
                        cls.StageModel,
                        null=True,
                        blank=True,
                        on_delete=models.SET_NULL,
                        limit_choices_to={"pipeline__type": "lead"},
                    ),
                    "__str__": lambda self: self.name,
                },
            },
            use_bloomerp_base=True,
        )["RelatedValueLead"]
        cls._register_dynamic_model_routes(
            [cls.PipelineModel, cls.StageModel, cls.LeadModel]
        )

    def extendedSetup(self):
        self.lead_pipeline = self.PipelineModel.objects.create(
            name="Leads", type="lead"
        )
        self.opportunity_pipeline = self.PipelineModel.objects.create(
            name="Opportunities", type="opportunity"
        )
        self.later_stage = self.StageModel.objects.create(
            name="Qualified", position=2, pipeline=self.lead_pipeline
        )
        self.first_stage = self.StageModel.objects.create(
            name="New", position=1, pipeline=self.lead_pipeline
        )
        self.invalid_stage = self.StageModel.objects.create(
            name="Won", position=0, pipeline=self.opportunity_pipeline
        )
        self.stage_field = ApplicationField.get_by_field(
            self.LeadModel, "pipeline_stage"
        )

    def test_allowed_queryset_applies_limit_choices_and_default_ordering(self):
        """
        Use case: A foreign relation has application-level eligibility and ordering.
        Expected result: Only eligible rows are returned in related-model order.
        """
        # 1. Resolve the permission and limit_choices_to scoped queryset.
        queryset = get_allowed_related_queryset(self.stage_field, self.admin_user)

        # 2. Verify both the restriction and the related model's ordering.
        self.assertEqual(
            list(queryset.values_list("name", flat=True)),
            ["New", "Qualified"],
        )

    def test_kanban_includes_empty_ordered_columns_and_unavailable_group(self):
        """
        Use case: A board contains an eligible empty stage and a legacy invalid stage.
        Expected result: Ordered eligible destinations and a label-safe fallback render.
        """
        # 1. Create cards in one valid and one legacy-invalid relation.
        self.LeadModel.objects.create(name="Valid", pipeline_stage=self.first_stage)
        self.LeadModel.objects.create(name="Legacy", pipeline_stage=self.invalid_stage)

        # 2. Build groups through the shared eligibility resolver.
        groups = KanbanDataviewRenderer.build_groups(
            self.LeadModel.objects.all(),
            self.stage_field,
            user=self.admin_user,
        )

        # 3. Verify the empty eligible stage, ordering, and non-destination fallback.
        self.assertEqual(
            [group["label"] for group in groups],
            ["New", "Qualified", "Unavailable value"],
        )
        self.assertEqual(groups[1]["count"], 0)
        self.assertEqual(groups[-1]["value"], KANBAN_UNAVAILABLE_COLUMN_VALUE)
        self.assertFalse(groups[-1]["is_destination"])

    def test_form_and_generated_api_reject_ineligible_relation(self):
        """
        Use case: UI and API clients submit a relation excluded by limit_choices_to.
        Expected result: Both supported mutation paths reject it.
        """
        # 1. Submit the invalid stage through a Bloomerp model form.
        form_class = bloomerp_modelform_factory(
            self.LeadModel, fields=["name", "pipeline_stage"]
        )
        form = form_class(
            data={"name": "Form lead", "pipeline_stage": self.invalid_stage.pk},
            user=self.admin_user,
        )

        # 2. Verify model-form validation rejects the value.
        self.assertFalse(form.is_valid())
        self.assertIn("pipeline_stage", form.errors)

        # 3. Submit the same invalid relation through the generated serializer.
        request = RequestFactory().post("/")
        request.user = self.admin_user
        serializer = generate_serializer(self.LeadModel)(
            data={"name": "API lead", "pipeline_stage": self.invalid_stage.pk},
            context={"request": request},
        )

        # 4. Verify generated API validation agrees with the form.
        self.assertFalse(serializer.is_valid())
        self.assertIn("pipeline_stage", serializer.errors)

        # 5. Verify eligible values still pass both supported mutation paths.
        valid_form = form_class(
            data={"name": "Valid form lead", "pipeline_stage": self.first_stage.pk},
            user=self.admin_user,
        )
        valid_serializer = generate_serializer(self.LeadModel)(
            data={"name": "Valid API lead", "pipeline_stage": self.first_stage.pk},
            context={"request": request},
        )
        self.assertTrue(valid_form.is_valid(), valid_form.errors)
        self.assertTrue(valid_serializer.is_valid(), valid_serializer.errors)

    def test_update_and_permission_inaccessible_api_relation_are_rejected(self):
        """
        Use case: An update submits a restricted relation through form and API paths.
        Expected result: Limit and row-permission restrictions both reject the write.
        """
        # 1. Create an existing lead and prepare an authenticated API request.
        lead = self.LeadModel.objects.create(
            name="Existing", pipeline_stage=self.first_stage
        )
        request = RequestFactory().patch("/")
        request.user = self.admin_user

        # 2. Verify the update form rejects a limit_choices_to violation.
        form_class = bloomerp_modelform_factory(
            self.LeadModel, fields=["name", "pipeline_stage"]
        )
        form = form_class(
            data={"name": "Updated", "pipeline_stage": self.invalid_stage.pk},
            instance=lead,
            user=self.admin_user,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("pipeline_stage", form.errors)

        # 3. Restrict the otherwise eligible stage out of the permission queryset.
        with patch(
            "bloomerp.services.related_value_services.UserPolicyManager.get_queryset",
            return_value=self.StageModel.objects.none(),
        ):
            serializer = generate_serializer(self.LeadModel)(
                lead,
                data={"pipeline_stage": self.first_stage.pk},
                partial=True,
                context={"request": request},
            )
            is_valid = serializer.is_valid()

        # 4. Verify generated API validation rejects the inaccessible value.
        self.assertFalse(is_valid)
        self.assertIn("pipeline_stage", serializer.errors)

    def test_search_uses_source_field_and_standalone_widget_remains_supported(self):
        """
        Use case: Quick search originates from a constrained field or a standalone widget.
        Expected result: Field search is constrained and standalone rendering stays compatible.
        """
        # 1. Search with the source ApplicationField identifier.
        content_type = ContentType.objects.get_for_model(self.StageModel)
        url = reverse(
            "components_search_objects",
            kwargs={"content_type_id": content_type.pk},
        )
        self.client.force_login(self.admin_user)
        response = self.client.get(
            url,
            {"fk_search_results_query": "", "application_field_id": self.stage_field.pk},
        )

        # 2. Verify ineligible stages are absent from the server response.
        self.assertEqual(response.status_code, 200)
        response_text = response.content.decode()
        self.assertIn("New", response_text)
        self.assertNotIn("Won", response_text)

        # 3. Render a standalone widget without an ApplicationField.
        widget = ForeignFieldWidget(model=self.StageModel)
        html = widget.render("stage", "")

        # 4. Verify the legacy standalone mode remains identifiable and usable.
        self.assertIn('data-application-field-id=""', html)

    def test_row_permissions_further_reduce_related_values(self):
        """
        Use case: Row permissions hide an otherwise eligible relation.
        Expected result: The shared resolver returns the permissions intersection.
        """
        # 1. Replace the permission manager result with one visible eligible row.
        with patch(
            "bloomerp.services.related_value_services.UserPolicyManager.get_queryset",
            return_value=self.StageModel.objects.filter(pk=self.later_stage.pk),
        ):
            queryset = get_allowed_related_queryset(
                self.stage_field,
                self.normal_user,
            )

        # 2. Verify limit_choices_to and row visibility are intersected.
        self.assertEqual(list(queryset), [self.later_stage])

    def test_kanban_rejects_invalid_drop_destination(self):
        """
        Use case: A client posts a drag destination excluded by limit_choices_to.
        Expected result: The direct Kanban mutation endpoint rejects the move.
        """
        # 1. Create a lead in an eligible stage and authenticate as an administrator.
        lead = self.LeadModel.objects.create(
            name="Move me", pipeline_stage=self.first_stage
        )
        self.client.force_login(self.admin_user)
        content_type = ContentType.objects.get_for_model(self.LeadModel)

        # 2. Post an ineligible destination directly to the mutation endpoint.
        response = self.client.post(
            reverse(
                "components_kanban_move_card",
                kwargs={"content_type_id": content_type.pk},
            ),
            {
                "object_id": lead.pk,
                "group_by_field_id": self.stage_field.pk,
                "group_value": self.invalid_stage.pk,
            },
        )

        # 3. Verify the request failed and the persisted relation did not change.
        self.assertEqual(response.status_code, 400)
        lead.refresh_from_db()
        self.assertEqual(lead.pipeline_stage_id, self.first_stage.pk)

    def test_fifty_first_eligible_value_exceeds_kanban_limit(self):
        """
        Use case: A foreign grouping field has more than fifty eligible values.
        Expected result: The renderer selects the alternate-grouping state.
        """
        # 1. Add enough eligible stages to bring the total to fifty-one.
        self.StageModel.objects.bulk_create([
            self.StageModel(
                name=f"Stage {index}",
                position=index + 10,
                pipeline=self.lead_pipeline,
            )
            for index in range(49)
        ])

        # 2. Verify the threshold is applied after eligibility filtering.
        self.assertTrue(
            KanbanDataviewRenderer.has_too_many_related_columns(
                self.stage_field,
                self.admin_user,
            )
        )
