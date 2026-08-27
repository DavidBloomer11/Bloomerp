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


def _read_toml_model(path: Path, model_type):
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        return model_type.model_validate(data)
    except FileNotFoundError as exc:
        raise click.ClickException(f"Missing Bloomerp metadata file: {path}") from exc
    except (tomllib.TOMLDecodeError, ValidationError) as exc:
        raise click.ClickException(f"Invalid Bloomerp metadata in {path}: {exc}") from exc


def get_project_manifest() -> BloomerpProjectManifest:
    """Return the manifest for the project containing the current directory."""
    return _read_toml_model(
        get_project_metadata_dir() / "project.toml",
        BloomerpProjectManifest,
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
    write_toml_model(get_project_metadata_dir() / "project.toml", manifest)


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