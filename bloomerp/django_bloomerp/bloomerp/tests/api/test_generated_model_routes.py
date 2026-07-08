import asyncio
from unittest.mock import patch

from django_celery_beat.models import CrontabSchedule
from django.test import SimpleTestCase
from django.urls import resolve

from bloomerp.models.project_management.initiative import Initiative
from bloomerp.utils.api import generate_model_viewset_class, generate_serializer
from bloomerp.views.api.models import BloomerpModelViewSet


class GeneratedModelApiRouteTests(SimpleTestCase):
    def test_generated_viewset_can_be_built_in_async_context(self):
        async def build_viewset():
            return generate_model_viewset_class(
                model=Initiative,
                serializer=generate_serializer(Initiative),
                base_viewset=BloomerpModelViewSet,
            )

        viewset = asyncio.run(build_viewset())

        self.assertEqual(viewset.model, Initiative)

    def test_generated_model_endpoint_resolves(self):
        match = resolve("/api/initiatives/")

        self.assertEqual(match.url_name, "initiatives-list")

    def test_generated_serializer_normalizes_object_choice_values(self):
        serializer = generate_serializer(CrontabSchedule)()
        timezone_choices = serializer.fields["timezone"].choices

        first_choice_value = next(iter(timezone_choices.keys()))
        self.assertIsInstance(first_choice_value, str)

    def test_schema_fake_view_queryset_does_not_require_database_access(self):
        viewset = generate_model_viewset_class(
            model=Initiative,
            serializer=generate_serializer(Initiative),
            base_viewset=BloomerpModelViewSet,
        )
        view = viewset()
        view.swagger_fake_view = True

        queryset = view.get_queryset()

        self.assertEqual(queryset.model, Initiative)

    def test_schema_fake_view_filterset_does_not_require_application_fields(self):
        viewset = generate_model_viewset_class(
            model=Initiative,
            serializer=generate_serializer(Initiative),
            base_viewset=BloomerpModelViewSet,
        )
        view = viewset()
        view.swagger_fake_view = True

        with patch(
            "bloomerp.utils.api.ApplicationField.get_for_model",
            side_effect=RuntimeError("database unavailable"),
        ):
            filterset_class = view.filterset_class

        self.assertEqual(filterset_class.Meta.model, Initiative)
