from datetime import date, datetime, time
from decimal import Decimal
from importlib import import_module
from typing import Any, Callable
from uuid import UUID

from django.apps import apps
from django.db import models

from bloomerp.celery.utils import is_celery_available


try:
    from celery import shared_task
except ImportError:
    def shared_task(*task_args, **task_kwargs):
        if task_args and callable(task_args[0]) and not task_kwargs:
            return task_args[0]

        def decorator(func):
            return func

        return decorator


SERIALIZED_TYPE_KEY = "__bloomerp_async_type__"


class AsyncSerializationError(TypeError):
    """Raised when a value cannot be safely passed through Celery."""


def _callable_path(func: Callable) -> str:
    module = getattr(func, "__module__", None)
    qualname = getattr(func, "__qualname__", None)
    if not module or not qualname or "<locals>" in qualname:
        raise AsyncSerializationError("Only importable module-level callables can run asynchronously.")
    return f"{module}.{qualname}"


def _import_callable(path: str) -> Callable:
    module_path, _, qualname = path.partition(":")
    if not qualname:
        module_path, _, qualname = path.rpartition(".")
    if not module_path or not qualname:
        raise AsyncSerializationError(f"Invalid callable path: {path!r}")

    obj = import_module(module_path)
    for attr in qualname.split("."):
        obj = getattr(obj, attr)
    if not callable(obj):
        raise AsyncSerializationError(f"Imported object is not callable: {path!r}")
    return obj


def serialize_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, models.Model):
        if value.pk is None:
            raise AsyncSerializationError("Unsaved model instances cannot run asynchronously.")
        return {
            SERIALIZED_TYPE_KEY: "model",
            "app_label": value._meta.app_label,
            "model_name": value._meta.model_name,
            "pk": serialize_value(value.pk),
        }
    if isinstance(value, datetime):
        return {SERIALIZED_TYPE_KEY: "datetime", "value": value.isoformat()}
    if isinstance(value, date):
        return {SERIALIZED_TYPE_KEY: "date", "value": value.isoformat()}
    if isinstance(value, time):
        return {SERIALIZED_TYPE_KEY: "time", "value": value.isoformat()}
    if isinstance(value, Decimal):
        return {SERIALIZED_TYPE_KEY: "decimal", "value": str(value)}
    if isinstance(value, UUID):
        return {SERIALIZED_TYPE_KEY: "uuid", "value": str(value)}
    if isinstance(value, tuple):
        return {
            SERIALIZED_TYPE_KEY: "tuple",
            "items": [serialize_value(item) for item in value],
        }
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    if isinstance(value, set):
        return {
            SERIALIZED_TYPE_KEY: "set",
            "items": [serialize_value(item) for item in value],
        }
    if isinstance(value, dict):
        return {
            SERIALIZED_TYPE_KEY: "dict",
            "items": [
                [serialize_value(key), serialize_value(item)]
                for key, item in value.items()
            ],
        }

    raise AsyncSerializationError(f"Cannot serialize value of type {type(value).__name__}.")


def deserialize_value(value: Any) -> Any:
    if isinstance(value, list):
        return [deserialize_value(item) for item in value]
    if not isinstance(value, dict) or SERIALIZED_TYPE_KEY not in value:
        return value

    value_type = value[SERIALIZED_TYPE_KEY]
    if value_type == "model":
        model_cls = apps.get_model(value["app_label"], value["model_name"])
        return model_cls.objects.get(pk=deserialize_value(value["pk"]))
    if value_type == "datetime":
        return datetime.fromisoformat(value["value"])
    if value_type == "date":
        return date.fromisoformat(value["value"])
    if value_type == "time":
        return time.fromisoformat(value["value"])
    if value_type == "decimal":
        return Decimal(value["value"])
    if value_type == "uuid":
        return UUID(value["value"])
    if value_type == "tuple":
        return tuple(deserialize_value(item) for item in value["items"])
    if value_type == "set":
        return {deserialize_value(item) for item in value["items"]}
    if value_type == "dict":
        return {
            deserialize_value(key): deserialize_value(item)
            for key, item in value["items"]
        }

    raise AsyncSerializationError(f"Unknown serialized value type: {value_type!r}.")


@shared_task(name="bloomerp.utils.async_utils.run_serialized_async_job")
def run_serialized_async_job(func_path: str, serialized_args: Any, serialized_kwargs: Any) -> Any:
    func = _import_callable(func_path)
    args = deserialize_value(serialized_args)
    kwargs = deserialize_value(serialized_kwargs)
    return serialize_value(func(*args, **kwargs))


def run_async_or_sync(func: Callable, *args, **kwargs) -> tuple[bool, Any]:
    """Tries to run a function asynchronously, and if that doesn't work, runs it synchronously.

    Args:
        func (Callable): the function to run

    Returns:
        tuple[bool, Any]: 
            - bool: True if the function was run asynchronously, False if it was run synchronously
            - Any: the result of the function call
    """
    if is_celery_available():
        try:
            func_path = _callable_path(func)
            serialized_args = serialize_value(args)
            serialized_kwargs = serialize_value(kwargs)
            result = run_serialized_async_job.delay(
                func_path,
                serialized_args,
                serialized_kwargs,
            )
            return True, result
        except Exception:
            pass

    return False, func(*args, **kwargs)
