from django.db import models
from django.utils.translation import gettext_lazy as _
from bloomerp.models.definition import BloomerpModelConfig
from bloomerp.models.mixins.timestamp_model_mixin import TimestampModelMixin

class WorkflowRunStepStatus(models.TextChoices):
    PAUSED = "PAUSED", "Paused"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


class WorkflowRunStep(TimestampModelMixin, models.Model):
    class Meta:
        db_table = "bloomerp_workflow_run_step"
        verbose_name = "Workflow Run Step"
        verbose_name_plural = "Workflow Run Steps"
    
    bloomerp_config = BloomerpModelConfig(
        module="automation",
        record_activity_log=False
    )
    
    workflow_run = models.ForeignKey(
        "WorkflowRun",
        on_delete=models.CASCADE,
        related_name="steps",
        verbose_name=_("Workflow Run"),
        help_text=_("The workflow run that this step belongs to."),
    )
    sequence = models.PositiveIntegerField(
        help_text=_("The sequence number of this step within the workflow run."),
        verbose_name=_("Sequence"),
    )
    action_id = models.CharField(
        max_length=255,
        help_text=_("The identifier of the action being executed in this step."),
        verbose_name=_("Action ID"),
    )
    status = models.CharField(
        max_length=20,
        choices=WorkflowRunStepStatus.choices,
        default=WorkflowRunStepStatus.COMPLETED,
        help_text=_("The status of this workflow run step."),
        verbose_name=_("Status"),
    )
    state = models.JSONField(
        null=True,
        blank=True,
        help_text=_("Serializable workflow execution state captured after this step."),
        verbose_name=_("State"),
    )
    output_file = models.FileField(
        upload_to="workflow_run_outputs/",
        null=True,
        blank=True,
        help_text=_("Serialized output produced by this workflow node execution."),
        verbose_name=_("Output File"),
    )
    node = models.ForeignKey(
        to="WorkflowNode",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text=_("Reference to node object"),
        verbose_name=_("Node"),
    )
    
