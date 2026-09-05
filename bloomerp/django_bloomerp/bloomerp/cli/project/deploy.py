"""Build, upload, deploy the exact snapshot, and report its terminal result."""
import tempfile
import time
from pathlib import Path

import click

from bloomerp.cli.client import BloomerpCliClient
from bloomerp.cli.utils import get_project_state
from .build import build_project_wheel
from .upload import upload_project_wheel
from .sync import synchronize_project_to_remote


@click.command()
@click.option("--timeout", type=click.IntRange(min=1), default=1800, show_default=True)
def deploy(timeout: int) -> None:
    """Build and upload local code, then wait for that exact release."""
    state = get_project_state()
    if not state.project_id:
        raise click.ClickException("Run bloomerp project link first.")
    from .marketplace_sources import assert_no_overrides, local_source_dirs
    from ..app._utils import read_app_state
    from ..app.upload import upload_app
    from ..utils import write_project_manifest
    assert_no_overrides()
    client = BloomerpCliClient()
    result = synchronize_project_to_remote(client=client)
    manifest = result.manifest
    versions = {read_app_state(directory).app_id: upload_app(directory, client=client)["version"]
                for directory in local_source_dirs(manifest)}
    for extension in manifest.extensions:
        if str(extension.id) in versions:
            extension.version = versions[str(extension.id)]
    write_project_manifest(manifest)
    synchronize_project_to_remote(client=client)
    with tempfile.TemporaryDirectory(prefix="bloomerp-deploy-") as directory:
        wheel = build_project_wheel(Path(directory))
        snapshot = upload_project_wheel(wheel)
    client = BloomerpCliClient()
    response = client.request("POST", f"/api/deployments/deploy/{state.project_id}/",
                              json={"snapshot_id": snapshot["id"]}).json()
    deployment_id = response.get("deployment_id")
    if not deployment_id:
        raise click.ClickException("Server did not return a deployment ID.")
    click.echo(f"Deployment {deployment_id} queued for snapshot {snapshot['id']}.")
    deadline = time.monotonic() + timeout
    previous = None
    while time.monotonic() < deadline:
        deployment = client.request("GET", f"/api/deployments/{deployment_id}/").json()
        status = deployment["status"]
        progress = (status, deployment.get("current_step"))
        if progress != previous:
            click.echo(f"{status}: {progress[1] or ''}")
            previous = progress
        if status in {"SUCCEEDED", "SKIPPED"}:
            return
        if status in {"FAILED", "CANCELLED"}:
            raise click.ClickException(deployment.get("error_message") or f"Deployment {status.lower()}.")
        time.sleep(2)
    raise click.ClickException(f"Timed out waiting; deployment {deployment_id} may still be running.")
