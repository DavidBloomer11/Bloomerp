from django.db.models import Model
from django.urls import reverse

from bloomerp.modules.definition import module_registry
from bloomerp.router import RouteType, router
from bloomerp.tests.base.core_test_case import BaseBloomerpTestCaseWithModels
from bloomerp.tests.base.request_test_case_mixin import RequestTestCaseMixin


class BloomerpViewTestCase(RequestTestCaseMixin, BaseBloomerpTestCaseWithModels):
    """Base class for declarative tests of routed Bloomerp views."""

    view_name: str | None = None
    route_type = RouteType.APP
    model: type[Model] | None = None
    module = None

    def get_test_case_module(self):
        """Resolve a configured module object or registry ID."""
        if isinstance(self.module, str):
            module = module_registry.get(self.module)
            if module is None:
                raise AssertionError(
                    f"Module {self.module!r} is not registered"
                )
            return module
        return self.module

    def get_route(self, view_name: str | None = None):
        """Resolve the concrete route for this test's model/module context."""
        selected_view_name = view_name or self.view_name
        selected_module = self.get_test_case_module()
        candidates = [
            route
            for route in router.get_routes_by_type(self.route_type)
            if selected_view_name in {route.base_url_name, route.url_name}
            and (
                self.model is None
                or route.model is self.model
            )
            and (selected_module is None or route.module == selected_module)
        ]
        if len(candidates) != 1:
            raise AssertionError(
                f"Expected one {self.route_type.value!r} route named "
                f"{selected_view_name!r}, found {len(candidates)}."
            )
        return candidates[0]

    def get_endpoint(self, view_name: str, kwargs: dict | None) -> str:
        """Reverse the concrete route selected by the test context."""
        route = self.get_route(view_name)
        return reverse(viewname=route.url_name, kwargs=kwargs)

    def test_route_registration(self) -> None:
        """
        Use case: A generated view test selects a route context.
        Expected result: Exactly one matching concrete route is registered.
        """
        # 1. Do not execute the reusable base class itself.
        if self.view_name is None:
            return

        # 2. Require the context needed by specialized route families.
        if self.route_type in {RouteType.MODEL, RouteType.DETAIL}:
            if self.model is None:
                self.skipTest("Set model to test this route")
        if self.route_type == RouteType.MODULE and self.module is None:
            self.skipTest("Set module to test this route")

        # 3. Resolve and validate the selected route registration.
        route = self.get_route()
        self.assertEqual(route.route_type, self.route_type)
        if self.model is not None:
            self.assertIs(route.model, self.model)
        if self.module is not None:
            self.assertEqual(route.module, self.get_test_case_module())


class BloomerpModelViewTestCase(BloomerpViewTestCase):
    """Base class for model-level routes."""

    route_type = RouteType.MODEL


class BloomerpDetailViewTestCase(BloomerpViewTestCase):
    """Base class for object-detail routes."""

    route_type = RouteType.DETAIL


class BloomerpModuleViewTestCase(BloomerpViewTestCase):
    """Base class for module-level routes."""

    route_type = RouteType.MODULE
