from bloomerp.models.users.user import AbstractBloomerpUser
from django.db.models import Model


class BasePermissionCompiler:
    """Base class for permission compilers."""

    def __init__(self, user: AbstractBloomerpUser):
        self.user = user

    def compile(self, model: type[Model]) -> set[str]:
        """Compile the permissions for the given model."""
        raise NotImplementedError("Subclasses must implement this method.")