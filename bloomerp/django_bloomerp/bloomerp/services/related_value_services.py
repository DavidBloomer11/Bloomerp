from __future__ import annotations

from typing import Any

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import QuerySet

from bloomerp.models.application_field import ApplicationField
from bloomerp.permissions.definition import BloomerpPermission
from bloomerp.permissions.manager import UserPolicyManager


SUPPORTED_RELATED_FIELD_TYPES = (models.ForeignKey, models.OneToOneField)


def get_related_model_field(application_field: ApplicationField) -> models.Field:
    """Resolve and validate a concrete to-one relation field."""
    try:
        model_field = application_field._get_model_field()
    except Exception as exc:
        raise ValidationError("The application field does not resolve to a model field.") from exc

    if not isinstance(model_field, SUPPORTED_RELATED_FIELD_TYPES):
        raise ValidationError("The application field is not a foreign-key relation.")
    return model_field


def get_allowed_related_queryset(
    application_field: ApplicationField,
    user,
) -> QuerySet:
    """Return related records allowed by row permissions and field constraints.

    The related model's default manager supplies its canonical ordering. The
    permission manager narrows that queryset to viewable rows, after which
    Django's own ``limit_choices_to`` representation is applied unchanged.
    """
    model_field = get_related_model_field(application_field)
    related_model = model_field.remote_field.model
    queryset = UserPolicyManager(user).get_queryset(
        related_model,
        BloomerpPermission.VIEW,
    )
    limit_choices_to = model_field.get_limit_choices_to()
    if limit_choices_to:
        queryset = queryset.complex_filter(limit_choices_to)
    return queryset


def get_allowed_related_object(
    application_field: ApplicationField,
    user,
    value: Any,
) -> models.Model:
    """Resolve a related object only when it belongs to the allowed queryset."""
    model_field = get_related_model_field(application_field)
    raw_pk = value.pk if isinstance(value, models.Model) else value
    try:
        normalized_pk = model_field.target_field.to_python(raw_pk)
        return get_allowed_related_queryset(application_field, user).get(pk=normalized_pk)
    except (TypeError, ValueError, ValidationError, ObjectDoesNotExist) as exc:
        raise ValidationError("Select a valid related value.") from exc
