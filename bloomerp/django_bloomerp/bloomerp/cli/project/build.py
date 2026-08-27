from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import click

from bloomerp.cli.utils import get_project_manifest, get_project_metadata_dir

from .scaffold_sync import assert_scaffold_current


def get_project_root() -> Path:
    """Return the root directory of the current Bloomerp project."""
    return get_project_metadata_dir().parent


def build_project_wheel(output_dir: Path) -> Path:
    """Build the current project and copy its wheel into OUTPUT_DIR."""
    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.is_file():
        raise click.ClickException(f"Missing project build configuration: {pyproject_path}")

    assert_scaffold_current(project_root, get_project_manifest())

    output_dir = output_dir.expanduser()
    if not output_dir.is_absolute():
        output_dir = project_root / output_dir
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="bloomerp-build-") as temporary_dir:
        staging_dir = Path(temporary_dir)
        command = [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(staging_dir),
            str(project_root),
        ]
        try:
            subprocess.run(command, check=True)
        except FileNotFoundError as exc:
            raise click.ClickException("Could not start the Python wheel build.") from exc
        except subprocess.CalledProcessError as exc:
            raise click.ClickException(
                f"Wheel build failed with exit code {exc.returncode}."
            ) from exc

        wheels = list(staging_dir.glob("*.whl"))
        if len(wheels) != 1:
            raise click.ClickException(
                f"Expected one wheel from the build, but found {len(wheels)}."
            )

        destination = output_dir / wheels[0].name
        shutil.copy2(wheels[0], destination)

    return destination


def find_built_wheel(directory: Path) -> Path:
    """Return the sole wheel in DIRECTORY, rejecting ambiguous artifacts."""
    project_root = get_project_root()
    if not directory.is_absolute():
        directory = project_root / directory
    wheels = sorted(directory.expanduser().glob("*.whl"))
    if not wheels:
        raise click.ClickException(
            f"No wheel found in {directory}. Run 'bloomerp project build' first."
        )
    if len(wheels) > 1:
        raise click.ClickException(
            f"Multiple wheels found in {directory}. Pass one using '--wheel PATH'."
        )
    return wheels[0].resolve()


@click.command("build")
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("dist"),
    show_default=True,
    help="Directory in which to place the built wheel.",
)
def build(output_dir: Path) -> None:
    """Build the current Bloomerp project as a Python wheel."""
    wheel_path = build_project_wheel(output_dir)
    click.echo(f"Built project wheel: {wheel_path}")
