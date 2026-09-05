from __future__ import annotations

import tomllib
from pathlib import Path

import click
from pydantic import ValidationError

from bloomerp.cli.base import BloomerpProjectManifest, BloomerpProjectState
from bloomerp.cli.client import BloomerpCliClient
from bloomerp.cli.toml import write_toml_model


def get_project_metadata_dir(start: Path | None = None) -> Path:
    """Find the nearest .bloomerp directory from START or the current directory."""
    current = (start or Path.cwd()).expanduser().resolve()
    if current.is_file():
        current = current.parent

    for directory in (current, *current.parents):
        metadata_dir = directory / ".bloomerp"
        if metadata_dir.is_dir():
            return metadata_dir

    raise click.ClickException(
        "This is not a Bloomerp project. Run this command inside a project "
        "created with 'bloomerp project init'."
    )


def _read_toml_model(path: Path, model_type, *, cache_releases: bool = True):
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        if model_type is BloomerpProjectManifest and (data.get("schema_version") == 1 or "marketplace_extensions" in data):
            locks = data.pop("marketplace_apps", [])
            declarations = data.pop("marketplace_extensions", [])
            by_slug = {lock["app_slug"]: lock for lock in locks}
            extensions = []
            for declaration in declarations:
                lock = by_slug.get(declaration["slug"], {})
                app_id = lock.get("app_id") or lock.get("marketplace_app_id")
                if not app_id:
                    raise click.ClickException("Pull the project with the previous CLI to resolve legacy app IDs before upgrading.")
                extensions.append({"id": app_id, "version": declaration["version"]})
            data["extensions"] = extensions
            data["apps"] = [{**lock, "id": lock.get("app_id") or lock.get("marketplace_app_id")} for lock in locks]
            data["schema_version"] = 2
        if cache_releases and model_type is BloomerpProjectManifest and data.get("schema_version", 2) == 2:
            locks = data.get("apps", [])
            if locks and all(isinstance(item, dict) and "manifest" in item for item in locks):
                from .project.marketplace_sources import write_release_cache
                write_release_cache(locks, path.parent)
        return model_type.model_validate(data)
    except FileNotFoundError as exc:
        raise click.ClickException(f"Missing Bloomerp metadata file: {path}") from exc
    except (tomllib.TOMLDecodeError, ValidationError) as exc:
        raise click.ClickException(f"Invalid Bloomerp metadata in {path}: {exc}") from exc


def get_project_manifest(project_root: Path | None = None) -> BloomerpProjectManifest:
    """Read an explicit project root without side effects, or discover the CLI workspace."""
    return _read_toml_model(
        (Path(project_root).expanduser().resolve() / ".bloomerp" if project_root is not None
         else get_project_metadata_dir()) / "project.bloomerp.toml",
        BloomerpProjectManifest,
        cache_releases=project_root is None,
    )


def get_project_state() -> BloomerpProjectState:
    """Return the state for the project containing the current directory."""
    return _read_toml_model(
        get_project_metadata_dir() / "state.toml",
        BloomerpProjectState,
    )


def write_project_state(state: BloomerpProjectState) -> None:
    """Replace the current project's local state file."""
    write_toml_model(get_project_metadata_dir() / "state.toml", state)
    

def write_project_manifest(manifest:BloomerpProjectManifest) -> None:
    """Writes the project manifest using the remote"""
    write_toml_model(get_project_metadata_dir() / "project.bloomerp.toml", manifest)


def get_remote_project(project_id:str) -> dict:
    """Returns the remote project

    Args:
        project_id (str): the project ID

    Returns:
        dict: the project dictionary
    """
    client = BloomerpCliClient()
    return client.request(
        "GET",
        f"/api/projects/{project_id}"
    ).json()