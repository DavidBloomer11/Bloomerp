from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import click

from ..app._utils import find_app_dirs, read_app_manifest
from ..base import BloomerpProjectManifest
from ..client import BloomerpCliClient
from ..environment import merge_environments
from ..utils import (
    get_project_manifest,
    get_project_metadata_dir,
    get_project_state,
    write_project_manifest,
)
from .scaffold import synchronize_scaffold


PROJECTS_ENDPOINT = "/api/projects/"
PROJECT_ENVIRONMENT_VARIABLES_ENDPOINT = "/api/project_environment_variables/"


@dataclass(frozen=True)
class ProjectSyncResult:
    manifest: BloomerpProjectManifest
    updated_scaffold_files: tuple[Path, ...]
    created_project_files: tuple[Path, ...]
    backup_root: Path | None


def _project_root() -> Path:
    return get_project_metadata_dir().parent


def _linked_project_id() -> str:
    project_id = get_project_state().project_id
    if not project_id:
        raise click.ClickException(
            "This project is not linked. Run 'bloomerp project link' first."
        )
    return project_id


def _response_results(payload: object) -> list[dict]:
    if isinstance(payload, list):
        values = payload
    elif isinstance(payload, dict) and isinstance(payload.get("results"), list):
        values = payload["results"]
    else:
        raise click.ClickException(
            "Bloomerp.io returned invalid project environment metadata."
        )
    return [value for value in values if isinstance(value, dict)]


def _merge_app_environments(
    manifest: BloomerpProjectManifest,
    project_root: Path,
) -> BloomerpProjectManifest:
    from .marketplace_sources import local_source_dirs, locks_for, app_package
    from ..app._utils import read_app_state
    directories = local_source_dirs(manifest)
    app_manifests = [read_app_manifest(directory) for directory in directories]
    for directory, app_manifest in zip(directories, app_manifests):
        package = app_package(app_manifest.django.app_config)
        for lock in locks_for(manifest):
            if package == app_package(lock["manifest"]["django"]["app_config"]) and read_app_state(directory).app_id != lock["id"]:
                raise click.ClickException(f"Local app {directory.name} collides with another app package; link it explicitly.")
    return manifest.model_copy(update={
        "django": manifest.django.model_copy(update={"installed_apps": list(dict.fromkeys([
            *(["project_app"] if get_project_state().generated_wheel_filename else []),
            *[lock["manifest"]["django"]["app_config"] for lock in locks_for(manifest)],
            *[item.django.app_config for item in app_manifests if item.django.app_config],
        ]))}),
        "environment": merge_environments(manifest.environment, *[app.environment for app in app_manifests]),
    })



def synchronize_local_project(
    manifest: BloomerpProjectManifest | None = None,
    *,
    force: bool = False,
) -> ProjectSyncResult:
    """Merge app declarations and synchronize the generated project scaffold."""

    project_root = _project_root()
    manifest = manifest or get_project_manifest()
    from .marketplace_sources import ensure_release_cache
    ensure_release_cache(manifest)
    synchronized = _merge_app_environments(
        manifest,
        project_root,
    )
    updated, created, backup_root = synchronize_scaffold(
        project_root,
        synchronized,
        force=force,
    )
    write_project_manifest(synchronized)
    return ProjectSyncResult(
        manifest=synchronized,
        updated_scaffold_files=tuple(updated),
        created_project_files=tuple(created),
        backup_root=backup_root,
    )


def synchronize_project_from_remote(
    *,
    client: BloomerpCliClient | None = None,
    force: bool = False,
    artifacts: bool = False,
) -> ProjectSyncResult:
    """Pull the model-generated manifest without creating a snapshot."""
    from ..utils import write_project_state
    if artifacts:
        from .remote import pull_project
        pull_project(client or BloomerpCliClient(), _linked_project_id(), force=force)
    payload = (client or BloomerpCliClient()).request("GET", f"{PROJECTS_ENDPOINT}{_linked_project_id()}/manifest/").json()
    manifest = BloomerpProjectManifest.model_validate(payload["manifest"])
    from ..marketplace.manage import resolve_manifest
    manifest = resolve_manifest(manifest)
    result = synchronize_local_project(manifest, force=force)
    state = get_project_state()
    state.manifest_revision = payload["revision"]
    write_project_state(state)
    return result


def synchronize_project_to_remote(*, client=None, force=False) -> ProjectSyncResult:
    """Register local apps and synchronize declarations, without building code."""
    from ..base import BloomerpProjectApp
    from ..app._utils import read_app_state, write_app_state
    from ..app.link import _create_app
    from ..utils import write_project_state
    from .marketplace_sources import upload_manifest, local_source_dirs
    project_id = _linked_project_id()
    api_client = client or BloomerpCliClient()
    state = get_project_state()
    if not state.manifest_revision:
        raise click.ClickException("Pull the project manifest before pushing configuration.")
    manifest = get_project_manifest()
    selections = {str(item.id): item for item in manifest.apps}
    for directory in local_source_dirs(manifest):
        app_state = read_app_state(directory)
        if not app_state.app_id:
            app_state.app_id = str(_create_app(api_client, directory)["id"])
            write_app_state(directory, app_state)
        selections.setdefault(app_state.app_id, BloomerpProjectApp(id=app_state.app_id, name=read_app_manifest(directory).name))
    manifest.apps = list(selections.values())
    result = synchronize_local_project(manifest, force=force)
    payload = api_client.request("POST", f"{PROJECTS_ENDPOINT}{project_id}/manifest/", json={
        "manifest": upload_manifest(result.manifest), "base_revision": state.manifest_revision,
    }).json()
    state.manifest_revision = payload["revision"]
    write_project_state(state)
    # Persist the server's normalized declarations; local discovery supplies source AppConfigs.
    return synchronize_local_project(BloomerpProjectManifest.model_validate(payload["manifest"]), force=force)


def echo_project_sync(result: ProjectSyncResult) -> None:
    """Print a concise project synchronization result."""

    click.echo(
        "Project synchronized: "
        f"{len(result.manifest.environment.required)} required and "
        f"{len(result.manifest.environment.optional)} optional environment "
        "variable(s); "
        f"{len(result.updated_scaffold_files)} generated file(s) updated."
    )
    if result.backup_root is not None:
        click.echo(f"Previous generated files backed up to {result.backup_root}")


@click.command("sync")
@click.option("--from-remote", is_flag=True, help="Pull linked project metadata.")
@click.option("--to-remote", is_flag=True, help="Push local metadata after syncing.")
@click.option("--artifacts", is_flag=True, help="Also download the latest built artifacts with --from-remote.")
@click.option(
    "--force",
    is_flag=True,
    help="Back up and replace locally modified generated scaffold files.",
)
def sync(from_remote: bool, to_remote: bool, force: bool, artifacts: bool = False) -> None:
    """Synchronize the project manifest, app environment, and scaffold."""

    if artifacts and not from_remote:
        raise click.ClickException("--artifacts requires --from-remote.")
    if from_remote and to_remote:
        raise click.ClickException(
            "--from-remote and --to-remote cannot be used together."
        )
    if from_remote:
        result = synchronize_project_from_remote(force=force, artifacts=artifacts)
    elif to_remote:
        result = synchronize_project_to_remote(force=force)
    else:
        result = synchronize_local_project(force=force)
    echo_project_sync(result)
