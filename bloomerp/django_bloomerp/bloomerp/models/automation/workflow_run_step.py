from django.db import models

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
        help_text="The workflow run that this step belongs to.",
    )
    sequence = models.PositiveIntegerField(
        help_text="The sequence number of this step within the workflow run.",
    )
    action_id = models.CharField(
        max_length=255,
        help_text="The identifier of the action being executed in this step."
    )
    status = models.CharField(
        max_length=20,
        choices=WorkflowRunStepStatus.choices,
        default=WorkflowRunStepStatus.COMPLETED,
        help_text="The status of this workflow run step.",
    )
    state = models.JSONField(
        null=True,
        blank=True,
        help_text="Serializable workflow execution state captured after this step.",
    )
    output_file = models.FileField(
        upload_to="workflow_run_outputs/",
        null=True,
        blank=True,
        help_text="Serialized output produced by this workflow node execution.",
    )
    node = models.ForeignKey(
        to="WorkflowNode",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text="Reference to node object"
    )
    
