from django.http import HttpRequest

from bloomerp.workspaces.base import BaseTileRenderer
from bloomerp.workspaces.utils import UserParameterResolver


class LinksTileRenderer(BaseTileRenderer):
    template_name = "cotton/features/workspaces/tiles/link.html"

    @classmethod
    def render(cls, config, request: HttpRequest):
        rendered_config = config.model_copy(deep=True)
        resolver = UserParameterResolver(request.user)
        for link in rendered_config.links:
            link.url = resolver.resolve(link.url)

        return cls.render_to_string(
            {
                "config": rendered_config
            }
        )
