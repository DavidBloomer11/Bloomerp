from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.db.models import Model, QuerySet


def serialize_form_value(value: Any) -> Any:
    """Convert a cleaned form value into JSON-compatible data."""
    if isinstance(value, StructuredFormValue):
        return value.serialize()
    if isinstance(value, Model):
        return str(value.pk)
    if isinstance(value, QuerySet):
        return [str(pk) for pk in value.values_list("pk", flat=True)]
    if isinstance(value, dict):
        return {key: serialize_form_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [serialize_form_value(item) for item in value]
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    return value


class StructuredFormValue(ABC):
    """Persistence and serialization contract for non-model form values."""

    @abstractmethod
    def save(self, parent: Model, *, user=None) -> None:
        raise NotImplementedError

    @abstractmethod
    def serialize(self) -> Any:
        raise NotImplementedError
