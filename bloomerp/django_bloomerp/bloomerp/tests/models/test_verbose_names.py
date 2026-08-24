from django.apps import apps
from django.test import SimpleTestCase


class ModelVerboseNameTests(SimpleTestCase):
    def test_bloomerp_models_and_fields_have_explicit_verbose_names(self):
        models = [
            model
            for model in apps.get_models()
            if model.__module__.startswith("bloomerp.models.")
        ]

        missing_model_names = []
        missing_field_names = []

        for model in models:
            options = model._meta
            if "verbose_name" not in options.original_attrs:
                missing_model_names.append(f"{options.label}.verbose_name")
            if "verbose_name_plural" not in options.original_attrs:
                missing_model_names.append(f"{options.label}.verbose_name_plural")

            for field in [*options.fields, *options.many_to_many]:
                if getattr(field, "_verbose_name", None) is None:
                    missing_field_names.append(f"{options.label}.{field.name}")

        self.assertEqual(missing_model_names, [])
        self.assertEqual(missing_field_names, [])
