from bloomerp.tests.base.component_test_case import BloomerpComponentTestCase
from bloomerp.tests.base.core_test_case import (
    BaseBloomerpTestCaseWithModels,
    BloomerpChannelTestCase,
)
from bloomerp.tests.base.e2e_test_case import BloomerpE2ETestCase
from bloomerp.tests.base.dataview_test_case import BloomerpDataviewTestCase
from bloomerp.tests.base.model_field_test_case import BloomerpModelFieldTestCase
from bloomerp.tests.base.model_test_case import (
    BaseBloomerpModelTestCase,
    BloomerpModelTestCase,
)
from bloomerp.tests.base.request_test_case_mixin import (
    ExpectedResult,
    RequestSetup,
    RequestTestCaseMixin,
    ResponseValidator,
)
from bloomerp.tests.base.view_test_case import (
    BloomerpDetailViewTestCase,
    BloomerpModelViewTestCase,
    BloomerpModuleViewTestCase,
    BloomerpViewTestCase,
)
from bloomerp.tests.base.widget_test_case import BloomerpWidgetTestCase
from bloomerp.tests.base.workflow_node_test_case import (
    BloomerpWorkflowNodeTestCase,
    WorkflowSimulation,
)


# Backwards-compatible names used by existing projects.
BaseBloomerpComponentTest = BloomerpComponentTestCase
BaseBloomerpWidgetTestCase = BloomerpWidgetTestCase

__all__ = [
    "BaseBloomerpComponentTest",
    "BaseBloomerpModelTestCase",
    "BaseBloomerpTestCaseWithModels",
    "BaseBloomerpWidgetTestCase",
    "BloomerpChannelTestCase",
    "BloomerpComponentTestCase",
    "BloomerpDataviewTestCase",
    "BloomerpDetailViewTestCase",
    "BloomerpE2ETestCase",
    "BloomerpModelFieldTestCase",
    "BloomerpModelTestCase",
    "BloomerpModelViewTestCase",
    "BloomerpModuleViewTestCase",
    "BloomerpViewTestCase",
    "BloomerpWidgetTestCase",
    "BloomerpWorkflowNodeTestCase",
    "ExpectedResult",
    "RequestSetup",
    "RequestTestCaseMixin",
    "ResponseValidator",
    "WorkflowSimulation",
]
