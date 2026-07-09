import logging

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Model
from django.utils.decorators import classonlymethod

from bloomerp.api.base import BloomerpModelViewSet
from bloomerp.models.application_field import ApplicationField
from bloomerp.models.definition import get_model_config
from bloomerp.serializers.model_serializers import get_serializer_cls
from bloomerp.utils.api import _fallback_filterset_class
from bloomerp.utils.filters import dynamic_filterset_factory

logger = logging.getLogger(__name__)

def get_auto_api_models() -> list[type[Model]]:
    api_models: list[type[Model]] = []

    for model in apps.get_models():
        if model._meta.abstract or model._meta.proxy:
            continue

        config = get_model_config(model)
        if config and config.should_enable_api_auto_generation():
            api_models.append(model)

    return api_models


AUTO_API_MODELS = get_auto_api_models()


class BaseModelApiView(BloomerpModelViewSet):
    model: type[Model] | None = None
    serializer_class = None
    actions: dict[str, str] = {}
    _bloomerp_filterset_classes: dict[type[Model], type] = {}

    @classonlymethod
    def as_view(cls, actions=None, **initkwargs):
        resolved_actions = actions or cls.actions
        if not resolved_actions:
            raise ImproperlyConfigured(
                f"{cls.__name__} must define a DRF action map."
            )
        return super().as_view(actions=resolved_actions, **initkwargs)

    def get_serializer_class(self):
        if self.serializer_class is not None:
            return self.serializer_class
        if self.model is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} requires a model."
            )
        return get_serializer_cls(self.model)

    @property
    def filterset_class(self):
        if self.model is None:
            return None

        filterset_class = self._bloomerp_filterset_classes.get(self.model)
        if filterset_class is not None:
            return filterset_class

        try:
            if not ApplicationField.get_for_model(self.model).exists():
                logger.warning(
                    "ApplicationField records are not available for API filterset model %s.%s",
                    self.model._meta.app_label,
                    self.model.__name__,
                )
                return _fallback_filterset_class(self.model)

            filterset_class = dynamic_filterset_factory(self.model)
        except Exception:
            logger.exception(
                "Error generating API filterset for model %s.%s",
                self.model._meta.app_label,
                self.model.__name__,
            )
            return _fallback_filterset_class(self.model)

        self._bloomerp_filterset_classes[self.model] = filterset_class
        return filterset_class
