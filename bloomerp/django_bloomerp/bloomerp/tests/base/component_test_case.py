from bloomerp.tests.base.core_test_case import BaseBloomerpTestCaseWithModels
from bloomerp.tests.base.request_test_case_mixin import RequestTestCaseMixin


class BloomerpComponentTestCase(RequestTestCaseMixin, BaseBloomerpTestCaseWithModels):
    """Base class for declarative tests of routed Bloomerp components."""

    view_name: str | None = None
