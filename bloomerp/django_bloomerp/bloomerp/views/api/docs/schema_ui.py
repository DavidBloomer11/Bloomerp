from drf_spectacular.views import SpectacularRedocView
from bloomerp.router import router

@router.register(
    path="schema/ui/",
    route_type="api",
    url_name="schema_ui",
)
class BloomerpRedocSchemaView(SpectacularRedocView):
    """
    Custom Redoc schema view for the Bloomerp API.
    """
    url_name='schema'
