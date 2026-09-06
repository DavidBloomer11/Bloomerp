from __future__ import annotations

import os
import sys
from pathlib import Path

import click

from ..base import (
    BloomerpAppDjango,
    BloomerpAppManifest,
    BloomerpAppModel,
    BloomerpAppModule,
    BloomerpAppRoute,
)
from ..client import BloomerpCliClient
from ..toml import write_toml_model
from ._utils import (
    APP_MANIFEST_FILENAME,
    get_project_root,
    read_app_manifest,
    read_app_state,
    resolve_app_dir,
)


MARKETPLACE_APPS_ENDPOINT = "/api/apps/"
REMOTE_APP_METADATA_FIELDS = ("description", "tagline")


def discover_app_manifest(
    app_dir: Path,
    existing: BloomerpAppManifest,
) -> BloomerpAppManifest:
    """Discover locally owned app metadata from Django and the app README."""

    project_root = get_project_root()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django
    from django.apps import apps

    django.setup()

    expected_name = f"apps.{app_dir.name}"
    app_config = next(
        (config for config in apps.get_app_configs() if config.name == expected_name),
        None,
    )
    if app_config is None:
        raise click.ClickException(
            f"Django app {expected_name!r} is not installed in this project."
        )

    from bloomerp.modules.definition import module_registry
    from bloomerp.router import router

    module_registry.refresh()
    modules = [
        BloomerpAppModule(
            id=module.full_id or module.id,
            name=module.name,
            description=module.description or "",
        )
        for module in module_registry.get_all().values()
        if module.owner_app_label == app_config.label
    ]
    models = [
        BloomerpAppModel(
            name=model.__name__,
            database_table=model._meta.db_table,
        )
        for model in app_config.get_models()
    ]
    routes = [
        BloomerpAppRoute(
            url=route.path,
            name=route.name,
            description=route.description or "",
        )
        for route in router.get_routes_by_app(app_config)
    ]

    description_path = app_dir / "readme.md"
    description = (
        description_path.read_text(encoding="utf-8").strip()
        if description_path.is_file()
        else existing.description
    )

    return existing.model_copy(
        update={
            "django": BloomerpAppDjango(
                app_config=(
                    f"{app_config.__class__.__module__}."
                    f"{app_config.__class__.__name__}"
                )
            ),
            "modules": sorted(modules, key=lambda module: module.id),
            "models": sorted(models, key=lambda model: model.name),
            "routes": sorted(routes, key=lambda route: (route.url, route.name)),
            "description": description,
        }
    )


def synchronize_local_app(app_dir: Path) -> BloomerpAppManifest:
    """Synchronize an app manifest with locally discoverable app state."""

    manifest = discover_app_manifest(app_dir, read_app_manifest(app_dir))
    write_toml_model(app_dir / APP_MANIFEST_FILENAME, manifest)
    return manifest


def _linked_app_id(app_dir: Path) -> str:
    app_id = read_app_state(app_dir).app_id
    if not app_id:
        raise click.ClickException(
            f"App {app_dir.name!r} is not linked. Run 'bloomerp app link "
            f"{app_dir.name}' first."
        )
    return app_id


def synchronize_app_from_remote(
    app_dir: Path,
    *,
    client: BloomerpCliClient | None = None,
) -> BloomerpAppManifest:
    """Pull editable marketplace metadata without changing application state."""

    app_id = _linked_app_id(app_dir)
    api_client = client or BloomerpCliClient()
    payload = api_client.request(
        "GET",
        f"{MARKETPLACE_APPS_ENDPOINT}{app_id}/",
    ).json()
    if not isinstance(payload, dict):
        raise click.ClickException("Bloomerp.io returned invalid app metadata.")

    existing = read_app_manifest(app_dir)
    updates = {
        field: str(payload[field] or "")
        for field in REMOTE_APP_METADATA_FIELDS
        if field in payload
    }
    if "name" in payload:
        updates["display_name"] = str(payload["name"] or "")
    manifest = existing.model_copy(update=updates)
    write_toml_model(app_dir / APP_MANIFEST_FILENAME, manifest)
    return manifest


def synchronize_app_to_remote(
    app_dir: Path,
    *,
    client: BloomerpCliClient | None = None,
    synchronize_local: bool = True,
) -> BloomerpAppManifest:
    """Push editable app metadata after synchronizing local app state."""

    app_id = _linked_app_id(app_dir)
    manifest = (
        synchronize_local_app(app_dir)
        if synchronize_local
        else read_app_manifest(app_dir)
    )
    api_client = client or BloomerpCliClient()
    api_client.request(
        "PATCH",
        f"{MARKETPLACE_APPS_ENDPOINT}{app_id}/",
        json={
            "name": manifest.display_name or manifest.name.replace("_", " ").title(),
            **{
                field: getattr(manifest, field)
                for field in REMOTE_APP_METADATA_FIELDS
            },
        },
    )
    return manifest


def echo_app_sync(app_dir: Path, manifest: BloomerpAppManifest) -> None:
    """Print a concise app synchronization result."""

    click.echo(
        f"Synchronized {app_dir / APP_MANIFEST_FILENAME}: "
        f"{len(manifest.modules)} module(s), {len(manifest.models)} model(s), "
        f"{len(manifest.routes)} route(s)."
    )


@click.command("sync")
@click.argument("name", required=False)
@click.option("--from-remote", is_flag=True, help="Pull linked marketplace metadata.")
@click.option("--to-remote", is_flag=True, help="Push local metadata after syncing.")
def sync(name: str | None, from_remote: bool, to_remote: bool) -> None:
    """Synchronize local and linked remote app metadata."""

    if from_remote and to_remote:
        raise click.ClickException(
            "--from-remote and --to-remote cannot be used together."
        )
    app_dir = resolve_app_dir(name)
    if from_remote:
        manifest = synchronize_app_from_remote(app_dir)
    elif to_remote:
        manifest = synchronize_app_to_remote(app_dir)
    else:
        manifest = synchronize_local_app(app_dir)
    echo_app_sync(app_dir, manifest)
