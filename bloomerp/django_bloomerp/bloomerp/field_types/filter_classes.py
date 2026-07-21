import django_filters
from django.db.models import BooleanField, DateField, DateTimeField, DecimalField, DurationField, Field, FloatField, IntegerField, Model, TimeField, UUIDField


def filter_class_for_model_field(model_field: Field | None) -> type[django_filters.Filter]:
    if isinstance(model_field, BooleanField):
        return django_filters.BooleanFilter
    if isinstance(model_field, DateTimeField):
        return django_filters.DateTimeFilter
    if isinstance(model_field, DateField):
        return django_filters.DateFilter
    if isinstance(model_field, TimeField):
        return django_filters.TimeFilter
    if isinstance(model_field, DurationField):
        return django_filters.DurationFilter
    if isinstance(model_field, UUIDField):
        return django_filters.UUIDFilter
    if isinstance(model_field, (IntegerField, DecimalField, FloatField)):
        return django_filters.NumberFilter
    return django_filters.CharFilter


def resolve_model_field_path(model: type[Model], field_path: str) -> Field | None:
    current_model = model
    resolved_field = None

    for field_name in field_path.split("__"):
        try:
            resolved_field = current_model._meta.get_field(field_name)
        except Exception:
            return None

        related_field = getattr(resolved_field, "remote_field", None)
        if related_field is not None and related_field.model is not None:
            current_model = related_field.model

    return resolved_field


def filter_class_for_model_field_path(model: type[Model], field_path: str) -> type[django_filters.Filter]:
    return filter_class_for_model_field(resolve_model_field_path(model, field_path))
