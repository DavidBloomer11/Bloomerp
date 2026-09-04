from django.http import HttpResponse
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from bloomerp.router import BloomerpRoute, BloomerpRouteRegistry, RouteType, ViewType
from bloomerp.tests.base import BloomerpChannelTestCase


def http_view(request):
    return HttpResponse("ok")


class EchoConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive_json(self, content, **kwargs):
        await self.send_json(content)


class BloomerpWebsocketRouterTests(BloomerpChannelTestCase):
    def test_route_constructor_remains_backwards_compatible(self):
        route = BloomerpRoute(
            "http/",
            RouteType.APP,
            "HTTP",
            "http",
            ViewType.FUNCTION,
            http_view,
        )

        self.assertIsNone(route.re_path)

    def test_path_websocket_route_builds_a_channels_pattern(self):
        registry = BloomerpRouteRegistry()
        registry.register(path="ws/echo/", route_type="websocket")(EchoConsumer)

        patterns = registry.create_websocket_url_patterns()

        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0].name, "echoconsumer")
        self.assertEqual(registry.routes[0].route_type, RouteType.WEBSOCKET)

    async def test_path_websocket_route_connects_and_exchanges_json(self):
        registry = BloomerpRouteRegistry()
        registry.register(path="ws/echo/", route_type="websocket")(EchoConsumer)

        communicator = self.websocket_communicator(registry, "/ws/echo/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.send_json_to({"message": "hello"})
        self.assertEqual(await communicator.receive_json_from(), {"message": "hello"})
        await communicator.disconnect()

    async def test_regex_route_is_preserved_and_connects(self):
        registry = BloomerpRouteRegistry()
        expression = r"^ws/rooms/(?P<room_id>\d+)/$"
        registry.register(re_path=expression, route_type="websocket")(EchoConsumer)

        route = registry.routes[0]
        pattern = registry.create_websocket_url_patterns()[0]

        self.assertEqual(route.re_path, expression)
        self.assertEqual(pattern.pattern.regex.pattern, expression)
        communicator = self.websocket_communicator(registry, "/ws/rooms/42/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    def test_path_and_re_path_are_mutually_exclusive(self):
        registry = BloomerpRouteRegistry()

        with self.assertRaisesMessage(ValueError, "Only one of 'path' or 're_path'"):
            registry.register(
                path="ws/echo/",
                re_path=r"^ws/echo/$",
                route_type="websocket",
            )(EchoConsumer)

    def test_websocket_routes_are_excluded_from_http_patterns(self):
        registry = BloomerpRouteRegistry()
        registry.register(path="http/", name="http")(http_view)
        registry.register(path="ws/echo/", route_type="websocket")(EchoConsumer)

        patterns = registry.create_url_patterns()

        self.assertEqual([pattern.name for pattern in patterns], ["http"])
