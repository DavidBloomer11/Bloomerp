from __future__ import annotations

import tomllib
from pathlib import Path

import click
from pydantic import ValidationError

from ..base import BloomerpAppManifest, BloomerpAppState
from ..toml import write_toml_model
from ..utils import get_project_metadata_dir
from .init import normalize_app_name


APP_MANIFEST_FILENAME = "app.bloomerp.toml"


def get_project_root() -> Path:
    return get_project_metadata_dir().parent


def resolve_app_dir(name: str | None = None) -> Path:
    project_root = get_project_root()
    if name:
        app_dir = project_root / "apps" / normalize_app_name(name)
        if (app_dir / APP_MANIFEST_FILENAME).is_file():
            return app_dir
        raise click.ClickException(f"Bloomerp app does not exist: {app_dir}")

    current = Path.cwd().resolve()
    for directory in (current, *current.parents):
        if directory == project_root.parent:
            break
        if (directory / APP_MANIFEST_FILENAME).is_file():
            return directory

    app_dirs = sorted(
        path.parent for path in (project_root / "apps").glob(f"*/{APP_MANIFEST_FILENAME}")
    )
    if len(app_dirs) == 1:
        return app_dirs[0]
    if not app_dirs:
        raise click.ClickException("This project does not contain a Bloomerp app.")
    raise click.ClickException("Multiple apps found. Pass the app name explicitly.")


def read_app_manifest(app_dir: Path) -> BloomerpAppManifest:
    path = app_dir / APP_MANIFEST_FILENAME
    try:
        return BloomerpAppManifest.model_validate(
            tomllib.loads(path.read_text(encoding="utf-8"))
        )
    except FileNotFoundError as exc:
        raise click.ClickException(f"Missing app manifest: {path}") from exc
    except (tomllib.TOMLDecodeError, ValidationError) as exc:
        raise click.ClickException(f"Invalid app manifest in {path}: {exc}") from exc


def app_state_path(app_dir: Path) -> Path:
    return get_project_metadata_dir() / "apps" / f"{app_dir.name}.toml"


def read_app_state(app_dir: Path) -> BloomerpAppState:
    path = app_state_path(app_dir)
    if not path.exists():
        return BloomerpAppState()
    try:
        return BloomerpAppState.model_validate(
            tomllib.loads(path.read_text(encoding="utf-8"))
        )
    except (tomllib.TOMLDecodeError, ValidationError) as exc:
        raise click.ClickException(f"Invalid app state in {path}: {exc}") from exc


def write_app_state(app_dir: Path, state: BloomerpAppState) -> None:
    write_toml_model(app_state_path(app_dir), state, exclude_defaults=True)
