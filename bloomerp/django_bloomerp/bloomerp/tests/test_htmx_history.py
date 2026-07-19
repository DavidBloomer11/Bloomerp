from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, SimpleTestCase

from bloomerp.middleware import HTMXVaryMiddleware


class HTMXVaryMiddlewareTests(SimpleTestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_response_varies_by_headers_that_change_htmx_rendering(self) -> None:
        """
        Use case: A URL is requested first by HTMX and later by normal browser navigation.
        Expected result: Caches keep full-page, history-restore, and target-specific responses separate.
        """
        # 1. Pass a response through the global HTMX cache middleware.
        middleware = HTMXVaryMiddleware(lambda request: HttpResponse("response"))
        response = middleware(self.factory.get("/objects/"))

        # 2. Verify every request header that changes the rendered response is declared.
        vary_headers = {header.strip().lower() for header in response["Vary"].split(",")}
        self.assertEqual(
            vary_headers,
            {"hx-request", "hx-history-restore-request", "hx-target"},
        )

    def test_response_preserves_existing_vary_headers(self) -> None:
        """
        Use case: Another middleware already varies a response by cookies.
        Expected result: The HTMX cache headers are added without discarding the existing value.
        """
        # 1. Create a response that already has a Vary header.
        def get_response(request: HttpRequest) -> HttpResponse:
            response = HttpResponse("response")
            response["Vary"] = "Cookie"
            return response

        # 2. Pass the response through the global HTMX cache middleware.
        response = HTMXVaryMiddleware(get_response)(self.factory.get("/objects/"))

        # 3. Verify the existing and HTMX-specific variants are all retained.
        vary_headers = {header.strip().lower() for header in response["Vary"].split(",")}
        self.assertEqual(
            vary_headers,
            {"cookie", "hx-request", "hx-history-restore-request", "hx-target"},
        )
