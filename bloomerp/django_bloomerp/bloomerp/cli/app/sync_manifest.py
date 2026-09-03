import click

from ._utils import resolve_app_dir
from .sync import discover_app_manifest, echo_app_sync, synchronize_local_app


synchronize_app_manifest = synchronize_local_app


@click.command("sync_manifest")
@click.argument("name", required=False)
def sync_manifest(name: str | None) -> None:
    """Deprecated alias for ``bloomerp app sync``."""

    click.echo("Deprecated: use 'bloomerp app sync' instead.", err=True)
    app_dir = resolve_app_dir(name)
    echo_app_sync(app_dir, synchronize_local_app(app_dir))
