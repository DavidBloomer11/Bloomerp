from pathlib import Path
from typing import Iterable

from django.apps import AppConfig, apps
from django.conf import settings

from bloomerp.config.definition import BloomerpI18nSettings

NON_PROJECT_PATH_PARTS = {
    ".tox",
    ".venv",
    "dist-packages",
    "node_modules",
    "site-packages",
    "venv",
}


def _resolve_app(identifier: str) -> AppConfig:
    try:
        return apps.get_app_config(identifier)
    except LookupError:
        matches = [app for app in apps.get_app_configs() if app.name == identifier]
        if len(matches) == 1:
            return matches[0]
        raise LookupError(f"No installed Django app matches {identifier!r}.")


def discover_translatable_apps(
    config: BloomerpI18nSettings,
    requested_apps: Iterable[str] | None = None,
) -> list[AppConfig]:
    """Return framework and project apps that should own translation catalogs."""

    identifiers = list(requested_apps or [])
    if not identifiers and config.apps != "auto":
        identifiers = list(config.apps)

    if identifiers:
        candidates = [_resolve_app(identifier) for identifier in identifiers]
    else:
        base_dir = Path(getattr(settings, "BASE_DIR", Path.cwd())).resolve()
        candidates = []
        for app in apps.get_app_configs():
            app_path = Path(app.path).resolve()
            if app.name == "bloomerp" or _is_project_app_path(app_path, base_dir):
                candidates.append(app)

    excluded = set(config.exclude_apps)
    return sorted(
        [
            app
            for app in candidates
            if app.label not in excluded and app.name not in excluded
        ],
        key=lambda app: app.name,
    )


def _is_project_app_path(app_path: Path, base_dir: Path) -> bool:
    if not app_path.is_relative_to(base_dir):
        return False
    relative_parts = set(app_path.relative_to(base_dir).parts)
    return relative_parts.isdisjoint(NON_PROJECT_PATH_PARTS)
