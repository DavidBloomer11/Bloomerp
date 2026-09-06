from dataclasses import dataclass, field
from typing import Any, Callable

from django.test import TestCase

from bloomerp.automation.registry import WORKFLOW_NODE_REGISTRY, WorkflowNodeDefinition
from bloomerp.automation.base_executor import BaseExecutor
from bloomerp.models.automation.workflow import Workflow
from bloomerp.models.automation.workflow_node import WorkflowNode


EXPECTED_OUTPUT_UNSET = object()


@dataclass
class WorkflowSimulation:
    """One direct execution scenario for a registered workflow node."""

    nodes: list[WorkflowNode] = field(default_factory=list)
    trigger_data: dict = field(default_factory=dict)
    expected_output: Any = EXPECTED_OUTPUT_UNSET
    output_validator: Callable[[Any], bool] | None = None
    name: str | None = None



class BloomerpWorkflowNodeTestCase(TestCase):
    """Base class for registration and execution tests of a workflow node."""

    node_id: str | None = None
    executor_class: type[BaseExecutor] | None = None

    def create_workflow(self) -> Workflow:
        """Create the workflow used by node simulations."""
        return Workflow.objects.create(name="Test Workflow")

    def get_node_definition(self, node_id: str | None = None) -> WorkflowNodeDefinition:
        """Return a registered node definition or fail with a useful message."""
        selected_node_id = node_id or self.node_id
        definition = WORKFLOW_NODE_REGISTRY.get(selected_node_id)
        if definition is None:
            raise AssertionError(f"Workflow node {selected_node_id!r} is not registered")
        return definition

    def add_node(
        self,
        node_id: str | None = None,
        *,
        parameters: dict | None = None,
        workflow: Workflow | None = None,
    ) -> WorkflowNode:
        """Add a registered node to the current simulation workflow."""
        definition = self.get_node_definition(node_id)
        selected_workflow = workflow or self.workflow
        return WorkflowNode.objects.create(
            workflow=selected_workflow,
            type=definition.type,
            sub_type=definition.id,
            parameters=parameters or {},
        )

    def add_trigger(self, **kwargs) -> WorkflowNode:
        """Add the configured node and assert that it is a trigger."""
        definition = self.get_node_definition()
        if definition.type != "TRIGGER":
            raise AssertionError(f"Workflow node {definition.id!r} is not a trigger")
        return self.add_node(**kwargs)

    def get_simulations(self) -> list[WorkflowSimulation]:
        """Return direct execution scenarios for the configured node."""
        return []

    def test_workflow_node_simulations(self) -> None:
        """
        Use case: A registered workflow node declares execution simulations.
        Expected result: The node exists, can be persisted, and produces valid output.
        """
        # 1. Do not execute the reusable base class itself.
        if self.node_id is None:
            return

        # 2. Create the shared workflow before subclasses build simulations.
        definition = self.get_node_definition()
        if self.executor_class is not None:
            self.assertIs(definition.executor_cls, self.executor_class)
        self.workflow = self.create_workflow()

        # 3. Execute the configured node once for every simulation.
        for index, simulation in enumerate(self.get_simulations(), start=1):
            with self.subTest(name=simulation.name or f"simulation {index}"):
                nodes = simulation.nodes or [self.add_node()]
                node = next(
                    (item for item in nodes if item.sub_type == self.node_id), None
                )
                self.assertIsNotNone(
                    node,
                    f"Simulation does not contain workflow node {self.node_id!r}",
                )
                output = node.execute(simulation.trigger_data)

                if simulation.expected_output is not EXPECTED_OUTPUT_UNSET:
                    self.assertEqual(output, simulation.expected_output)
                if simulation.output_validator is not None:
                    self.assertTrue(simulation.output_validator(output))
