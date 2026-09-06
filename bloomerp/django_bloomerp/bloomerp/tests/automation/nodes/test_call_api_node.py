from bloomerp.automation.actions.call_api import CallApiExecutor
from bloomerp.tests.base import (
    BloomerpWorkflowNodeTestCase,
    WorkflowSimulation,
)


class TestCallApiNode(BloomerpWorkflowNodeTestCase):
    node_id = 'CALL_API'
    executor_class = CallApiExecutor
    
    def get_simulations(self) -> list[WorkflowSimulation]:
        return []
