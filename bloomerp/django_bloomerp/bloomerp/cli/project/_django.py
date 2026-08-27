from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence

import click

from .build import get_project_root


def run_django_command(command: str, arguments: Sequence[str] = ()) -> None:
    """Run a Django management command for the current Bloomerp project."""
    project_root = get_project_root()
    manage_py = project_root / "manage.py"
    if not manage_py.is_file():
        raise click.ClickException(f"Missing Django project entry point: {manage_py}")

    result = subprocess.run(
        [sys.executable, str(manage_py), command, *arguments],
        cwd=project_root,
    )
    if result.returncode:
        raise click.exceptions.Exit(result.returncode)
