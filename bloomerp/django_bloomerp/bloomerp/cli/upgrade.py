from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import click
import requests
from packaging.requirements import InvalidRequirement, Requirement
from packaging.version import InvalidVersion, Version

from .utils import (
    get_project_manifest,
    get_project_metadata_dir,
    write_project_manifest,
)


PYPI_PROJECT_URL = "https://pypi.org/pypi/Bloomerp/json"


def normalize_version(value: str) -> str:
    """Return VALUE as a normalized PEP 440 release version."""

    try:
        return str(Version(value.strip()))
    except InvalidVersion as exc:
        raise click.ClickException(f"Invalid Bloomerp version: {value!r}.") from exc


def latest_bloomerp_version() -> str:
    """Return the latest Bloomerp version published on PyPI."""

    try:
        response = requests.get(PYPI_PROJECT_URL, timeout=30)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise click.ClickException(
            f"Could not resolve the latest Bloomerp version from PyPI: {exc}"
        ) from exc

    info = payload.get("info") if isinstance(payload, dict) else None
    version = info.get("version") if isinstance(info, dict) else None
    if not isinstance(version, str) or not version.strip():
        raise click.ClickException("PyPI returned invalid Bloomerp release metadata.")
    return normalize_version(version)


def _bloomerp_requirement(dependencies: object) -> tuple[str, str]:
    if not isinstance(dependencies, list):
        raise click.ClickException(
            "pyproject.toml [project].dependencies must be a list."
        )

    matches = []
    for dependency in dependencies:
        if not isinstance(dependency, str):
            continue
        try:
            requirement = Requirement(dependency)
        except InvalidRequirement:
            continue
        if requirement.name.lower() == "bloomerp":
            matches.append((dependency, requirement))

    if not matches:
        raise click.ClickException(
            "pyproject.toml does not declare Bloomerp in [project].dependencies."
        )
    if len(matches) > 1:
        raise click.ClickException(
            "pyproject.toml declares Bloomerp more than once in "
            "[project].dependencies."
        )

    dependency, requirement = matches[0]
    extras = f"[{','.join(sorted(requirement.extras))}]" if requirement.extras else ""
    marker = f"; {requirement.marker}" if requirement.marker else ""
    return dependency, f"Bloomerp{extras}=={{version}}{marker}"


def updated_pyproject_contents(path: Path, version: str) -> tuple[str, str]:
    """Return updated pyproject contents and the exact Bloomerp requirement."""

    try:
        contents = path.read_text(encoding="utf-8")
        document = tomllib.loads(contents)
    except FileNotFoundError as exc:
        raise click.ClickException(
            f"Missing project build configuration: {path}"
        ) from exc
    except tomllib.TOMLDecodeError as exc:
        raise click.ClickException(f"Invalid pyproject.toml: {exc}") from exc

    project = document.get("project")
    if not isinstance(project, dict):
        raise click.ClickException("pyproject.toml does not contain a [project] table.")
    current, replacement_template = _bloomerp_requirement(project.get("dependencies"))
    replacement = replacement_template.format(version=version)

    project_match = re.search(
        r"(?ms)^\[project\][ \t]*$.*?(?=^\[(?!project(?:\.|\]))|\Z)",
        contents,
    )
    if project_match is None:
        raise click.ClickException("Could not locate [project] in pyproject.toml.")

    section = project_match.group(0)
    encoded_current = json.dumps(current)
    encoded_replacement = json.dumps(replacement)
    if section.count(encoded_current) != 1:
        raise click.ClickException(
            "Could not safely update the Bloomerp dependency in pyproject.toml. "
            "Use a standard double-quoted dependency entry."
        )
    updated_section = section.replace(encoded_current, encoded_replacement, 1)
    updated_contents = (
        contents[: project_match.start()]
        + updated_section
        + contents[project_match.end() :]
    )
    return updated_contents, replacement


def _environment_python(project_root: Path, explicit_python: Path | None) -> Path:
    if explicit_python is not None:
        return explicit_python.expanduser().resolve()

    active_environment = os.environ.get("VIRTUAL_ENV")
    if active_environment:
        environment_root = Path(active_environment)
        candidates = (
            environment_root / "bin" / "python",
            environment_root / "Scripts" / "python.exe",
        )
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        raise click.ClickException(
            f"VIRTUAL_ENV does not contain a Python executable: {environment_root}"
        )

    candidates = (
        project_root / ".venv" / "bin" / "python",
        project_root / ".venv" / "Scripts" / "python.exe",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    raise click.ClickException(
        "No project Python environment found. Activate a virtual environment, "
        "create .venv, pass --python, or explicitly use --system."
    )


def install_bloomerp(
    requirement: str,
    *,
    project_root: Path,
    explicit_python: Path | None,
    system: bool,
) -> Path:
    """Install a Bloomerp requirement into the selected Python environment."""

    if explicit_python is not None and system:
        raise click.ClickException("--python and --system cannot be used together.")
    python = Path(sys.executable).resolve() if system else _environment_python(
        project_root,
        explicit_python,
    )
    if not python.is_file():
        raise click.ClickException(f"Python executable does not exist: {python}")

    uv = shutil.which("uv")
    command = (
        [uv, "pip", "install", "--python", str(python), requirement]
        if uv
        else [str(python), "-m", "pip", "install", requirement]
    )
    try:
        subprocess.run(command, cwd=project_root, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise click.ClickException(
            f"Could not install {requirement} into {python}."
        ) from exc
    return python


@click.command("upgrade")
@click.argument("version", required=False)
@click.option(
    "--install",
    is_flag=True,
    help="Install the selected version into the project Python environment.",
)
@click.option(
    "--python",
    "python_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
    help="Python executable to use with --install.",
)
@click.option(
    "--system",
    is_flag=True,
    help="With --install, explicitly install into the CLI's Python environment.",
)
def upgrade(
    version: str | None,
    install: bool,
    python_path: Path | None,
    system: bool,
) -> None:
    """Upgrade a Bloomerp project's declared runtime version."""

    if (python_path is not None or system) and not install:
        raise click.ClickException("--python and --system require --install.")

    selected_version = (
        normalize_version(version) if version else latest_bloomerp_version()
    )
    metadata_dir = get_project_metadata_dir()
    project_root = metadata_dir.parent
    pyproject_path = project_root / "pyproject.toml"
    pyproject_contents, requirement = updated_pyproject_contents(
        pyproject_path,
        selected_version,
    )
    manifest = get_project_manifest()
    manifest = manifest.model_copy(
        update={
            "runtime": manifest.runtime.model_copy(
                update={"bloomerp_version": selected_version}
            )
        }
    )

    installed_python = None
    if install:
        installed_python = install_bloomerp(
            requirement,
            project_root=project_root,
            explicit_python=python_path,
            system=system,
        )

    pyproject_path.write_text(pyproject_contents, encoding="utf-8")
    write_project_manifest(manifest)
    click.echo(f"Upgraded project metadata to Bloomerp {selected_version}.")
    if installed_python is not None:
        click.echo(f"Installed Bloomerp {selected_version} into {installed_python}.")
    else:
        click.echo(
            "Run your package manager's install/sync command, or rerun with "
            "--install to update the project environment."
        )
