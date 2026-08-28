from __future__ import annotations

import json
import tempfile
from pathlib import Path

import click

from ..client import BloomerpCliClient
from ._utils import read_app_manifest, read_app_state, resolve_app_dir
from .build import build_app_wheel


ENDPOINT = "/api/marketplace_apps/upload/"

@click.command()
@click.argument("name", required=False)
@click.option(
    "--wheel",
    "wheel_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
    help="Upload an existing app wheel instead of building one.",
)
def upload(name: str | None, wheel_path: Path | None) -> None:
    """Build and upload a linked app version to Bloomerp.io."""

    app_dir = resolve_app_dir(name)
    state = read_app_state(app_dir)
    if not state.marketplace_app_id:
        raise click.ClickException(
            "This app is not linked. Run 'bloomerp app link' first."
        )
    manifest = read_app_manifest(app_dir)

    def upload_wheel(path: Path) -> dict:
        with path.open("rb") as wheel_file:
            response = BloomerpCliClient().request(
                "POST",
                ENDPOINT,
                data={
                    "marketplace_app_id": state.marketplace_app_id,
                    "manifest": json.dumps(manifest.model_dump(mode="json")),
                },
                files={
                    "wheel": (path.name, wheel_file, "application/octet-stream")
                },
                timeout=300,
            )
        payload = response.json()
        if not isinstance(payload, dict) or not payload.get("version_id"):
            raise click.ClickException("Bloomerp.io returned an invalid upload response.")
        return payload

    if wheel_path is not None:
        payload = upload_wheel(wheel_path.expanduser().resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="bloomerp-app-upload-") as directory:
            payload = upload_wheel(build_app_wheel(app_dir, Path(directory)))

    action = "Created" if payload.get("created", True) else "Reused"
    click.echo(
        f"{action} {manifest.name} {payload.get('version', manifest.version)} "
        f"({payload['version_id']})."
    )
