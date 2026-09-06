from __future__ import annotations

import json
import tempfile
from pathlib import Path

import click

from bloomerp.cli.client import BloomerpCliClient
from bloomerp.cli.utils import get_project_manifest, get_project_state

from .build import build_project_wheel, find_built_wheel, get_project_root


def upload_project_wheel(wheel_path: Path) -> dict:
    """Upload WHEEL_PATH and current manifest as project snapshot."""
    if not wheel_path.is_file():
        raise click.ClickException(f"Wheel does not exist: {wheel_path}")
    if wheel_path.suffix.lower() != ".whl":
        raise click.ClickException(f"Project artifact must be a wheel (.whl): {wheel_path}")

    state = get_project_state()
    if not state.project_id:
        raise click.ClickException(
            "This project is not linked. Run 'bloomerp project link' first."
        )

    from .marketplace_sources import assert_no_overrides, validate_user_wheel
    assert_no_overrides()
    if not state.manifest_revision:
        raise click.ClickException("Sync the project before uploading.")
    validate_user_wheel(wheel_path, get_project_manifest())
    with wheel_path.open("rb") as wheel_file:
        response = BloomerpCliClient().request(
            "POST",
            f"/api/projects/{state.project_id}/upload-from-cli/",
            data={"base_revision": state.manifest_revision},
            files={
                "wheel": (
                    wheel_path.name,
                    wheel_file,
                    "application/octet-stream",
                )
            },
            timeout=300,
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise click.ClickException(
            "Bloomerp.io returned an invalid upload response."
        ) from exc
    if not isinstance(payload, dict) or not payload.get("id"):
        raise click.ClickException("Bloomerp.io returned an invalid upload response.")
    from ..utils import write_project_state
    state.snapshot_id = str(payload["id"])
    write_project_state(state)
    return payload


def _print_upload_result(payload: dict) -> None:
    action = "Created" if payload.get("created", True) else "Reused"
    click.echo(f"{action} project snapshot {payload['id']}.")
    if payload.get("snapshot_hash"):
        click.echo(f"Snapshot hash: {payload['snapshot_hash']}")


@click.command()
@click.option(
    "--wheel",
    "wheel_path",
    type=click.Path(path_type=Path, exists=True, dir_okay=False),
    help="Upload an existing wheel instead of building the project.",
)
@click.option(
    "--build/--no-build",
    "build_first",
    default=True,
    show_default=True,
    help="Build before uploading; --no-build uses the wheel in dist/.",
)
def upload(wheel_path: Path | None, build_first: bool) -> None:
    """Upload the current project into a new Bloomerp.io snapshot."""
    # Validate linkage before spending time on a build.
    state = get_project_state()
    if not state.project_id:
        raise click.ClickException(
            "This project is not linked. Run 'bloomerp project link' first."
        )

    if wheel_path is not None:
        payload = upload_project_wheel(wheel_path.expanduser().resolve())
    elif not build_first:
        wheel_path = find_built_wheel(get_project_root() / "dist")
        payload = upload_project_wheel(wheel_path)
    else:
        with tempfile.TemporaryDirectory(prefix="bloomerp-upload-") as temporary_dir:
            wheel_path = build_project_wheel(Path(temporary_dir))
            payload = upload_project_wheel(wheel_path)

    _print_upload_result(payload)
