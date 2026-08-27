from __future__ import annotations

import json
import re
import sys
import tomllib
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import click
from packaging.version import InvalidVersion, Version
from pydantic import ValidationError

from ..app.init import create_app
from ..base import (
    BloomerpEnvironment,
    BloomerpProjectManifest,
    BloomerpProjectState,
    BloomerpRuntime,
)
from ..toml import write_toml_model
from .scaffold_sync import synchronize_scaffold


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "template_project"
SUPPORTED_PYTHON_VERSIONS = {"3.12", "3.13"}
LOCAL_ONLY_TEMPLATE_PATHS = {
    Path(".env"),
    Path(".gitignore"),
    Path(".python-version"),
}


@dataclass(frozen=True)
class ProjectInitializationOptions:
    destination: Path
    manifest: BloomerpProjectManifest
    app_names: tuple[str, ...] = ()
    create_local_files: bool = True


@dataclass(frozen=True)
class ProjectInitializationResult:
    project_root: Path
    manifest_path: Path
    created_files: int
    installed_apps: tuple[str, ...]


def _distribution_name(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9-]+", "-", value).strip("-").lower()
    if not slug:
        raise click.ClickException("Project names must contain at least one letter or number.")
    return slug


def _render_template(text: str, replacements: dict[str, str]) -> str:
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)
    return text


def _copy_template_project(
    target_dir: Path,
    replacements: dict[str, str],
    *,
    create_local_files: bool,
) -> None:
    for source_path in sorted(TEMPLATE_DIR.rglob("*")):
        if "__pycache__" in source_path.parts or source_path.suffix == ".pyc":
            continue
        relative_path = source_path.relative_to(TEMPLATE_DIR)
        if "<app-name>" in relative_path.parts:
            continue
        if not create_local_files and relative_path in LOCAL_ONLY_TEMPLATE_PATHS:
            continue
        rendered_relative_path = Path(
            _render_template(relative_path.as_posix(), replacements)
        )
        destination_path = target_dir / rendered_relative_path

        if source_path.is_dir():
            destination_path.mkdir(parents=True, exist_ok=True)
            continue

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        contents = source_path.read_text(encoding="utf-8")
        destination_path.write_text(
            _render_template(contents, replacements), encoding="utf-8"
        )


def _bloomerp_version() -> str:
    try:
        return version("Bloomerp")
    except PackageNotFoundError:
        return "unknown"


def _project_python_version() -> str:
    running_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    if running_version in SUPPORTED_PYTHON_VERSIONS:
        return running_version
    return BloomerpRuntime.model_fields["python_version"].default


def _create_project_manifest(
    project_name: str,
    python_version: str,
) -> BloomerpProjectManifest:
    return BloomerpProjectManifest(
        name=project_name,
        description="",
        environment=BloomerpEnvironment(),
        runtime=BloomerpRuntime(
            bloomerp_version=_bloomerp_version(),
            python_version=python_version,
        ),
    )


def _write_project_metadata(
    target_dir: Path,
    manifest: BloomerpProjectManifest,
    *,
    create_local_files: bool,
) -> None:
    metadata_dir = target_dir / ".bloomerp"
    write_toml_model(metadata_dir / "project.toml", manifest)
    if create_local_files:
        write_toml_model(
            metadata_dir / "state.toml",
            BloomerpProjectState(),
            exclude_defaults=True,
        )


def _load_manifest(path: Path) -> BloomerpProjectManifest:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        return BloomerpProjectManifest.model_validate(data)
    except FileNotFoundError as exc:
        raise click.ClickException(f"Manifest does not exist: {path}") from exc
    except (tomllib.TOMLDecodeError, ValidationError) as exc:
        raise click.ClickException(f"Invalid project manifest in {path}: {exc}") from exc


def _validate_generator_version(manifest: BloomerpProjectManifest) -> None:
    generator_version = _bloomerp_version()
    if generator_version == "unknown":
        return

    try:
        requested_version = Version(manifest.runtime.bloomerp_version)
        installed_version = Version(generator_version)
    except InvalidVersion as exc:
        raise click.ClickException(
            "Project manifest and installed Bloomerp package must use valid versions."
        ) from exc

    if requested_version != installed_version:
        raise click.ClickException(
            f"Manifest requests Bloomerp {requested_version}, but generator is "
            f"Bloomerp {installed_version}."
        )


def initialize_project(
    options: ProjectInitializationOptions,
) -> ProjectInitializationResult:
    """Create one complete project without prompting for input."""

    target_dir = options.destination.expanduser().resolve()
    if target_dir.exists() and any(target_dir.iterdir()):
        raise click.ClickException(
            f"Target directory already exists and is not empty: {target_dir}"
        )

    _validate_generator_version(options.manifest)
    replacements = {
        "__PROJECT_NAME__": options.manifest.name,
        "__DISTRIBUTION_NAME__": _distribution_name(options.manifest.name),
        "__PYTHON_VERSION__": options.manifest.runtime.python_version,
    }
    _copy_template_project(
        target_dir,
        replacements,
        create_local_files=options.create_local_files,
    )
    _write_project_metadata(
        target_dir,
        options.manifest,
        create_local_files=options.create_local_files,
    )
    synchronize_scaffold(target_dir, options.manifest)

    for app_name in options.app_names:
        create_app(app_name, target_dir)

    final_manifest = _load_manifest(target_dir / ".bloomerp" / "project.toml")
    return ProjectInitializationResult(
        project_root=target_dir,
        manifest_path=target_dir / ".bloomerp" / "project.toml",
        created_files=sum(1 for path in target_dir.rglob("*") if path.is_file()),
        installed_apps=tuple(final_manifest.django.installed_apps),
    )


@click.command()
@click.argument("directory", required=False)
@click.option(
    "--manifest",
    "manifest_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
    help="Initialize from an existing .bloomerp/project.toml manifest.",
)
@click.option("--name", help="Project name for a newly generated manifest.")
@click.option(
    "--app",
    "app_names",
    multiple=True,
    help="Create a Bloomerp app without prompting. May be repeated.",
)
@click.option("--no-app", is_flag=True, help="Do not create an initial app.")
@click.option("--no-input", is_flag=True, help="Never prompt for input.")
@click.option(
    "--local-files/--no-local-files",
    default=True,
    show_default=True,
    help="Create local development files and project linkage state.",
)
@click.option(
    "--output",
    "output_format",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    show_default=True,
)
def init(
    directory: str | None,
    manifest_path: Path | None,
    name: str | None,
    app_names: tuple[str, ...],
    no_app: bool,
    no_input: bool,
    local_files: bool,
    output_format: str,
) -> None:
    """Create a Django project configured for Bloomerp."""

    if manifest_path is not None and name is not None:
        raise click.ClickException("--name cannot be combined with --manifest.")
    if app_names and no_app:
        raise click.ClickException("--app cannot be combined with --no-app.")
    if no_input and directory is None:
        raise click.ClickException("DIRECTORY is required when using --no-input.")

    target_name = directory
    if target_name is None:
        target_name = click.prompt(
            "Project directory",
            default="my-bloomerp-project",
        )
    target_dir = Path(target_name).expanduser().resolve()

    if manifest_path is not None:
        manifest = _load_manifest(manifest_path.expanduser().resolve())
    else:
        project_name = name
        if project_name is None:
            project_name = (
                target_dir.name
                if no_input
                else click.prompt("Project name", default=target_dir.name)
            )
        manifest = _create_project_manifest(
            project_name,
            _project_python_version(),
        )

    selected_apps = list(app_names)
    if not selected_apps and not no_app and not no_input:
        if click.confirm("Create a Bloomerp app in this project?", default=True):
            selected_apps.append(
                click.prompt("App name", default="core", show_default=True)
            )

    result = initialize_project(
        ProjectInitializationOptions(
            destination=target_dir,
            manifest=manifest,
            app_names=tuple(selected_apps),
            create_local_files=local_files,
        )
    )

    if output_format.lower() == "json":
        click.echo(
            json.dumps(
                {
                    "contract_version": 1,
                    "generator_version": _bloomerp_version(),
                    "project_root": str(result.project_root),
                    "manifest": str(result.manifest_path),
                    "created_files": result.created_files,
                    "installed_apps": list(result.installed_apps),
                },
                sort_keys=True,
            )
        )
        return

    click.echo(f"Created Bloomerp project at {target_dir}")
    for app_name in selected_apps:
        click.echo(f"Created Bloomerp app: apps.{app_name}")
    click.echo("")
    click.echo("Next steps:")
    click.echo(f"  cd {target_dir}")
    click.echo("  python -m venv .venv")
    click.echo("  source .venv/bin/activate")
    click.echo("  pip install -e .")
    click.echo("  python manage.py migrate")
    click.echo("  python manage.py createsuperuser")
    click.echo("  python manage.py save_application_fields")
    click.echo("  python manage.py runserver")
