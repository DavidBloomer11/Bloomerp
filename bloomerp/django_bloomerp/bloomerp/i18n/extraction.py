from __future__ import annotations

import json
import os
import subprocess
from contextlib import contextmanager
from pathlib import Path

from django.apps import AppConfig
from django.core.management import call_command

from bloomerp.config.definition import BloomerpI18nSettings
from bloomerp.i18n.catalogs import (
    catalog_path,
    merge_messages,
    read_catalog,
    reconcile_obsolete_messages,
    save_catalog,
)
from bloomerp.i18n.models import model_messages


@contextmanager
def working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def extract_django_messages(app: AppConfig, languages: list[str], verbosity: int = 0) -> None:
    for language in languages:
        path = catalog_path(Path(app.path), language, "django")
        if not path.exists():
            continue
        catalog = read_catalog(path, language, "django")
        if reconcile_obsolete_messages(catalog):
            save_catalog(catalog, path)

    with working_directory(Path(app.path)):
        call_command(
            "makemessages",
            locale=languages,
            domain="django",
            extensions=["py", "html", "txt"],
            ignore=["node_modules/*", "static/*", "static_src/*"],
            no_wrap=True,
            verbosity=verbosity,
        )


def extract_model_messages(
    app: AppConfig,
    languages: list[str],
    source_language: str,
) -> int:
    messages = model_messages(app, source_language)
    return sum(
        merge_messages(
            catalog_path(Path(app.path), language, "django"),
            language,
            "django",
            messages,
        )
        for language in languages
    )


def _frontend_files(app: AppConfig, globs: list[str]) -> list[Path]:
    root = Path(app.path)
    files = {path for pattern in globs for path in root.glob(pattern) if path.is_file()}
    return sorted(files)


def extract_typescript_messages(
    app: AppConfig,
    languages: list[str],
    config: BloomerpI18nSettings,
) -> int:
    files = _frontend_files(app, config.frontend_globs)
    if not files:
        return 0
    extractor = Path(__file__).with_name("extract_typescript.mjs")
    try:
        completed = subprocess.run(
            ["node", str(extractor), app.path, *map(str, files)],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Node.js is required for TypeScript message extraction.") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(exc.stderr.strip() or "TypeScript message extraction failed.") from exc
    messages = json.loads(completed.stdout)
    return sum(
        merge_messages(
            catalog_path(Path(app.path), language, "djangojs"),
            language,
            "djangojs",
            messages,
            prune=True,
        )
        for language in languages
    )
