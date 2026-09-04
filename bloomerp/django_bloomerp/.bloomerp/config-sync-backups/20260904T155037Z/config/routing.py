from bloomerp.routing import websocket_urlpatterns as bloomerp_websocket_urlpatterns

from config.project_routing import websocket_urlpatterns as project_websocket_urlpatterns


websocket_urlpatterns = [
    *bloomerp_websocket_urlpatterns,
    *project_websocket_urlpatterns,
]
