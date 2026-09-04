from .router import router


websocket_urlpatterns = router.create_websocket_url_patterns()
