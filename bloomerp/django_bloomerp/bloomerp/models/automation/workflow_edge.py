from django.utils.translation import gettext_lazy as _
from django.db import models
from bloomerp.models.automation.workflow import Workflow

class WorkflowEdge(
    models.Model):
    """
    An edge connects two nodes in a workflow.
    It defines the flow of execution from one node to another.
    """
    class Meta:
        db_table = "bloomerp_workflow_edge"
        verbose_name = _("Workflow Edge")
        verbose_name_plural = _("Workflow Edges")
    
    name = models.CharField(
        max_length=1000,
        help_text="A descriptive name for the edge.",
        null=True,
        blank=True,
        verbose_name=_("Name"),
    )

    from_node = models.ForeignKey(
        'WorkflowNode',
        on_delete=models.CASCADE,
        related_name="outgoing_edges",
        help_text="The node where this edge starts.",
        verbose_name=_("From Node"),
    )
    
    to_node = models.ForeignKey(
        'WorkflowNode',
        on_delete=models.CASCADE,
        related_name="incoming_edges",
        help_text="The node where this edge ends.",
        verbose_name=_("To Node"),
    )