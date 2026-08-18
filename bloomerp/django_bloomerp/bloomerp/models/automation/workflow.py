from typing import TYPE_CHECKING
from django.db import models
from django.urls import reverse
from bloomerp.models.base_bloomerp_model import FieldLayout, LayoutItem, LayoutRow
from bloomerp.models.definition import BloomerpModelConfig, DetailViewSettings, ObjectModalAction
from bloomerp.models.mixins.absolute_url_model_mixin import AbsoluteUrlModelMixin
from bloomerp.models.mixins.user_stamp_model_mixin import UserStampModelMixin
from bloomerp.models.mixins import TimestampModelMixin
from django.utils.translation import gettext_lazy as _
from bloomerp.automation.defintion import WorkflowNodeType

if TYPE_CHECKING:
    from bloomerp.models.automation.workflow_node import WorkflowNode
    from bloomerp.models.automation.workflow_edge import WorkflowEdge


class Workflow(
    UserStampModelMixin,
    TimestampModelMixin,
    AbsoluteUrlModelMixin,
    models.Model
    ):
    """
    A workflow is a model for automation.
    Each workflow can have differnent nodes.
    """
    class Meta:
        db_table = "bloomerp_workflow"
        verbose_name = _("Workflow")
        verbose_name_plural = _("Workflows")
    
    bloomerp_config = BloomerpModelConfig(
        module="automation",
        layout=FieldLayout(
            rows=[
                LayoutRow(
                    title="Details",
                    columns=2,
                    items=[
                        LayoutItem(id="name")
                    ]
                ),
                LayoutRow(
                    title="Configuration",
                    columns=2,
                    items=[
                        LayoutItem(id="active"),
                        LayoutItem(id="run_asynchronously"),
                        LayoutItem(id="enable_logging"),
                    ]
                ),
            ]
        ),
        object_actions=[
            ObjectModalAction(
                id="run_workflow",
                label="Run workflow",
                endpoint=lambda obj: reverse("components_automation_run_workflow", kwargs={"workflow_id" : obj.id}),
                modal_title="Run workflow"
            ),
            
        ],
        create_redirect_url_func=lambda x: reverse(
            "workflows_detail_builder",
            kwargs={"pk":x.pk}
        ),
        detail_view_settings=DetailViewSettings(
            skip_views=["document_templates", "files"]
        )
    )
    
    name = models.CharField(
        max_length=255,
        help_text=_("The name of the workflow."),
        verbose_name=_("Name")
        )
    run_asynchronously = models.BooleanField(
        default=False,
        help_text=_("Whether runs asynchronously"),
        verbose_name=_("Run Asynchronously")
    )
    active = models.BooleanField(
        default=True,
        help_text=_("Whether the workflow is active or not"),
        verbose_name=_("Active")
    )
    enable_logging = models.BooleanField(
        default=False,
        help_text=_("Whether to enable logging for this workflow. Disabling logging may improve performance but will result in no detailed execution history being stored."),
        verbose_name=_("Enable Logging")
    )
    
    def get_trigger(self) -> "WorkflowNode |None":
        """Returns the trigger of a workflow.

        Returns:
            WorkflowNode: the triggering node of this workflow
        """
        nodes: models.QuerySet["WorkflowNode"] = self.nodes.all()

        return nodes.filter(
            type=WorkflowNodeType.TRIGGER.value.id
        ).first()

    def __str__(self) -> str:
        return self.name    
        
    def contains_node(self, node:"WorkflowNode") -> bool:
        """Checks whether a workflow contains a node object

        Args:
            node (WorkflowNode): the node to check for

        Returns:
            bool: whether it contains the node
        """
        return self.nodes.filter(id=node.id).exists()
    
    def connect_nodes(self, from_node:"WorkflowNode", to_node:"WorkflowNode") -> "WorkflowEdge":
        """Adds a connection between two nodes.

        Args:
            input_node (WorkflowNode): the input node
            output_node (WorkflowNode): the output node 
        
        Returns:
            edge : the edge between the two nodes
        """
        from bloomerp.models.automation.workflow_edge import WorkflowEdge
        if not self.contains_node(from_node) or not self.contains_node(to_node):
            raise ValueError("Node not in workflow")
        
        return WorkflowEdge.objects.create(
            from_node=from_node,
            to_node=to_node
        )
        
    