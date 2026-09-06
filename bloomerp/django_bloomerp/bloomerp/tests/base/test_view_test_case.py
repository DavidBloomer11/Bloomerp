from django.test import SimpleTestCase

from bloomerp.models.forms.form import Form
from bloomerp.models.workspaces.workspace import Workspace
from bloomerp.tests.base import view_test_case as view_test_cases


class SubmitFormRouteTestCase(view_test_cases.BloomerpDetailViewTestCase):
    __test__ = False
    view_name = "submit"
    model = Form

    def get_request_setups(self):
        return []


class CreateWorkspaceRouteTestCase(view_test_cases.BloomerpModelViewTestCase):
    __test__ = False
    view_name = "add"
    model = Workspace

    def get_request_setups(self):
        return []


class ModuleHomeRouteTestCase(view_test_cases.BloomerpModuleViewTestCase):
    __test__ = False
    view_name = "{module}"
    module = "finance"

    def get_request_setups(self):
        return []


class SpecializedViewTestCaseTests(SimpleTestCase):
    def test_detail_route_uses_model_and_preserves_view_kwargs(self):
        """
        Use case: A detail-view test selects a model and supplies path arguments.
        Expected result: The base resolves the concrete URL and passes kwargs through.
        """
        # 1. Configure the declarative detail-route test.
        test_case = SubmitFormRouteTestCase()

        # 2. Resolve the model-specific route registration.
        route = test_case.get_route()
        self.assertIs(route.model, Form)
        self.assertEqual(route.url_name, "forms_detail_submit")

        # 3. Pass the scenario's primary key through normal view kwargs.
        self.assertEqual(
            test_case.get_endpoint("submit", {"pk": 123}),
            "/misc/forms/123/submit/",
        )

    def test_model_route_resolves_from_its_single_model(self):
        """
        Use case: A model-view test declares a stable name and concrete model.
        Expected result: The matching expanded model route is selected.
        """
        # 1. Resolve the route from the registration name and model.
        route = CreateWorkspaceRouteTestCase().get_route()

        # 2. Confirm it is the Workspace-specific generated URL name.
        self.assertIs(route.model, Workspace)
        self.assertEqual(route.url_name, "workspaces_add")

    def test_module_route_resolves_after_selecting_a_module(self):
        """
        Use case: One module route expands into registrations for many modules.
        Expected result: A module ID selects exactly one concrete route.
        """
        # 1. Resolve the shared module-home registration for Finance.
        route = ModuleHomeRouteTestCase().get_route()

        # 2. Confirm the selected module and final URL name.
        self.assertEqual(route.module.id, "finance")
        self.assertEqual(route.url_name, "finance_module_finance")
