from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from babel.messages.catalog import Catalog, Message
from django.apps import apps
from django.conf import settings
from django.template import Context, Template
from django.test import SimpleTestCase
from django.urls import reverse
from django.utils.translation import override

from bloomerp.config.definition import BloomerpConfig, BloomerpI18nSettings
from bloomerp.i18n.apps import discover_translatable_apps
from bloomerp.i18n.catalogs import (
    approve_translated_messages,
    merge_messages,
    read_catalog,
    reconcile_obsolete_messages,
    save_catalog,
    validate_message,
)
from bloomerp.i18n.models import model_messages
from bloomerp.i18n.translator import TranslationBatch, TranslationResult, translate_catalog
from bloomerp.models.application_field import ApplicationField


class TestI18nConfiguration(SimpleTestCase):
    def test_i18n_configuration_is_nested_on_bloomerp_config(self):
        config = BloomerpConfig(
            i18n={
                "languages": ["nl", "de"],
                "apps": ["bloomerp"],
                "llm": {"model": "example-model", "provider": "example"},
            }
        )

        self.assertEqual(config.i18n.languages, ["nl", "de"])
        self.assertEqual(config.i18n.apps, ["bloomerp"])
        self.assertEqual(config.i18n.llm.provider, "example")

    def test_explicit_app_discovery_accepts_app_label(self):
        discovered = discover_translatable_apps(
            BloomerpI18nSettings(apps=["bloomerp"])
        )

        self.assertEqual([app.label for app in discovered], ["bloomerp"])

    def test_auto_discovery_excludes_apps_installed_inside_project_venv(self):
        discovered = discover_translatable_apps(BloomerpI18nSettings())
        labels = {app.label for app in discovered}

        self.assertIn("bloomerp", labels)
        self.assertNotIn("channels", labels)
        self.assertNotIn("auth", labels)

    def test_catalog_merge_handles_references_without_line_numbers(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "nl" / "LC_MESSAGES" / "django.po"
            merge_messages(
                path,
                "nl",
                "django",
                [{"message": "Invoice", "locations": [("billing.invoice", None)]}],
            )
            merge_messages(
                path,
                "nl",
                "django",
                [{"message": "Invoice", "locations": [("billing.invoice", None)]}],
            )

            self.assertEqual(
                read_catalog(path, "nl", "django")["Invoice"].locations,
                [("billing.invoice", None)],
            )

    def test_catalog_merge_resurrects_obsolete_model_translation_without_duplicate(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "nl" / "LC_MESSAGES" / "django.po"
            catalog = Catalog(locale="nl", domain="django")
            catalog.add("Invoice")
            catalog.obsolete["Invoice"] = Message("Invoice", "Factuur")
            save_catalog(catalog, path)

            merge_messages(
                path,
                "nl",
                "django",
                [{"message": "Invoice", "locations": [("billing.invoice", None)]}],
            )

            merged = read_catalog(path, "nl", "django")
            self.assertEqual(merged["Invoice"].string, "Factuur")
            self.assertNotIn("Invoice", merged.obsolete)

    def test_reconcile_repairs_existing_active_and_obsolete_duplicate(self):
        catalog = Catalog(locale="nl", domain="django")
        active = catalog.add("Invoice")
        catalog.obsolete["Invoice"] = Message("Invoice", "Factuur", flags={"fuzzy"})

        self.assertEqual(reconcile_obsolete_messages(catalog), 1)
        self.assertEqual(active.string, "Factuur")
        self.assertIn("fuzzy", active.flags)
        self.assertNotIn("Invoice", catalog.obsolete)


class TestI18nCatalogs(SimpleTestCase):
    def test_merge_preserves_existing_translation(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "nl" / "LC_MESSAGES" / "djangojs.po"
            merge_messages(
                path,
                "nl",
                "djangojs",
                [{"message": "Search", "locations": [("search.ts", 1)]}],
                prune=True,
            )
            catalog = read_catalog(path, "nl", "djangojs")
            catalog["Search"].string = "Zoeken"
            save_catalog(catalog, path)
            merge_messages(
                path,
                "nl",
                "djangojs",
                [{"message": "Search", "locations": [("other.ts", 2)]}],
                prune=True,
            )

            merged = read_catalog(path, "nl", "djangojs")["Search"]
            self.assertEqual(merged.string, "Zoeken")
            self.assertEqual(merged.locations, [("other.ts", 2)])

    def test_validation_rejects_changed_placeholders(self):
        catalog = Catalog(locale="nl")
        message = catalog.add("Welcome %(name)s", "Welkom %(user)s")

        self.assertIn("placeholder mismatch in plural form 0", validate_message(message))

    def test_approve_clears_fuzzy_only_for_translated_messages(self):
        catalog = Catalog(locale="nl")
        translated = catalog.add("Save", "Opslaan", flags={"fuzzy"})
        untranslated = catalog.add("Cancel", "", flags={"fuzzy"})

        self.assertEqual(approve_translated_messages(catalog), 1)
        self.assertNotIn("fuzzy", translated.flags)
        self.assertIn("fuzzy", untranslated.flags)

    def test_model_metadata_includes_fallback_field_title(self):
        messages = model_messages(apps.get_app_config("bloomerp"), "en")

        self.assertTrue(any(item["message"] == "Field" for item in messages))

    def test_application_field_title_uses_declared_verbose_name(self):
        application_field = ApplicationField(field="first_name")
        model_field = SimpleNamespace(_verbose_name="Customer name")

        with patch.object(application_field, "_get_model_field", return_value=model_field):
            self.assertEqual(application_field.title, "Customer name")

    def test_application_field_title_humanizes_undeclared_label(self):
        application_field = ApplicationField(field="first_name")
        model_field = SimpleNamespace(_verbose_name=None)

        with patch.object(application_field, "_get_model_field", return_value=model_field):
            self.assertEqual(application_field.title, "First Name")


class _FakeStructuredModel:
    def invoke(self, messages):
        return TranslationBatch(
            results=[TranslationResult(index=0, translations=["Welkom %(name)s"])]
        )


class _FakeChatModel:
    def with_structured_output(self, schema):
        self.schema = schema
        return _FakeStructuredModel()


class TestI18nTranslation(SimpleTestCase):
    def test_translation_is_provider_independent_and_marked_fuzzy(self):
        catalog = Catalog(locale="nl")
        message = catalog.add("Welcome %(name)s")

        count = translate_catalog(
            catalog,
            "nl",
            "en",
            BloomerpConfig().i18n.llm,
            model_factory=lambda settings: _FakeChatModel(),
        )

        self.assertEqual(count, 1)
        self.assertEqual(message.string, "Welkom %(name)s")
        self.assertIn("fuzzy", message.flags)


class TestJavaScriptCatalog(SimpleTestCase):
    def test_json_catalog_endpoint_is_available(self):
        response = self.client.get(reverse("bloomerp_javascript_catalog"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("catalog", response.json())
        self.assertIn("plural", response.json())

    def test_json_catalog_combines_compiled_frontend_translation(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "nl"

        response = self.client.get(reverse("bloomerp_javascript_catalog"))

        self.assertEqual(response.json()["catalog"]["Remove row"], "Rij verwijderen")


class TestTemplateTranslations(SimpleTestCase):
    def test_trimmed_multiline_blocktrans_uses_compiled_translation(self):
        template = Template(
            "{% load i18n %}{% blocktrans trimmed %}\n"
            "    Save and Create New\n"
            "{% endblocktrans %}"
        )

        with override("nl"):
            rendered = template.render(Context())

        self.assertEqual(rendered, "Opslaan en nieuw maken")
