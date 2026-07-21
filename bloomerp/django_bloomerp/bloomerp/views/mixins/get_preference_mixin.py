


from typing import Any, Optional, Type

from bloomerp.models.users.base_preference import BasePreference
from bloomerp.models.users.user import AbstractBloomerpUser
from bloomerp.services.preference_services import PreferenceManager
from django.db.models import Model

class GetPreferenceMixin:
    """
    Mixin to get the selected preference for a given model.
    """
    def get_preference(self, model:Type[Model], scope: dict[str, Any] | None = None, user:Optional[AbstractBloomerpUser]=None) -> BasePreference:
        user = user or self.request.user
        manager = PreferenceManager(user)
        return manager.get_or_create_selected(model, scope=scope)