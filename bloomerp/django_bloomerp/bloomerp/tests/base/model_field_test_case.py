from django.db import models
from django.test import SimpleTestCase


class BloomerpModelFieldTestCase(SimpleTestCase):
    """Base class providing common validity checks for a model field."""

    field_class: type[models.Field] | None = None

    def get_field_kwargs(self) -> dict:
        """Return constructor arguments for fields that need custom setup."""
        return {}

    def test_model_field_is_valid(self) -> None:
        """
        Use case: An app exposes a custom Django model field.
        Expected result: The field can be constructed and deconstructed by Django.
        """
        # 1. Do not execute the reusable base class itself.
        if self.field_class is None:
            return

        # 2. Instantiate and validate Django's migration representation.
        self.assertTrue(issubclass(self.field_class, models.Field))
        field = self.field_class(**self.get_field_kwargs())
        _, import_path, args, kwargs = field.deconstruct()

        # 3. Confirm the field exposes a reusable import path and arguments.
        self.assertTrue(import_path)
        self.assertIsInstance(args, list)
        self.assertIsInstance(kwargs, dict)
