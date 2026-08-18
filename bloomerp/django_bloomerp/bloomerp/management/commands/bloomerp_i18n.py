from __future__ import annotations

from pathlib import Path

from django.core.management import BaseCommand, CommandError, call_command

from bloomerp.config.definition import get_bloomerp_config
from bloomerp.i18n.apps import discover_translatable_apps, get_app_source_language
from bloomerp.i18n.catalogs import (
    approve_translated_messages,
    catalog_path,
    read_catalog,
    save_catalog,
    validate_message,
)
from bloomerp.i18n.extraction import (
    extract_django_messages,
    extract_model_messages,
    extract_route_messages,
    extract_typescript_messages,
    working_directory,
)
from bloomerp.i18n.languages import catalog_locale, unique_languages
from bloomerp.i18n.translator import translate_catalog


class Command(BaseCommand):
    help = "Extract, translate, validate and compile BloomERP app translations."

    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            choices=["extract", "translate", "approve", "validate", "compile", "sync"],
        )
        parser.add_argument("--languages", nargs="+", metavar="LANGUAGE")
        parser.add_argument("--apps", nargs="+", metavar="APP")
        parser.add_argument("--skip-frontend", action="store_true")
        parser.add_argument("--skip-models", action="store_true")
        parser.add_argument("--include-fuzzy", action="store_true")
        parser.add_argument("--accept-machine", action="store_true")
        parser.add_argument("--no-translate", action="store_true")
        parser.add_argument("--model")
        parser.add_argument("--provider")

    def handle(self, *args, **options):
        config = get_bloomerp_config().i18n
        languages = self._languages(config.languages, options["languages"])
        try:
            app_configs = discover_translatable_apps(config, options["apps"])
        except LookupError as exc:
            raise CommandError(str(exc)) from exc
        if not app_configs:
            raise CommandError("No translatable apps were discovered.")
        app_languages = self._app_languages(app_configs, languages, config)

        action = options["action"]
        if action in {"extract", "sync"}:
            self._extract(app_languages, config, options)
        if action == "translate" or (action == "sync" and not options["no_translate"]):
            self._translate(app_languages, config, options)
        if action == "approve" or (action == "compile" and options["accept_machine"]):
            self._approve(app_languages)
        if action in {"validate", "sync"}:
            self._validate(app_languages)
        if action in {"compile", "sync"}:
            self._compile(app_languages)

    def _languages(self, configured, requested):
        if requested:
            languages = requested
        elif configured:
            languages = configured
        else:
            languages = []
        languages = unique_languages(languages)
        if not languages:
            raise CommandError("Configure i18n.languages or pass --languages.")
        return languages

    def _app_languages(self, app_configs, languages, config):
        app_languages = []
        for app in app_configs:
            source_language = get_app_source_language(app, config)
            targets = [
                catalog_locale(language)
                for language in languages
                if language != source_language
            ]
            app_languages.append((app, source_language, targets))
        return app_languages

    def _extract(self, app_languages, config, options):
        for app, source_language, languages in app_languages:
            if not languages:
                continue
            self.stdout.write(f"Extracting {app.name} (source: {source_language})")
            try:
                extract_django_messages(app, languages, verbosity=max(self.verbosity - 1, 0))
                if not options["skip_models"]:
                    extract_model_messages(app, languages, source_language)
                extract_route_messages(app, languages)
                if not options["skip_frontend"]:
                    extract_typescript_messages(app, languages, config)
            except (OSError, RuntimeError) as exc:
                raise CommandError(f"Could not extract {app.name}: {exc}") from exc

    @property
    def verbosity(self):
        return int(getattr(self, "_verbosity", 1))

    def execute(self, *args, **options):
        self._verbosity = options.get("verbosity", 1)
        return super().execute(*args, **options)

    def _translate(self, app_languages, config, options):
        llm_settings = config.llm.model_copy(
            update={
                key: value
                for key, value in {
                    "model": options["model"],
                    "provider": options["provider"],
                }.items()
                if value
            }
        )
        for app, source_language, languages in app_languages:
            for language in languages:
                for domain in ("django", "djangojs"):
                    path = catalog_path(Path(app.path), language, domain)
                    if not path.exists():
                        continue
                    catalog = read_catalog(path, language, domain)
                    try:
                        count = translate_catalog(
                            catalog,
                            language,
                            source_language,
                            llm_settings,
                            include_fuzzy=options["include_fuzzy"],
                            mark_fuzzy=(
                                config.mark_machine_translations_fuzzy
                                and not options["accept_machine"]
                            ),
                        )
                    except RuntimeError as exc:
                        raise CommandError(str(exc)) from exc
                    if count:
                        save_catalog(catalog, path)
                        self.stdout.write(f"Translated {count} messages in {path}")

    def _validate(self, app_languages):
        failures = []
        for app, _source_language, languages in app_languages:
            for language in languages:
                for domain in ("django", "djangojs"):
                    path = catalog_path(Path(app.path), language, domain)
                    if not path.exists():
                        continue
                    catalog = read_catalog(path, language, domain)
                    for message in catalog:
                        for error in validate_message(message):
                            failures.append(f"{path}: {message.id!r}: {error}")
        if failures:
            raise CommandError("Invalid translations:\n" + "\n".join(failures))
        self.stdout.write(self.style.SUCCESS("Translation catalogs are valid."))

    def _approve(self, app_languages):
        approved = 0
        for app, _source_language, languages in app_languages:
            for language in languages:
                for domain in ("django", "djangojs"):
                    path = catalog_path(Path(app.path), language, domain)
                    if not path.exists():
                        continue
                    catalog = read_catalog(path, language, domain)
                    count = approve_translated_messages(catalog)
                    if count:
                        save_catalog(catalog, path)
                        approved += count
        self.stdout.write(self.style.SUCCESS(f"Approved {approved} translated messages."))

    def _compile(self, app_languages):
        for app, _source_language, languages in app_languages:
            if not languages:
                continue
            if not (Path(app.path) / "locale").exists():
                continue
            with working_directory(Path(app.path)):
                call_command(
                    "compilemessages",
                    locale=languages,
                    verbosity=self.verbosity,
                )
        self.stdout.write(self.style.SUCCESS("Translation catalogs compiled."))
