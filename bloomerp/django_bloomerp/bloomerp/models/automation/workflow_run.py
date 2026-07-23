from datetime import datetime

from django.db import models
from django.urls import reverse
from bloomerp.models.automation import workflow
from bloomerp.models.automation.workflow_run_step import WorkflowRunStep, WorkflowRunStepStatus
from bloomerp.models.base_bloomerp_model import FieldLayout, LayoutItem, LayoutRow
from bloomerp.models.definition import BloomerpModelConfig, DetailViewSettings, ObjectModalAction
from bloomerp.models.mixins.absolute_url_model_mixin import AbsoluteUrlModelMixin
from bloomerp.models.mixins.user_stamp_model_mixin import UserStampModelMixin
from bloomerp.models.mixins import TimestampModelMixin
from django.utils.translation import gettext_lazy as _
from django.db.models import Count
from django.db.models import Max, Min
from django.db.models import Case, IntegerField, Value, When

class WorkflowRun(
    TimestampModelMixin,
    AbsoluteUrlModelMixin,
    models.Model):
    
    class Meta:
        db_table = "bloomerp_workflow_run"
        verbose_name = _("Workflow Run")
        verbose_name_plural = _("Workflow Runs")
    
    bloomerp_config = BloomerpModelConfig(
        module="automation",
        layout=FieldLayout(
            rows=[
                LayoutRow(
                    columns=2,
                    items=[
                        LayoutItem(id="workflow"),
                        LayoutItem(id="datetime_created"),
                        LayoutItem(id="steps", colspan=2, config={
                            "inline_fields" : [
                                "sequence",
                                "action_id",
                                "status",
                                "datetime_created"
                            ]
                        })
                    ]
                )
            ]
        ),
        detail_view_settings=DetailViewSettings(
            skip_views=["files", "document_templates"]
        ),
        object_actions=[
            ObjectModalAction(
                id="approve_step",
                label="Approve",
                endpoint=lambda obj: reverse(
                    "components_automation_approve_workflow_continuation",
                    kwargs={
                        "workflow_run_id" : obj.id
                    }
                ),
                should_render_func=lambda req, obj: obj.status == WorkflowRunStepStatus.PAUSED,
                modal_title="Approve workflow continuation"
            )
        ],
        record_activity_log=False
    )
    
    workflow = models.ForeignKey(
        workflow.Workflow,
        on_delete=models.CASCADE,
        help_text=_("The workflow associated with this run."),
        editable=False,
        related_name="runs",
    )
    
    def __str__(self):
        return f"{self.workflow.name} - {self.datetime_created}"


    @property
    def execution_time(self) -> datetime:
        """Returns the execution time of the workflow

        Returns:
            datetime: the time it took for the workflow to run
        """
        timestamps = self.steps.aggregate(
            started_at=Min("datetime_created"),
            finished_at=Max("datetime_created"),
        )

        return (
            timestamps["finished_at"] - timestamps["started_at"]
            if timestamps["started_at"] and timestamps["finished_at"]
            else None
        )
            
    @property
    def number_of_steps(self):
        """Returns there were in the workflow
        """
        return self.steps.all().count()
    
    @property
    def status(self) -> str:
        """Returns the status of the workflow run step

        Returns:
            str: the status
        """
        status = (
            self.steps
            .filter(
                status__in=[
                    WorkflowRunStepStatus.PAUSED,
                    WorkflowRunStepStatus.FAILED,
                    WorkflowRunStepStatus.CANCELLED,
                ]
            )
            .annotate(
                priority=Case(
                    When(
                        status=WorkflowRunStepStatus.PAUSED,
                        then=Value(1),
                    ),
                    When(
                        status=WorkflowRunStepStatus.FAILED,
                        then=Value(2),
                    ),
                    When(
                        status=WorkflowRunStepStatus.CANCELLED,
                        then=Value(3),
                    ),
                    output_field=IntegerField(),
                )
            )
            .order_by("priority")
            .values_list("status", flat=True)
            .first()
        )

        return status or WorkflowRunStepStatus.COMPLETED
        