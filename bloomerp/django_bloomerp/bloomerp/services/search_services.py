from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session

from bloomerp.models.application_field import ApplicationField
from bloomerp.models.definition import BloomerpModelConfig
from bloomerp.services.permission_services import UserPermissionManager


def is_model_searchable(model) -> bool:
    """Return whether a model may appear in cross-model object search."""
    internal_models = [ContentType, ApplicationField, Permission, LogEntry, Session]
    if not model or model in internal_models or getattr(model._meta, "swapped", None):
        return False

    config = getattr(model, "bloomerp_config", None)
    if isinstance(config, BloomerpModelConfig):
        return not config.is_internal and config.allow_string_search
    return True


def get_accessible_search_models(user, permission_manager: UserPermissionManager | None = None) -> list:
    """Return de-duplicated models visible through auth or row policies."""
    permission_manager = permission_manager or UserPermissionManager(user)
    content_types = list(user.accessible_content_types)
    row_policy_ct_ids = permission_manager.get_row_policies().values_list(
        "content_type_id", flat=True
    ).distinct()
    if row_policy_ct_ids:
        content_types.extend(ContentType.objects.filter(id__in=row_policy_ct_ids))

    seen_ids: set[int] = set()
    models = []
    for content_type in content_types:
        if content_type.id in seen_ids:
            continue
        seen_ids.add(content_type.id)
        model = content_type.model_class()
        if is_model_searchable(model):
            models.append(model)
    return models
