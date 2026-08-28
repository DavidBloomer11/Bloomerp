from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import click

from ._utils import read_app_manifest


def build_app_wheel(app_dir: Path, output_dir: Path) -> Path:
    manifest = read_app_manifest(app_dir)
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="bloomerp-app-build-") as temporary_dir:
        staging_root = Path(temporary_dir)
        staging_app = staging_root / "apps" / app_dir.name
        (staging_root / "apps").mkdir(parents=True)
        (staging_root / "apps" / "__init__.py").touch()
        shutil.copytree(
            app_dir,
            staging_app,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        (staging_root / "pyproject.toml").write_text(
            "\n".join(
                [
                    "[project]",
                    f"name = {json.dumps(manifest.name.replace('_', '-'))}",
                    f"version = {json.dumps(manifest.version)}",
                    f"description = {json.dumps(manifest.description)}",
                    'requires-python = ">=3.12,<3.14"',
                    'dependencies = ["Bloomerp"]',
                    "",
                    "[build-system]",
                    'requires = ["setuptools>=75", "wheel"]',
                    'build-backend = "setuptools.build_meta"',
                    "",
                    "[tool.setuptools.packages.find]",
                    f'include = ["apps.{app_dir.name}*"]',
                    "",
                    "[tool.setuptools.package-data]",
                    '"*" = ["templates/**/*", "static/**/*", "app.bloomerp.toml"]',
                    "",
                ]
            ),
            encoding="utf-8",
        )
        built_dir = staging_root / "dist"
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "build",
                    "--wheel",
                    "--no-isolation",
                    "--outdir",
                    str(built_dir),
                    str(staging_root),
                ],
                check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            raise click.ClickException("App wheel build failed.") from exc

        wheels = list(built_dir.glob("*.whl"))
        if len(wheels) != 1:
            raise click.ClickException(
                f"Expected one app wheel, but found {len(wheels)}."
            )
        destination = output_dir / wheels[0].name
        shutil.copy2(wheels[0], destination)
        return destination
