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
from .scaffold_sync import synchronize_scaffold


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
    app_environments = [
        read_app_manifest(app_dir).environment
        for app_dir in find_app_dirs(project_root)
    ]
    return manifest.model_copy(
        update={
            "environment": merge_environments(
                manifest.environment,
                *app_environments,
            )
        }
    )


def synchronize_local_project(
    manifest: BloomerpProjectManifest | None = None,
    *,
    force: bool = False,
) -> ProjectSyncResult:
    """Merge app declarations and synchronize the generated project scaffold."""

    project_root = _project_root()
    synchronized = _merge_app_environments(
        manifest or get_project_manifest(),
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
) -> ProjectSyncResult:
    """Pull remote project metadata and user-managed environment names."""

    project_id = _linked_project_id()
    api_client = client or BloomerpCliClient()
    remote = api_client.request(
        "GET",
        f"{PROJECTS_ENDPOINT}{project_id}/",
    ).json()
    if not isinstance(remote, dict):
        raise click.ClickException("Bloomerp.io returned invalid project metadata.")

    manifest = get_project_manifest()
    updates = {
        field: str(remote[field] or "")
        for field in ("name", "description")
        if field in remote
    }
    if "bloomerp_version" in remote:
        updates["runtime"] = manifest.runtime.model_copy(
            update={"bloomerp_version": str(remote["bloomerp_version"])}
        )
    manifest = manifest.model_copy(update=updates)

    environment_payload = api_client.request(
        "GET",
        f"{PROJECT_ENVIRONMENT_VARIABLES_ENDPOINT}?project={project_id}",
    ).json()
    remote_names = {
        str(item["name"]).strip().upper()
        for item in _response_results(environment_payload)
        if item.get("name") and not item.get("is_platform_managed", False)
    }
    manifest = manifest.model_copy(
        update={
            "environment": manifest.environment.model_copy(
                update={
                    "optional": sorted(
                        set(manifest.environment.optional)
                        | (remote_names - set(manifest.environment.required))
                    )
                }
            )
        }
    )
    return synchronize_local_project(manifest, force=force)


def synchronize_project_to_remote(
    *,
    client: BloomerpCliClient | None = None,
    force: bool = False,
) -> ProjectSyncResult:
    """Synchronize locally, then push editable project metadata."""

    project_id = _linked_project_id()
    result = synchronize_local_project(force=force)
    manifest = result.manifest
    api_client = client or BloomerpCliClient()
    api_client.request(
        "PATCH",
        f"{PROJECTS_ENDPOINT}{project_id}/",
        json={
            "name": manifest.name,
            "description": manifest.description,
            "bloomerp_version": manifest.runtime.bloomerp_version,
        },
    )
    return result


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
@click.option(
    "--force",
    is_flag=True,
    help="Back up and replace locally modified generated scaffold files.",
)
def sync(from_remote: bool, to_remote: bool, force: bool) -> None:
    """Synchronize the project manifest, app environment, and scaffold."""

    if from_remote and to_remote:
        raise click.ClickException(
            "--from-remote and --to-remote cannot be used together."
        )
    if from_remote:
        result = synchronize_project_from_remote(force=force)
    elif to_remote:
        result = synchronize_project_to_remote(force=force)
    else:
        result = synchronize_local_project(force=force)
    echo_project_sync(result)
