from datetime import date, datetime, time
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.test import TestCase

from bloomerp.utils.async_utils import (
    deserialize_value,
    run_async_or_sync,
    run_serialized_async_job,
    serialize_value,
)


def count_serialized_values(*, user, payload):
    return {
        "user_id": user.id,
        "payload": payload,
    }


class AsyncUtilsTests(TestCase):
    def test_serialize_value_round_trips_model_and_common_value_types(self):
        user = get_user_model().objects.create_user(
            username="async-utils",
            password="test",
        )
        value_id = uuid4()
        payload = {
            "user": user,
            "date": date(2026, 7, 7),
            "datetime": datetime(2026, 7, 7, 12, 30, 15),
            "time": time(12, 30, 15),
            "decimal": Decimal("10.50"),
            "uuid": value_id,
            "tuple": ("a", 1),
            "set": {"x", "y"},
        }

        deserialized = deserialize_value(serialize_value(payload))

        self.assertEqual(deserialized["user"], user)
        self.assertEqual(deserialized["date"], payload["date"])
        self.assertEqual(deserialized["datetime"], payload["datetime"])
        self.assertEqual(deserialized["time"], payload["time"])
        self.assertEqual(deserialized["decimal"], payload["decimal"])
        self.assertEqual(deserialized["uuid"], value_id)
        self.assertEqual(deserialized["tuple"], payload["tuple"])
        self.assertEqual(deserialized["set"], payload["set"])

    def test_run_serialized_async_job_deserializes_values_before_calling_function(self):
        user = get_user_model().objects.create_user(
            username="async-task",
            password="test",
        )

        result = run_serialized_async_job(
            "bloomerp.tests.test_async_utils.count_serialized_values",
            serialize_value(tuple()),
            serialize_value(
                {
                    "user": user,
                    "payload": {"sent_at": date(2026, 7, 7)},
                }
            ),
        )

        self.assertEqual(
            deserialize_value(result),
            {
                "user_id": user.id,
                "payload": {"sent_at": date(2026, 7, 7)},
            },
        )

    @patch("bloomerp.utils.async_utils.run_serialized_async_job.delay")
    @patch("bloomerp.utils.async_utils.is_celery_available", return_value=True)
    def test_run_async_or_sync_queues_serialized_job_when_celery_is_available(
        self,
        _is_celery_available,
        delay_mock,
    ):
        delay_mock.return_value = "async-result"

        ran_async, result = run_async_or_sync(
            count_serialized_values,
            user=None,
            payload={"value": Decimal("3.25")},
        )

        self.assertTrue(ran_async)
        self.assertEqual(result, "async-result")
        delay_mock.assert_called_once()
        func_path, serialized_args, serialized_kwargs = delay_mock.call_args.args
        self.assertEqual(
            func_path,
            "bloomerp.tests.test_async_utils.count_serialized_values",
        )
        self.assertEqual(deserialize_value(serialized_args), tuple())
        self.assertEqual(
            deserialize_value(serialized_kwargs),
            {"user": None, "payload": {"value": Decimal("3.25")}},
        )

    @patch("bloomerp.utils.async_utils.is_celery_available", return_value=True)
    def test_run_async_or_sync_falls_back_to_sync_for_non_importable_callable(
        self,
        _is_celery_available,
    ):
        func = lambda value: value + 1

        ran_async, result = run_async_or_sync(func, 41)

        self.assertFalse(ran_async)
        self.assertEqual(result, 42)
