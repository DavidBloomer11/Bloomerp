from __future__ import annotations

import json
import tempfile
from pathlib import Path

import click

from ..client import BloomerpCliClient
from ._utils import read_app_manifest, read_app_state, resolve_app_dir
from .build import build_app_wheel


ENDPOINT = "/api/apps/upload/"

def upload_app(app_dir: Path, *, client=None, wheel_path=None) -> dict:
    """Build/upload one immutable private or public app release."""
    state = read_app_state(app_dir)
    if not state.app_id:
        raise click.ClickException(
            "This app is not linked. Run 'bloomerp app link' first."
        )
    manifest = read_app_manifest(app_dir)

    def upload_wheel(path: Path) -> dict:
        with path.open("rb") as wheel_file:
            response = (client or BloomerpCliClient()).request(
                "POST",
                ENDPOINT,
                data={
                    "app_id": state.app_id,
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

    return payload


@click.command()
@click.argument("name", required=False)
@click.option("--wheel", "wheel_path", type=click.Path(path_type=Path, exists=True, dir_okay=False))
def upload(name, wheel_path):
    """Build and upload a linked app version."""
    payload = upload_app(resolve_app_dir(name), wheel_path=wheel_path)
    click.echo(f"Uploaded {payload['version']} ({payload['version_id']}).")
